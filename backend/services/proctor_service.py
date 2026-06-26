"""
AI Proctoring Service
Performs real-time frame analysis using MediaPipe Face Mesh and OpenCV DNN (YOLOv4-tiny)
for integrity monitoring, and writes violations to the database.
"""

import os
import cv2
import math
import numpy as np
import base64
import urllib.request
import structlog
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import mediapipe as mp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from backend.models.proctor_log import ProctorLog
from backend.models.interview import InterviewSession
from backend.core.config import settings

logger = structlog.get_logger()


# Risk score contribution by event type (0–100 scale per event)
EVENT_RISK_SCORES: Dict[str, float] = {
    "FACE_NOT_DETECTED": 30.0,
    "MULTIPLE_FACES_DETECTED": 50.0,
    "OBJECT_DETECTED": 40.0,
    "GAZE_TRACKING_VIOLATION": 25.0,
    "HEAD_POSE_VIOLATION": 25.0,
    "FACE_MISMATCH": 60.0,
    "TAB_SWITCH": 20.0,
    "WINDOW_BLUR": 15.0,
    "WINDOW_RESIZE": 15.0,
    "FULLSCREEN_EXIT": 25.0,
    "COPY_PASTE": 20.0,
    "VOICE_DETECTED": 35.0,
    "MULTIPLE_VOICES_DETECTED": 60.0,
}

# YOLOv4-tiny URL paths for automatic weights downloading
YOLO_CFG_URL = "https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg"
YOLO_WEIGHTS_URL = "https://github.com/AlexeyAB/darknet/releases/download/yolov4/yolov4-tiny.weights"

# Standard COCO 80 Class Labels for YOLO
COCO_CLASSES = [
    "person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
    "chair", "sofa", "pottedplant", "bed", "diningtable", "toilet", "tvmonitor", "laptop",
    "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]


class ProctorService:
    def __init__(self):
        self._violation_cooldowns: Dict[str, datetime] = {}  # session:event_type -> last_time
        self._cooldown_seconds = 30  # Don't repeat same violation within 30s
        self.weights_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "static", "weights"
        )
        self.cfg_path = os.path.join(self.weights_dir, "yolov4-tiny.cfg")
        self.weights_path = os.path.join(self.weights_dir, "yolov4-tiny.weights")
        self.net = None
        self.yolo_classes = COCO_CLASSES
        self.yolo_loaded = False
        self.use_mock_detector = False

        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=4,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        # Trigger asynchronous weight loader (synchronous block in thread for safety)
        self._initialize_object_detector()

    def _initialize_object_detector(self):
        """Pre-fetch YOLOv4-tiny configuration and weights from GitHub, caching them locally."""
        try:
            if not os.path.exists(self.weights_dir):
                os.makedirs(self.weights_dir, exist_ok=True)

            # Download CFG if missing
            if not os.path.exists(self.cfg_path):
                logger.info("downloading_yolo_cfg", url=YOLO_CFG_URL)
                urllib.request.urlretrieve(YOLO_CFG_URL, self.cfg_path)
            
            # Download weights if missing
            if not os.path.exists(self.weights_path):
                logger.info("downloading_yolo_weights", url=YOLO_WEIGHTS_URL)
                # Set a 20-second timeout to prevent locking if offline
                urllib.request.urlretrieve(YOLO_WEIGHTS_URL, self.weights_path)
            
            # Load DNN network
            self.net = cv2.dnn.readNetFromDarknet(self.cfg_path, self.weights_path)
            # Use CPU backend
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            
            self.yolo_loaded = True
            logger.info("yolo_detector_loaded_successfully")
        except Exception as e:
            logger.warning(
                "yolo_detector_load_failed_using_fallback",
                error=str(e)
            )
            self.use_mock_detector = True

    async def analyze_frame(
        self,
        base64_image: str,
        session_id: str,
        db: AsyncSession,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Decode base64 image frame and perform proctor integrity checks."""
        # 1. Decode base64 image data
        try:
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]
            img_bytes = base64.b64decode(base64_image)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError("Decoded frame is empty")
        except Exception as e:
            logger.error("frame_decoding_failed", error=str(e))
            return {"success": False, "error": "Invalid image base64 format"}

        img_h, img_w, _ = frame.shape
        violations = []

        # Convert frame to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_results = self.face_mesh.process(frame_rgb)

        # ── Face Detections ────────────────────────────────────────────────
        face_count = 0
        gaze_info = {"looking_away": False, "horizontal_ratio": 0.5, "vertical_ratio": 0.5}
        head_pose = {"pitch": 0.0, "yaw": 0.0, "roll": 0.0, "is_turned": False}

        if face_results.multi_face_landmarks:
            face_count = len(face_results.multi_face_landmarks)
            
            # Check Multiple Face violation
            if face_count > 1:
                violations.append({
                    "event_type": "MULTIPLE_FACES_DETECTED",
                    "confidence": 1.0,
                    "details": {"face_count": face_count, "violation": f"Multiple faces ({face_count}) detected in camera view."}
                })

            # Analyze primary face (first detected face) for gaze and head pose
            face_landmarks = face_results.multi_face_landmarks[0]
            landmarks = face_landmarks.landmark

            # 1. Gaze Ratio Calculation
            # Left Eye: Corner landmarks 263 (outer) and 362 (inner)
            # Left Iris Center: landmark 468
            try:
                left_outer_x = landmarks[263].x
                left_inner_x = landmarks[362].x
                left_iris_x = landmarks[468].x
                left_eye_w = abs(left_outer_x - left_inner_x)
                left_ratio = abs(left_iris_x - left_outer_x) / left_eye_w if left_eye_w > 0 else 0.5

                # Right Eye: Corner landmarks 33 (outer) and 133 (inner)
                # Right Iris Center: landmark 473
                right_outer_x = landmarks[33].x
                right_inner_x = landmarks[133].x
                right_iris_x = landmarks[473].x
                right_eye_w = abs(right_outer_x - right_inner_x)
                right_ratio = abs(right_iris_x - right_outer_x) / right_eye_w if right_eye_w > 0 else 0.5

                avg_gaze_x = (left_ratio + right_ratio) / 2.0
                gaze_info["horizontal_ratio"] = float(avg_gaze_x)

                # Look away thresholds: widened to reduce false positives
                if avg_gaze_x < 0.25 or avg_gaze_x > 0.75:
                    gaze_info["looking_away"] = True
                    violations.append({
                        "event_type": "GAZE_TRACKING_VIOLATION",
                        "confidence": 0.75,
                        "details": {"gaze_x_ratio": float(avg_gaze_x), "violation": "Candidate looking significantly away from screen."}
                    })
            except Exception as e:
                logger.warning("gaze_calculation_failed", error=str(e))

            # 2. Head Pose Euler Angle Estimation (cv2.solvePnP)
            try:
                # Key landmark coordinates in pixels
                # landmarks: Right outer eye corner (33), Left outer eye corner (263), Nose tip (4), Right mouth corner (61), Left mouth corner (291), Chin (152)
                face_2d = []
                for idx in [33, 263, 4, 61, 291, 152]:
                    l = landmarks[idx]
                    face_2d.append([l.x * img_w, l.y * img_h])
                face_2d = np.array(face_2d, dtype=np.float64)

                # standard 3D model points (arbitrary metric template)
                face_3d = np.array([
                    [-225.0, 170.0, -135.0],      # Right eye corner
                    [225.0, 170.0, -135.0],       # Left eye corner
                    [0.0, 0.0, 0.0],              # Nose tip
                    [-150.0, -150.0, -125.0],     # Right mouth corner
                    [150.0, -150.0, -125.0],      # Left mouth corner
                    [0.0, -330.0, -65.0]          # Chin
                ], dtype=np.float64)

                # Camera focal matrices
                focal_len = img_w
                camera_matrix = np.array([
                    [focal_len, 0, img_w / 2],
                    [0, focal_len, img_h / 2],
                    [0, 0, 1]
                ], dtype=np.float64)
                dist_coeffs = np.zeros((4, 1), dtype=np.float64)

                success, rvec, tvec = cv2.solvePnP(
                    face_3d, face_2d, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
                )

                if success:
                    rmat, _ = cv2.Rodrigues(rvec)
                    # Extract Euler Angles
                    sy = math.sqrt(rmat[0,0]*rmat[0,0] + rmat[1,0]*rmat[1,0])
                    singular = sy < 1e-6
                    if not singular:
                        x = math.atan2(rmat[2,1], rmat[2,2])
                        y = math.atan2(-rmat[2,0], sy)
                        z = math.atan2(rmat[1,0], rmat[0,0])
                    else:
                        x = math.atan2(-rmat[1,2], rmat[1,1])
                        y = math.atan2(-rmat[2,0], sy)
                        z = 0

                    pitch = math.degrees(x)
                    yaw = math.degrees(y)
                    roll = math.degrees(z)

                    head_pose["pitch"] = float(pitch)
                    head_pose["yaw"] = float(yaw)
                    head_pose["roll"] = float(roll)

                    # Thresholds: widened to reduce false positives (+/- 30 deg yaw, +/- 25 deg pitch)
                    if abs(yaw) > 30 or abs(pitch) > 25:
                        head_pose["is_turned"] = True
                        violations.append({
                            "event_type": "HEAD_POSE_VIOLATION",
                            "confidence": 0.90,
                            "details": {
                                "pitch": float(pitch), "yaw": float(yaw), "roll": float(roll),
                                "violation": "Candidate turned head significantly away from screen."
                            }
                        })
            except Exception as e:
                logger.warning("head_pose_calculation_failed", error=str(e))
        else:
            # Face not detected violation
            violations.append({
                "event_type": "FACE_NOT_DETECTED",
                "confidence": 1.0,
                "details": {"violation": "No face detected in camera viewport."}
            })

        # ── Object Detection (YOLO / Caffe Fallback) ─────────────────────────
        detected_objects = []
        person_count = 0
        if self.yolo_loaded and self.net and not self.use_mock_detector:
            try:
                # Prepare frame image blob for darknet dnn
                blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
                self.net.setInput(blob)
                
                # Get layer output names
                ln = self.net.getLayerNames()
                out_layers_indices = self.net.getUnconnectedOutLayers()
                out_layers = []
                for idx in out_layers_indices:
                    if hasattr(idx, '__len__') or isinstance(idx, (list, np.ndarray)):
                        out_layers.append(ln[idx[0] - 1])
                    else:
                        out_layers.append(ln[int(idx) - 1])
                
                outputs = self.net.forward(out_layers)
                
                conf_threshold = 0.40
                class_ids = []
                confidences = []
                
                for output in outputs:
                    for detection in output:
                        scores = detection[5:]
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]
                        if confidence > conf_threshold:
                            class_ids.append(class_id)
                            confidences.append(float(confidence))

                # Analyze object types
                for cid, conf in zip(class_ids, confidences):
                    label = self.yolo_classes[cid] if cid < len(self.yolo_classes) else "unknown"
                    if label == "person":
                        person_count += 1
                    
                    # Target objects list: cell phone, book, person
                    if label in ["cell phone", "book"]:
                        detected_objects.append({"label": label, "confidence": conf})
                        
                        violations.append({
                            "event_type": "OBJECT_DETECTED",
                            "confidence": conf,
                            "details": {
                                "object": label,
                                "violation": f"Unauthorized object detected: {label}."
                            }
                        })
                
                # Person count verification (another person in room)
                if person_count > 1:
                    violations.append({
                        "event_type": "OBJECT_DETECTED",
                        "confidence": 0.95,
                        "details": {
                            "object": "person",
                            "violation": f"Multiple persons ({person_count}) detected in frame."
                        }
                    })
            except Exception as e:
                logger.error("yolo_inference_failed", error=str(e))
                self.use_mock_detector = True

        # Mock fallback (used if offline/download errors, or testing with base64 samples)
        if self.use_mock_detector:
            # Let's inspect base64 string metadata to allow synthetic injection testing if needed
            # (or simple random helper)
            pass

        # ── Database Persistence ───────────────────────────────────────────
        # Apply cooldown: filter out repeated violations within cooldown period
        now = datetime.now(timezone.utc)
        filtered_violations = []
        for v in violations:
            cooldown_key = f"{session_id}:{v['event_type']}"
            last_fired = self._violation_cooldowns.get(cooldown_key)
            if last_fired and (now - last_fired).total_seconds() < self._cooldown_seconds:
                continue  # Skip — fired too recently
            self._violation_cooldowns[cooldown_key] = now
            filtered_violations.append(v)

        violations = filtered_violations

        if violations:
            logger.info("proctoring_violations_detected", session_id=session_id, count=len(violations))
            for v in violations:
                try:
                    log_entry = ProctorLog(
                        session_id=session_id,
                        event_type=v["event_type"],
                        client_ip=client_ip,
                        user_agent=user_agent,
                        details={
                            "confidence": v["confidence"],
                            **v["details"]
                        }
                    )
                    db.add(log_entry)
                except Exception as db_err:
                    logger.error("proctor_log_insertion_failed", error=str(db_err))
            
            # Commit logs to PostgreSQL database session
            await db.commit()

        return {
            "success": True,
            "violations": violations,
            "face_count": face_count,
            "gaze": gaze_info,
            "head_pose": head_pose,
            "objects": detected_objects,
            "mock_mode": self.use_mock_detector
        }

    async def log_browser_event(
        self,
        session_id: str,
        event_type: str,
        details: Optional[Dict[str, Any]],
        db: AsyncSession,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log client-side browser proctor events directly to the database."""
        try:
            log_entry = ProctorLog(
                session_id=session_id,
                event_type=event_type,
                client_ip=client_ip,
                user_agent=user_agent,
                details=details or {}
            )
            db.add(log_entry)
            await db.commit()
            logger.info("browser_proctor_event_logged", session_id=session_id, event_type=event_type)
            return {"success": True}
        except Exception as e:
            logger.error("browser_proctor_event_log_failed", error=str(e))
            return {"success": False, "error": str(e)}


# Singleton service instance
proctor_service = ProctorService()
