"""
AI Interview Assistant - Streamlit Frontend

A clean, interactive UI that communicates with the FastAPI backend.

Workflow:
1. Upload Resume → Backend processes PDF → Creates FAISS vector store
2. Generate Questions → LangChain retrieves resume context → Creates 8 questions
3. Start Interview → Chat interface → One question at a time
4. Real-time Feedback → Score (0-10) + strengths + improvements
5. Final Summary → Overall score + recommendation
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import time
from typing import Optional

# ============================================
# Configuration
# ============================================
BACKEND_URL = "http://localhost:8000/api/v1"

# ============================================
# Page Configuration
# ============================================
st.set_page_config(
    page_title="AI Interview Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# Custom CSS Styling (Premium Dark Design)
# ============================================
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Reset */
    * { font-family: 'Inter', sans-serif; }
    
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1117 50%, #0a1628 100%);
        min-height: 100vh;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b27 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    /* Header Banner */
    .hero-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
        animation: glow 3s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3); }
        to { box-shadow: 0 20px 80px rgba(240, 147, 251, 0.4); }
    }
    
    .hero-banner h1 {
        color: white;
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 20px rgba(0,0,0,0.3);
    }
    
    .hero-banner p {
        color: rgba(255,255,255,0.85);
        font-size: 1.05rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* Step Cards */
    .step-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.8rem 0;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .step-card:hover {
        border-color: rgba(99, 102, 241, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.15);
    }
    
    .step-card.active {
        border-color: rgba(99, 102, 241, 0.7);
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(118, 75, 162, 0.05) 100%);
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.2);
    }
    
    .step-card.completed {
        border-color: rgba(16, 185, 129, 0.5);
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(16, 185, 129, 0.02) 100%);
    }
    
    /* Chat Messages */
    .chat-message {
        padding: 1rem 1.2rem;
        border-radius: 12px;
        margin: 0.6rem 0;
        line-height: 1.7;
        animation: fadeIn 0.4s ease;
        font-size: 0.95rem;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .chat-ai {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(118, 75, 162, 0.08) 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-left: 4px solid #667eea;
        color: #e2e8f0;
    }
    
    .chat-user {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(16, 185, 129, 0.05) 100%);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-right: 4px solid #10b981;
        color: #e2e8f0;
        text-align: right;
    }
    
    /* Feedback Cards */
    .feedback-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        animation: fadeIn 0.5s ease;
    }
    
    /* Score Display */
    .score-display {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #667eea, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
    }
    
    .score-label {
        text-align: center;
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.3rem;
    }
    
    /* Question Badge */
    .question-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 0.5rem;
    }
    
    .badge-technical {
        background: rgba(99, 102, 241, 0.2);
        border: 1px solid rgba(99, 102, 241, 0.4);
        color: #818cf8;
    }
    
    .badge-hr {
        background: rgba(245, 158, 11, 0.2);
        border: 1px solid rgba(245, 158, 11, 0.4);
        color: #fbbf24;
    }
    
    /* Skill Tags */
    .skill-tag {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 20px;
        color: #818cf8;
        font-size: 0.78rem;
        font-weight: 500;
        margin: 0.2rem;
    }
    
    /* Progress Bar */
    .progress-track {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        height: 8px;
        margin: 0.5rem 0;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #667eea, #f093fb);
        transition: width 0.5s ease;
    }
    
    /* Summary Cards */
    .summary-header {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(118, 75, 162, 0.05) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    /* Button Styling Override */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Text Input */
    .stTextArea textarea {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-size: 0.95rem !important;
    }
    
    .stTextArea textarea:focus {
        border-color: rgba(99, 102, 241, 0.7) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }
    
    /* Hide text area instructions (Press Ctrl+Enter to apply) */
    .stTextArea div[data-testid="InputInstructions"] { display: none !important; }
    .stTextArea small { display: none !important; }
    
    /* Info/Success/Warning boxes */
    .stSuccess { border-radius: 10px !important; }
    .stInfo { border-radius: 10px !important; }
    .stWarning { border-radius: 10px !important; }
    .stError { border-radius: 10px !important; }
    
    /* Divider */
    hr { border-color: rgba(255,255,255,0.1) !important; }
    
    /* Metric styling */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(99, 102, 241, 0.08) !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
</style>
""", unsafe_allow_html=True)


# ============================================
# Session State Initialization
# ============================================
def init_session_state():
    """Initialize all Streamlit session state variables"""
    defaults = {
        "session_id": None,
        "candidate_name": "",
        "skills_detected": [],
        "experience_years": "",
        "questions": [],
        "interview_started": False,
        "interview_complete": False,
        "chat_history": [],       # List of {"role": "ai"/"user", "content": "..."}
        "current_question_num": 0,
        "total_questions": 0,
        "last_feedback": None,
        "final_summary": None,
        "step": 1,                # Current step: 1=Upload, 2=Questions, 3=Interview, 4=Coding, 5=Summary
        "challenges_list": [],
        "coding_submission_verified": False,
        "analytics_selected_session_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================
# API Helper Functions
# ============================================
def _parse_api_response(response: requests.Response) -> dict:
    """
    Parse a FastAPI response into a consistent dict.

    FastAPI success responses already have {"success": true, ...}.
    FastAPI error responses look like {"detail": "some message"}.
    This helper normalises both into {"success": bool, "message": str, ...}.
    """
    try:
        data = response.json()
    except Exception:
        return {"success": False, "message": f"Non-JSON response (HTTP {response.status_code}): {response.text[:300]}"}

    if response.ok:
        # Successful response — pass through as-is
        return data

    # Error response — FastAPI wraps the detail in {"detail": "..."}
    detail = data.get("detail", "")
    if isinstance(detail, list):
        # Pydantic validation errors come as a list of dicts
        detail = "; ".join(str(e.get("msg", e)) for e in detail)
    return {"success": False, "message": str(detail) or f"HTTP {response.status_code} error"}


def api_upload_resume(file_bytes: bytes, filename: str) -> dict:
    """Call backend API to upload and process resume"""
    try:
        files = {"file": (filename, file_bytes, "application/pdf")}
        response = requests.post(
            f"{BACKEND_URL}/resume/upload",
            files=files,
            timeout=60,
        )
        return _parse_api_response(response)
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend. Make sure the FastAPI server is running on port 8000."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def api_generate_questions(session_id: str) -> dict:
    """Call backend API to generate interview questions"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/interview/generate-questions/{session_id}",
            timeout=60,
        )
        return _parse_api_response(response)
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def api_start_interview(session_id: str) -> dict:
    """Call backend API to start the interview"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/interview/start/{session_id}",
            timeout=30,
        )
        return _parse_api_response(response)
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def api_chat(session_id: str, message: str) -> dict:
    """Call backend API to send answer and get feedback"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/interview/chat",
            json={"session_id": session_id, "message": message},
            timeout=60,
        )
        return _parse_api_response(response)
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def api_get_summary(session_id: str) -> dict:
    """Call backend API to get final interview summary"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/interview/summary/{session_id}",
            timeout=60,
        )
        return _parse_api_response(response)
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def api_get_challenges() -> dict:
    """Call backend API to get coding challenges"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/coding/challenges",
            timeout=20,
        )
        if response.ok:
            return {"success": True, "challenges": response.json()}
        return {"success": False, "message": "Failed to fetch challenges"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def api_get_coding_submissions(session_id: str) -> dict:
    """Call backend to retrieve all submissions for an interview session"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/coding/submissions/{session_id}",
            timeout=20,
        )
        if response.ok:
            return {"success": True, "submissions": response.json()}
        return {"success": False, "message": "Failed to fetch submissions"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def api_get_analytics_overview() -> dict:
    """Call backend API to get analytics overview"""
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/overview", timeout=20)
        return _parse_api_response(response)
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def api_get_analytics_history() -> dict:
    """Call backend API to get analytics history"""
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/history", timeout=20)
        return _parse_api_response(response)
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def api_get_analytics_skills() -> dict:
    """Call backend API to get analytics skills distribution"""
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/skills", timeout=20)
        return _parse_api_response(response)
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def api_get_analytics_strengths_weaknesses() -> dict:
    """Call backend API to get candidate strengths/weaknesses aggregates"""
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/strengths-weaknesses", timeout=20)
        return _parse_api_response(response)
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def api_get_analytics_proctor_violations() -> dict:
    """Call backend API to get proctoring violation analytics"""
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/proctor-violations", timeout=20)
        return _parse_api_response(response)
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def api_get_analytics_performance_trend() -> dict:
    """Call backend API to get candidate average score trends over time"""
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/performance-trend", timeout=20)
        return _parse_api_response(response)
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "❌ Cannot connect to backend."}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ============================================
# UI Component Functions
# ============================================
PROCTOR_MONITOR_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background: transparent;
            color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        .proctor-card {
            background: linear-gradient(135deg, rgba(30,41,59,0.7) 0%, rgba(15,23,42,0.85) 100%);
            border: 1px solid rgba(99,102,241,0.3);
            border-radius: 12px;
            padding: 10px;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 7px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        .video-container {
            position: relative;
            width: 100%;
            max-width: 155px;
            height: 100px;
            border-radius: 8px;
            overflow: hidden;
            border: 2px solid rgba(99,102,241,0.4);
            background: #020617;
            transition: border-color 0.3s ease;
        }
        .video-container.violation {
            border-color: #ef4444;
            animation: vid-pulse 1s infinite alternate;
        }
        @keyframes vid-pulse {
            from { box-shadow: 0 0 4px rgba(239,68,68,0.3); }
            to   { box-shadow: 0 0 14px rgba(239,68,68,0.7); }
        }
        #webcam {
            width: 100%; height: 100%;
            object-fit: cover;
            transform: scaleX(-1);
        }
        .badge-row {
            width: 100%;
            display: flex;
            gap: 5px;
            align-items: center;
        }
        .status-badge {
            flex: 1;
            font-size: 0.65rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            text-align: center;
            transition: all 0.3s ease;
        }
        .violation-count {
            font-size: 0.6rem;
            font-weight: 800;
            padding: 3px 7px;
            border-radius: 20px;
            background: rgba(239,68,68,0.15);
            border: 1px solid rgba(239,68,68,0.4);
            color: #f87171;
            min-width: 28px;
            text-align: center;
            display: none;
        }
        .violation-count.visible { display: block; }
        .status-compliant {
            background: rgba(16,185,129,0.15);
            border: 1px solid rgba(16,185,129,0.4);
            color: #34d399;
        }
        .status-violation {
            background: rgba(239,68,68,0.18);
            border: 1px solid rgba(239,68,68,0.6);
            color: #f87171;
            animation: pulse-border 1.2s infinite alternate;
        }
        .status-warning {
            background: rgba(245,158,11,0.15);
            border: 1px solid rgba(245,158,11,0.4);
            color: #fbbf24;
        }
        .status-init {
            background: rgba(99,102,241,0.1);
            border: 1px solid rgba(99,102,241,0.3);
            color: #a5b4fc;
        }
        @keyframes pulse-border {
            from { box-shadow: 0 0 4px rgba(239,68,68,0.3); }
            to   { box-shadow: 0 0 14px rgba(239,68,68,0.7); }
        }
        .log-box {
            width: 100%;
            height: 80px;
            overflow-y: auto;
            font-size: 0.6rem;
            color: #94a3b8;
            background: rgba(15,23,42,0.65);
            padding: 5px 6px;
            border-radius: 7px;
            border: 1px solid rgba(255,255,255,0.04);
            text-align: left;
            scroll-behavior: smooth;
        }
        .log-item {
            display: flex;
            gap: 5px;
            margin-bottom: 3px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            padding-bottom: 2px;
            line-height: 1.4;
        }
        .log-time { color: #475569; flex-shrink: 0; }
        .log-msg  { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .log-item.alert .log-msg { color: #f87171; font-weight: 700; }
        .log-item.warn  .log-msg { color: #fbbf24; }
        .log-item.ok    .log-msg { color: #34d399; }
        .log-box::-webkit-scrollbar { width: 3px; }
        .log-box::-webkit-scrollbar-track { background: transparent; }
        .log-box::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.3); border-radius: 2px; }
    </style>
</head>
<body>
    <div class="proctor-card">
        <div class="video-container" id="videoContainer">
            <video id="webcam" autoplay playsinline muted></video>
            <canvas id="snapshotCanvas" style="display:none;" width="320" height="240"></canvas>
        </div>
        
        <div class="badge-row">
            <div id="proctorStatus" class="status-badge status-init">⏳ STARTING</div>
            <div id="violationCount" class="violation-count">0</div>
        </div>
        
        <div class="log-box" id="logBox">
            <div class="log-item"><span class="log-time">--:--</span><span class="log-msg">Initializing AI proctoring...</span></div>
        </div>
    </div>

    <script>
        const session_id  = "{session_id}";
        const backend_url = "{backend_url}";
        const video       = document.getElementById('webcam');
        const canvas      = document.getElementById('snapshotCanvas');
        const ctx         = canvas.getContext('2d');
        const statusBadge = document.getElementById('proctorStatus');
        const logBox      = document.getElementById('logBox');
        const vidContainer= document.getElementById('videoContainer');
        const vcBadge     = document.getElementById('violationCount');

        let frameCount   = 0;
        let violCount    = 0;
        let analyzeTimer = null;

        // ── Human-readable violation labels ────────────────────────────────
        const VIOLATION_LABELS = {
            FACE_NOT_DETECTED:         { emoji: '👤', text: 'No face detected in camera', level: 'alert' },
            MULTIPLE_FACES_DETECTED:   { emoji: '👥', text: 'Multiple faces in camera',   level: 'alert' },
            GAZE_TRACKING_VIOLATION:   { emoji: '👀', text: 'Looking away from screen',    level: 'alert' },
            HEAD_POSE_VIOLATION:       { emoji: '🔄', text: 'Head turned away from screen',level: 'alert' },
            OBJECT_DETECTED:           { emoji: '📱', text: 'Unauthorized object detected', level: 'alert' },
            TAB_SWITCH:                { emoji: '🪟', text: 'Tab switch / window minimized',level: 'alert' },
            FOCUS_LOSS:                { emoji: '🖱️', text: 'Focus lost — clicked outside', level: 'warn'  },
            COPY_PASTE:                { emoji: '📋', text: 'Copy/paste action detected',   level: 'warn'  },
        };

        function ts() {
            const d = new Date();
            return d.toTimeString().slice(0,5);
        }

        function addLog(msg, level = 'info', extra = '') {
            const row = document.createElement('div');
            row.className = 'log-item' + (level !== 'info' ? ' ' + level : '');
            row.innerHTML = `<span class="log-time">${ts()}</span><span class="log-msg">${msg}${extra ? ' — ' + extra : ''}</span>`;
            logBox.appendChild(row);
            // Keep max 40 entries
            while (logBox.children.length > 40) logBox.removeChild(logBox.firstChild);
            logBox.scrollTop = logBox.scrollHeight;
        }

        function setStatus(text, cssClass) {
            statusBadge.className = 'status-badge ' + cssClass;
            statusBadge.innerText = text;
        }

        function updateViolCount(n) {
            violCount += n;
            if (violCount > 0) {
                vcBadge.classList.add('visible');
                vcBadge.innerText = violCount + ' ⚠';
            }
        }

        async function startCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } });
                video.srcObject = stream;
                setStatus('🔒 COMPLIANT', 'status-compliant');
                vidContainer.classList.remove('violation');
                addLog('Camera connected — proctoring active', 'ok');
                // Start periodic analysis
                analyzeTimer = setInterval(captureAndAnalyze, 4000);
            } catch (err) {
                setStatus('📷 NO CAMERA', 'status-violation');
                addLog('Camera blocked — please grant access', 'alert');
                console.error('Camera access error:', err);
            }
        }

        async function captureAndAnalyze() {
            if (!video.srcObject || video.readyState < 2) return;
            frameCount++;

            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.55);

            try {
                const response = await fetch(backend_url + '/proctor/analyze-frame', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: session_id, image_data: dataUrl })
                });

                if (!response.ok) {
                    addLog('Analysis error — HTTP ' + response.status, 'warn');
                    return;
                }

                const data = await response.json();
                handleProctorResult(data);

                // Show a quiet info tick every 5 frames so user sees system is working
                if (frameCount % 5 === 0) {
                    addLog('Frame #' + frameCount + ' analyzed — ' + (data.violations && data.violations.length ? data.violations.length + ' issue(s)' : 'all clear'));
                }
            } catch (err) {
                addLog('Cannot reach proctoring server', 'warn');
                console.error('Proctor fetch error:', err);
            }
        }

        function handleProctorResult(data) {
            if (!data || !data.success) return;

            const violations = data.violations || [];

            if (violations.length > 0) {
                vidContainer.classList.add('violation');
                updateViolCount(violations.length);

                // Show the most severe violation in status badge
                const first = violations[0];
                const label = VIOLATION_LABELS[first.event_type] || { emoji: '⚠️', text: first.event_type.replace(/_/g, ' '), level: 'alert' };
                setStatus(label.emoji + ' ' + label.text.toUpperCase().slice(0,22), 'status-violation');

                // Log each violation with its human label
                violations.forEach(v => {
                    const info = VIOLATION_LABELS[v.event_type] || { emoji: '⚠️', text: v.event_type.replace(/_/g, ' '), level: 'alert' };
                    const detail = v.details && v.details.violation ? v.details.violation : '';
                    addLog(info.emoji + ' ' + info.text, info.level, detail);
                });
            } else {
                // Clear violation styling
                vidContainer.classList.remove('violation');
                setStatus('🔒 COMPLIANT', 'status-compliant');
            }
        }

        function logBrowserEvent(eventType, details = {}) {
            const label = VIOLATION_LABELS[eventType] || { emoji: '⚠️', text: eventType.replace(/_/g, ' '), level: 'warn' };
            setStatus(label.emoji + ' ' + label.text.toUpperCase().slice(0,22), 'status-violation');
            vidContainer.classList.add('violation');
            updateViolCount(1);
            addLog(label.emoji + ' ' + label.text, label.level, details.violation || '');

            fetch(backend_url + '/proctor/log-event', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: session_id, event_type: eventType, details: details })
            }).catch(err => console.error('Failed to log browser event:', err));

            // Auto-reset to compliant after 6 seconds if no new violations
            setTimeout(() => {
                if (!document.getElementById('proctorStatus').innerText.includes('COMPLIANT')) {
                    setStatus('🔒 COMPLIANT', 'status-compliant');
                    vidContainer.classList.remove('violation');
                }
            }, 6000);
        }

        function setupBrowserMonitoring() {
            function bindEvents(targetWin, targetDoc, contextName, options = {}) {
                targetDoc.addEventListener('visibilitychange', () => {
                    if (targetDoc.visibilityState === 'hidden') {
                        logBrowserEvent('TAB_SWITCH', { context: contextName, violation: 'Browser tab switched or window minimized.' });
                    }
                });
                if (!options.skipBlur) {
                    targetWin.addEventListener('blur', () => {
                        logBrowserEvent('FOCUS_LOSS', { context: contextName, violation: 'Candidate clicked outside the browser window.' });
                    });
                }
                targetDoc.addEventListener('copy', () => logBrowserEvent('COPY_PASTE', { context: contextName, action: 'copy', violation: 'Text copy action detected.' }));
                targetDoc.addEventListener('paste', () => logBrowserEvent('COPY_PASTE', { context: contextName, action: 'paste', violation: 'Text paste action detected.' }));
            }
            try {
                if (window.parent && window.parent !== window) {
                    bindEvents(window.parent, window.parent.document, 'parent', { skipBlur: false });
                    bindEvents(window, document, 'iframe', { skipBlur: true });
                } else {
                    bindEvents(window, document, 'self', { skipBlur: false });
                }
            } catch (err) {
                console.warn('Browser monitoring: using local fallback', err);
                bindEvents(window, document, 'self', { skipBlur: false });
            }
        }

        window.addEventListener('load', () => {
            startCamera();
            setupBrowserMonitoring();
        });
    </script>
</body>
</html>

"""




def render_hero():
    """Render the top hero banner"""
    st.markdown("""
    <div class="hero-banner">
        <h1>🎯 AI Interview Assistant</h1>
        <p>Agentic AI-powered mock interviews with real-time feedback & scoring</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_steps():
    """Render workflow steps in sidebar"""
    mode = st.sidebar.selectbox(
        "📂 Navigation Mode",
        ["Mock Interview", "Analytics Dashboard"],
        key="navigation_mode"
    )
    
    if mode == "Analytics Dashboard":
        st.sidebar.markdown("## 📊 Analytics Mode")
        st.sidebar.info(
            "Viewing aggregated recruitment reports, "
            "proctoring alerts, and candidate evaluation details."
        )
        return mode
        
    st.sidebar.markdown("## 📋 Interview Workflow")
    
    step = st.session_state.step
    
    steps = [
        (1, "📄", "Upload Resume"),
        (2, "🧠", "Generate Questions"),
        (3, "💬", "Mock Interview"),
        (4, "💻", "Coding Assessment"),
        (5, "🏆", "Final Summary"),
    ]
    
    for num, icon, label in steps:
        if num < step:
            status = "completed"
            prefix = "✅"
        elif num == step:
            status = "active"
            prefix = "▶️"
        else:
            status = ""
            prefix = "○"
        
        st.sidebar.markdown(f"""
        <div class="step-card {status}">
            {prefix} <strong>{icon} Step {num}: {label}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    st.sidebar.divider()
    
    # Session info
    if st.session_state.session_id:
        st.sidebar.markdown("### 👤 Candidate Info")
        st.sidebar.markdown(f"**Name:** {st.session_state.candidate_name}")
        if st.session_state.experience_years:
            st.sidebar.markdown(f"**Experience:** {st.session_state.experience_years}")
        
        if st.session_state.skills_detected:
            st.sidebar.markdown("**Skills Detected:**")
            skills_html = "".join(
                f'<span class="skill-tag">{s}</span>'
                for s in st.session_state.skills_detected[:10]
            )
            st.sidebar.markdown(skills_html, unsafe_allow_html=True)
        
        st.sidebar.divider()
    
    # Progress during interview
    if st.session_state.interview_started and not st.session_state.interview_complete:
        total = st.session_state.total_questions
        current = st.session_state.current_question_num
        if total > 0:
            progress_pct = min(100, int((current / total) * 100))
            st.sidebar.markdown(f"### 📊 Progress: {current}/{total}")
            st.sidebar.markdown(f"""
            <div class="progress-track">
                <div class="progress-fill" style="width: {progress_pct}%"></div>
            </div>
            """, unsafe_allow_html=True)
    
    # Reset button
    if st.session_state.session_id:
        st.sidebar.divider()
        if st.sidebar.button("🔄 Start New Session", use_container_width=True):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Proctoring monitor during active interview steps (Step 3 & 4)
    if step in [3, 4] and st.session_state.session_id:
        st.sidebar.divider()
        st.sidebar.markdown("<div style='text-align: center; font-weight: bold; color: #a5b4fc; margin-bottom: 8px;'>🛡️ Live AI Proctoring</div>", unsafe_allow_html=True)
        proctor_html = PROCTOR_MONITOR_HTML.replace(
            "{session_id}", st.session_state.session_id
        ).replace(
            "{backend_url}", BACKEND_URL
        )
        with st.sidebar:
            components.html(proctor_html, height=265)


def render_step1_upload():
    """Step 1: Resume Upload"""
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("## 📄 Step 1: Upload Your Resume")
        st.markdown("""
        Upload your PDF resume and our AI will:
        - 📝 **Extract** all text content
        - 🔍 **Analyze** your skills and experience  
        - 🧠 **Create embeddings** stored in FAISS vector database
        - 💡 **Generate** personalized interview questions
        """)
        
        uploaded_file = st.file_uploader(
            "Choose your resume (PDF only)",
            type=["pdf"],
            help="Upload a PDF resume. Max size: 10MB",
            key="resume_uploader",
        )
        
        if uploaded_file:
            st.success(f"✅ File loaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
            
            if st.button("🚀 Process Resume", use_container_width=True, key="btn_process"):
                with st.spinner("🔄 Processing your resume... (extracting text & creating embeddings)"):
                    file_bytes = uploaded_file.read()
                    result = api_upload_resume(file_bytes, uploaded_file.name)
                
                if result.get("success"):
                    st.session_state.session_id = result["session_id"]
                    st.session_state.candidate_name = result.get("candidate_name", "Candidate")
                    st.session_state.skills_detected = result.get("skills_detected", [])
                    st.session_state.experience_years = result.get("experience_years", "")
                    st.session_state.step = 2
                    
                    st.success(f"🎉 {result['message']}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('message', 'Failed to process resume.')}")
    
    with col2:
        # How it works diagram
        st.markdown("### ⚙️ How It Works")
        st.markdown("""
        <div class="step-card">
            <strong>🔹 PDF Parsing</strong><br>
            <small style="color: #94a3b8;">PyPDF extracts all text content from your resume</small>
        </div>
        <div class="step-card">
            <strong>🔹 Text Chunking</strong><br>
            <small style="color: #94a3b8;">Text is split into overlapping 500-char chunks</small>
        </div>
        <div class="step-card">
            <strong>🔹 OpenAI Embeddings</strong><br>
            <small style="color: #94a3b8;">Each chunk is converted to a 1536-dim vector</small>
        </div>
        <div class="step-card">
            <strong>🔹 FAISS Storage</strong><br>
            <small style="color: #94a3b8;">Vectors stored for fast similarity search</small>
        </div>
        """, unsafe_allow_html=True)


def render_step2_questions():
    """Step 2: Generate Questions"""
    st.markdown(f"## 🧠 Step 2: Generate Interview Questions")
    st.markdown(f"Welcome, **{st.session_state.candidate_name}**! Ready to generate your personalized questions.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Skills display
        if st.session_state.skills_detected:
            st.markdown("### 🎯 Skills Detected in Your Resume")
            skills_html = "".join(
                f'<span class="skill-tag">{skill}</span>'
                for skill in st.session_state.skills_detected
            )
            st.markdown(skills_html, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not st.session_state.questions:
            st.info("Click below to generate 5 technical + 3 HR questions **tailored to your resume**.")
            
            if st.button("✨ Generate Interview Questions", use_container_width=True, key="btn_generate"):
                with st.spinner("🧠 AI is analyzing your resume and generating questions... (this may take 20-30 seconds)"):
                    result = api_generate_questions(st.session_state.session_id)
                
                if result.get("success"):
                    st.session_state.questions = result.get("questions", [])
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('message', 'Failed to generate questions.')}")
        
        else:
            # Show confirmation card — questions are HIDDEN intentionally (no spoilers!)
            total_q = len(st.session_state.questions)
            technical_count = sum(1 for q in st.session_state.questions if q.get("type") == "technical")
            hr_count = sum(1 for q in st.session_state.questions if q.get("type") == "hr")
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(16,185,129,0.12) 0%, rgba(99,102,241,0.08) 100%);
                border: 1px solid rgba(16,185,129,0.4);
                border-left: 5px solid #10b981;
                border-radius: 14px;
                padding: 2rem 2.2rem;
                margin: 1rem 0 1.5rem 0;
                text-align: center;
                animation: fadeIn 0.5s ease;
            ">
                <div style="font-size: 2.8rem; margin-bottom: 0.6rem;">🎯</div>
                <div style="color: #34d399; font-size: 1.35rem; font-weight: 700; margin-bottom: 0.5rem;">
                    Questions are generated!
                </div>
                <div style="color: #94a3b8; font-size: 0.95rem; font-style: italic; margin-bottom: 1.2rem; line-height: 1.6;">
                    &ldquo;The secret of getting ahead is getting started.&rdquo;<br>
                    <span style="font-size: 0.8rem; opacity: 0.7;">&mdash; Mark Twain</span>
                </div>
                <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap;">
                    <div style="
                        background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.35);
                        border-radius: 10px; padding: 0.6rem 1.2rem; text-align: center;
                    ">
                        <div style="color: #818cf8; font-size: 1.6rem; font-weight: 800;">{technical_count}</div>
                        <div style="color: #94a3b8; font-size: 0.78rem;">Technical</div>
                    </div>
                    <div style="
                        background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.35);
                        border-radius: 10px; padding: 0.6rem 1.2rem; text-align: center;
                    ">
                        <div style="color: #fbbf24; font-size: 1.6rem; font-weight: 800;">{hr_count}</div>
                        <div style="color: #94a3b8; font-size: 0.78rem;">HR / Behavioral</div>
                    </div>
                    <div style="
                        background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.35);
                        border-radius: 10px; padding: 0.6rem 1.2rem; text-align: center;
                    ">
                        <div style="color: #34d399; font-size: 1.6rem; font-weight: 800;">{total_q}</div>
                        <div style="color: #94a3b8; font-size: 0.78rem;">Total</div>
                    </div>
                </div>
                <div style="color: #64748b; font-size: 0.82rem; margin-top: 1.2rem;">
                    🔒 Questions are confidential &mdash; they will appear one by one during the interview.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("▶️ Start Mock Interview", use_container_width=True, key="btn_start_interview"):
                st.session_state.step = 3
                st.rerun()
    
    with col2:
        st.markdown("### 📊 Question Breakdown")
        st.markdown("""
        <div class="step-card active">
            <div style="color: #818cf8; font-size: 2rem; font-weight: 800;">5</div>
            <div style="color: #94a3b8; font-size: 0.85rem;">Technical Questions</div>
        </div>
        <div class="step-card">
            <div style="color: #fbbf24; font-size: 2rem; font-weight: 800;">3</div>
            <div style="color: #94a3b8; font-size: 0.85rem;">HR / Behavioral Questions</div>
        </div>
        <div class="step-card completed">
            <div style="color: #10b981; font-size: 2rem; font-weight: 800;">8</div>
            <div style="color: #94a3b8; font-size: 0.85rem;">Total Questions</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🤖 AI Process")
        st.markdown("""
        <div class="step-card">
            <small style="color: #94a3b8;">
            1. Retrieves top 5 most relevant resume chunks from FAISS<br><br>
            2. Sends context to GPT-4o-mini with a structured prompt<br><br>
            3. Parses response into typed question objects
            </small>
        </div>
        """, unsafe_allow_html=True)


MONACO_EDITOR_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Monaco IDE</title>
    <!-- Load marked for markdown rendering -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #090d16;
            color: #f8fafc;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .app-container {
            display: flex;
            flex: 1;
            height: 100vh;
            overflow: hidden;
        }
        .left-pane {
            width: 40%;
            background: #0f172a;
            border-right: 2px solid #1e293b;
            padding: 20px;
            overflow-y: auto;
            box-sizing: border-box;
        }
        .right-pane {
            width: 60%;
            display: flex;
            flex-direction: column;
            background: #0b0f19;
            box-sizing: border-box;
            height: 100%;
        }
        .editor-header {
            background: #0f172a;
            border-bottom: 1px solid #1e293b;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .select-lang {
            background: #1e293b;
            border: 1px solid #334155;
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.9rem;
            outline: none;
            cursor: pointer;
        }
        .btn {
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            margin-left: 8px;
            transition: all 0.2s ease;
            font-size: 0.85rem;
        }
        .btn-run {
            background: #334155;
            color: #f1f5f9;
        }
        .btn-run:hover { background: #475569; }
        .btn-submit {
            background: linear-gradient(135deg, #6366f1, #4f46e5);
            color: white;
        }
        .btn-submit:hover {
            box-shadow: 0 0 12px rgba(99,102,241,0.4);
            transform: translateY(-1px);
        }
        #editor {
            flex: 1;
            width: 100%;
            background: #1e1e1e;
        }
        .terminal-pane {
            height: 220px;
            background: #020617;
            border-top: 2px solid #1e293b;
            display: flex;
            flex-direction: column;
        }
        .terminal-header {
            background: #0b1329;
            padding: 8px 20px;
            font-size: 0.75rem;
            font-weight: 700;
            color: #94a3b8;
            border-bottom: 1px solid #1e293b;
            display: flex;
            justify-content: space-between;
        }
        .terminal-output {
            flex: 1;
            padding: 15px 20px;
            overflow-y: auto;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.85rem;
            line-height: 1.5;
            color: #38bdf8;
            white-space: pre-wrap;
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 700;
            margin-right: 5px;
        }
        .badge-easy { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }
        .badge-medium { background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }
        .badge-hard { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }
    </style>
    <!-- Load Monaco Editor via AMD loader -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.6/require.min.js"></script>
</head>
<body>
    <div class="app-container">
        <div class="left-pane">
            <h2 id="probTitle" style="margin-top:0; color:#f1f5f9;">Loading...</h2>
            <div style="margin-bottom: 15px;">
                <span id="diffBadge" class="badge"></span>
                <span id="timeLimit" style="color: #94a3b8; font-size: 0.8rem; margin-left: 10px;">Time Limit: 2.0s</span>
                <span id="memoryLimit" style="color: #94a3b8; font-size: 0.8rem; margin-left: 10px;">Memory Limit: 128MB</span>
            </div>
            <hr style="border-color:#1e293b; margin: 15px 0;">
            <div id="probDesc" style="line-height:1.6; color:#cbd5e1;"></div>
        </div>
        <div class="right-pane">
            <div class="editor-header">
                <div>
                    <select id="langSelect" class="select-lang" onchange="changeLanguage()"></select>
                </div>
                <div>
                    <button class="btn btn-run" onclick="runCode()">Run Code</button>
                    <button class="btn btn-submit" onclick="submitCode()">Submit Solution</button>
                </div>
            </div>
            <div id="editor"></div>
            <div class="terminal-pane">
                <div class="terminal-header">
                    <span>CONSOLE OUTPUT</span>
                    <span id="sandboxInfo" style="color:#64748b;">Ready</span>
                </div>
                <div id="terminal-output" class="terminal-output">Ready to execute tests. Click "Run Code" to run sample test cases.</div>
            </div>
        </div>
    </div>

    <script>
        const challengeId = "{challenge_id}";
        const sessionId = "{session_id}";
        const backendUrl = "{backend_url}";
        const templates = {default_templates};
        const challengeTitle = {challenge_title};
        const challengeDesc = {challenge_description};
        const challengeDiff = {challenge_difficulty};
        
        let editor;
        let selectedLang = "";

        // Set challenge description
        document.getElementById("probTitle").innerText = challengeTitle;
        document.getElementById("probDesc").innerHTML = marked.parse(challengeDesc);
        
        const badge = document.getElementById("diffBadge");
        badge.innerText = challengeDiff.toUpperCase();
        badge.className = "badge badge-" + challengeDiff.toLowerCase();

        // Initialize Monaco
        require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.39.0/min/vs' }});
        require(['vs/editor/editor.main'], function() {
            // Load languages based on templates
            const langSelect = document.getElementById("langSelect");
            const languages = Object.keys(templates);
            
            languages.forEach(l => {
                const opt = document.createElement("option");
                opt.value = l;
                opt.innerText = l.toUpperCase();
                langSelect.appendChild(opt);
            });

            selectedLang = languages[0];
            
            // Map common names to Monaco languages
            const monacoLangs = {
                "python": "python",
                "javascript": "javascript",
                "cpp": "cpp",
                "java": "java",
                "sql": "sql"
            };

            editor = monaco.editor.create(document.getElementById('editor'), {
                value: templates[selectedLang] || "",
                language: monacoLangs[selectedLang] || "python",
                theme: 'vs-dark',
                automaticLayout: true,
                fontSize: 14,
                minimap: { enabled: false }
            });
        });

        function changeLanguage() {
            selectedLang = document.getElementById("langSelect").value;
            const monacoLangs = {
                "python": "python",
                "javascript": "javascript",
                "cpp": "cpp",
                "java": "java",
                "sql": "sql"
            };
            
            // Update model
            const model = editor.getModel();
            monaco.editor.setModelLanguage(model, monacoLangs[selectedLang] || "python");
            editor.setValue(templates[selectedLang] || "");
        }

        async function runCode() {
            const code = editor.getValue();
            const term = document.getElementById("terminal-output");
            term.innerHTML = "Running sample test cases...";
            term.style.color = "#94a3b8";

            try {
                const response = await fetch(`${backendUrl}/coding/run`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        challenge_id: challengeId,
                        language: selectedLang,
                        code: code
                    })
                });
                
                const data = await response.json();
                renderResults(data, false);
            } catch (err) {
                term.innerText = `Error connecting to execution server: ${err.message}`;
                term.style.color = "#ef4444";
            }
        }

        async function submitCode() {
            const code = editor.getValue();
            const term = document.getElementById("terminal-output");
            term.innerHTML = "Submitting code and running full test suite...";
            term.style.color = "#94a3b8";

            try {
                const response = await fetch(`${backendUrl}/coding/submit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        challenge_id: challengeId,
                        language: selectedLang,
                        code: code
                    })
                });
                
                const data = await response.json();
                renderResults(data.results, true);
            } catch (err) {
                term.innerText = `Error connecting to execution server: ${err.message}`;
                term.style.color = "#ef4444";
            }
        }

        function renderResults(res, isSubmit) {
            const term = document.getElementById("terminal-output");
            const info = document.getElementById("sandboxInfo");
            term.innerHTML = "";

            if (!res) {
                term.innerText = "Execution failed. No output from sandbox.";
                term.style.color = "#ef4444";
                return;
            }

            info.innerText = res.sandbox_type || "Completed";

            if (res.status === "Compile Error") {
                term.innerText = `Compilation Failed:\n\n${res.compile_error}`;
                term.style.color = "#f43f5e";
                return;
            }

            if (res.status === "System Error") {
                term.innerText = `System Error:\n\n${res.compile_error || res.error || "Execution setup failed"}`;
                term.style.color = "#f43f5e";
                return;
            }

            // Print test cases breakdown
            let html = "";
            
            const results = res.results || [];
            results.forEach((tc, idx) => {
                const statusColor = tc.passed ? "#10b981" : "#ef4444";
                const statusLabel = tc.passed ? "PASSED" : (tc.status || "FAILED");
                const hiddenLabel = tc.is_hidden ? " [HIDDEN TEST CASE]" : "";

                html += `<div style="margin-bottom: 12px; border-bottom: 1px solid #1e293b; padding-bottom: 8px;">`;
                html += `<span style="color:${statusColor}; font-weight:700;">Test Case ${idx + 1}:${hiddenLabel} ${statusLabel}</span>`;
                html += ` <span style="color:#64748b; font-size:0.75rem;">(${tc.run_time_ms} ms)</span>\n`;
                
                if (!tc.passed || !tc.is_hidden) {
                    if (tc.input && tc.input !== "SQL Test Database") html += `<div style="color:#64748b; margin-top:4px;">Input: <span style="color:#94a3b8;">${JSON.stringify(tc.input)}</span></div>`;
                    if (tc.expected) html += `<div style="color:#64748b;">Expected: <span style="color:#10b981;">${JSON.stringify(tc.expected)}</span></div>`;
                    if (tc.actual) html += `<div style="color:#64748b;">Actual: <span style="color:${statusColor};">${JSON.stringify(tc.actual)}</span></div>`;
                    if (tc.error) html += `<div style="color:#f43f5e;">Error: ${tc.error}</div>`;
                }
                html += `</div>`;
            });

            const scoreColor = res.score === 100 ? "#10b981" : "#f59e0b";
            let headerHtml = `<div style="font-size:1.1rem; font-weight:700; color:${scoreColor}; margin-bottom:15px;">`;
            if (isSubmit) {
                headerHtml += `✓ Submission Complete. Score: ${res.score}/100 - Status: ${res.status}`;
            } else {
                headerHtml += `✓ Run Finished. Sample Test Cases Passed: ${res.score}%`;
            }
            headerHtml += `</div>`;

            term.innerHTML = headerHtml + html;
            term.style.color = "#f1f5f9";
        }
    </script>
</body>
</html>
"""


VOICE_CONSOLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Interview Console</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
        }
        body {
            background: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 10px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 480px;
            overflow: hidden;
        }
        .console {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 16px;
            padding: 24px;
            width: 100%;
            max-width: 650px;
            backdrop-filter: blur(12px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
        }
        .header {
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 12px;
        }
        .title {
            font-size: 1.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #a5b4fc, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }
        .status-badge {
            font-size: 0.75rem;
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: rgba(255, 255, 255, 0.05);
            color: #94a3b8;
            transition: all 0.3s ease;
        }
        .status-badge.connected { background: rgba(99, 102, 241, 0.2); color: #818cf8; }
        .status-badge.speaking { background: rgba(240, 147, 251, 0.25); color: #f093fb; box-shadow: 0 0 10px rgba(240, 147, 251, 0.2); }
        .status-badge.listening { background: rgba(239, 68, 68, 0.25); color: #f87171; box-shadow: 0 0 10px rgba(239, 68, 68, 0.2); }
        .status-badge.processing { background: rgba(168, 85, 247, 0.25); color: #c084fc; box-shadow: 0 0 10px rgba(168, 85, 247, 0.2); }
        .status-badge.completed { background: rgba(16, 185, 129, 0.25); color: #34d399; }
        
        .orb-outer {
            width: 140px;
            height: 140px;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }
        .orb-ring {
            position: absolute;
            width: 130px;
            height: 130px;
            border-radius: 50%;
            border: 2px solid rgba(99, 102, 241, 0.15);
            transition: all 0.5s ease;
        }
        .orb-ring.active {
            border: 2.5px dashed #818cf8;
            animation: spin 12s linear infinite;
        }
        .orb {
            width: 90px;
            height: 90px;
            border-radius: 50%;
            background: radial-gradient(circle, #6366f1 0%, #4338ca 100%);
            box-shadow: 0 0 35px rgba(99, 102, 241, 0.55);
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 2.2rem;
            z-index: 10;
        }
        .orb:hover {
            transform: scale(1.08);
        }
        .orb.speaking {
            background: radial-gradient(circle, #f093fb 0%, #f5576c 100%);
            box-shadow: 0 0 45px rgba(240, 147, 251, 0.8);
            animation: pulse-speaking 1.2s infinite ease-in-out alternate;
        }
        .orb.listening {
            background: radial-gradient(circle, #ef4444 0%, #991b1b 100%);
            box-shadow: 0 0 45px rgba(239, 68, 68, 0.8);
            animation: pulse-listening 1s infinite ease-in-out alternate;
        }
        .orb.processing {
            background: radial-gradient(circle, #a855f7 0%, #6b21a8 100%);
            box-shadow: 0 0 35px rgba(168, 85, 247, 0.6);
            animation: pulse-processing 0.8s infinite ease-in-out alternate;
        }
        
        .display-area {
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .text-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 14px 18px;
            font-size: 0.95rem;
            line-height: 1.6;
        }
        .text-card.question {
            border-left: 4px solid #818cf8;
            background: linear-gradient(90deg, rgba(99, 102, 241, 0.06) 0%, transparent 100%);
            max-height: 120px;
            overflow-y: auto;
        }
        .text-card.transcript {
            border-right: 4px solid #10b981;
            background: linear-gradient(270deg, rgba(16, 185, 129, 0.06) 0%, transparent 100%);
            font-style: italic;
            color: #cbd5e1;
            text-align: right;
            max-height: 80px;
            overflow-y: auto;
        }
        .feedback-grid {
            display: grid;
            grid-template-columns: 85px 1fr;
            gap: 15px;
            align-items: center;
            border: 1px solid rgba(16, 185, 129, 0.25);
            background: rgba(16, 185, 129, 0.04);
            border-radius: 12px;
            padding: 14px;
            animation: fadeIn 0.5s ease-out;
        }
        .feedback-score {
            font-size: 2.5rem;
            font-weight: 900;
            color: #10b981;
            text-align: center;
            text-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
        }
        .feedback-details {
            font-size: 0.85rem;
            line-height: 1.5;
        }
        
        .controls {
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 16px;
        }
        .btn {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            color: #f8fafc;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .btn:hover {
            background: rgba(255,255,255,0.12);
            border-color: rgba(255,255,255,0.25);
        }
        .btn.primary {
            background: linear-gradient(135deg, #6366f1, #4f46e5);
            border: none;
            color: white;
        }
        .btn.primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        }
        .btn.record {
            background: #ef4444;
            border: none;
            color: white;
        }
        .btn.record.recording {
            animation: flash 1s infinite alternate;
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
        }
        
        .toggle-group {
            display: flex;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 3px;
        }
        .toggle-btn {
            background: transparent;
            border: none;
            color: #94a3b8;
            padding: 6px 14px;
            font-size: 0.78rem;
            font-weight: 700;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .toggle-btn.active {
            background: rgba(99, 102, 241, 0.25);
            color: #a5b4fc;
            border: 1px solid rgba(99, 102, 241, 0.35);
        }

        /* Animations */
        @keyframes spin { 100% { transform: rotate(360deg); } }
        @keyframes flash { from { opacity: 1; } to { opacity: 0.6; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse-speaking {
            from { transform: scale(1); box-shadow: 0 0 25px rgba(240, 147, 251, 0.5); }
            to { transform: scale(1.08); box-shadow: 0 0 50px rgba(240, 147, 251, 0.85); }
        }
        @keyframes pulse-listening {
            from { transform: scale(1); box-shadow: 0 0 25px rgba(239, 68, 68, 0.5); }
            to { transform: scale(1.1); box-shadow: 0 0 50px rgba(239, 68, 68, 0.85); }
        }
        @keyframes pulse-processing {
            from { transform: scale(1); box-shadow: 0 0 15px rgba(168, 85, 247, 0.4); }
            to { transform: scale(1.06); box-shadow: 0 0 40px rgba(168, 85, 247, 0.75); }
        }
        
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div class="console">
        <div class="header">
            <h3 class="title">🎙️ VOICE CONSOLE</h3>
            <div id="statusBadge" class="status-badge">Disconnected</div>
        </div>

        <div id="startScreen" style="text-align: center; margin: 40px 0;">
            <p style="font-size: 1rem; margin-bottom: 25px; color: #94a3b8; max-width: 480px; line-height: 1.6;">
                Click below to start your voice interview. Make sure your microphone is connected and allowed in the browser.
            </p>
            <button class="btn primary" style="font-size: 1.05rem; padding: 14px 35px;" onclick="initSession()">
                🎙️ START VOICE INTERVIEW
            </button>
        </div>

        <div id="consoleContent" class="hidden" style="width: 100%; display: flex; flex-direction: column; align-items: center; gap: 16px;">
            <div class="orb-outer">
                <div id="orbRing" class="orb-ring"></div>
                <div id="orb" class="orb" onclick="toggleSpeak()">🎙️</div>
            </div>
            
            <div class="display-area">
                <div id="questionCard" class="text-card question">Connecting to interview service...</div>
                <div id="transcriptCard" class="text-card transcript hidden">Transcribing speech...</div>
                
                <div id="feedbackCard" class="feedback-grid hidden">
                    <div class="feedback-score" id="feedbackScore">7</div>
                    <div class="feedback-details">
                        <strong style="color: #34d399;">Real-time Evaluation:</strong><br>
                        <span id="feedbackSummary" style="color: #cbd5e1;"></span>
                    </div>
                </div>
            </div>

            <div class="controls">
                <div class="toggle-group">
                    <button id="btnServerVoice" class="toggle-btn active" onclick="setVoiceMode(true)">Server AI</button>
                    <button id="btnLocalVoice" class="toggle-btn" onclick="setVoiceMode(false)">Local Browser</button>
                </div>
                
                <div>
                    <button id="btnAction" class="btn primary" onclick="toggleSpeak()">Speak Answer</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const session_id = "{session_id}";
        let ws;
        let mediaRecorder;
        let isRecording = false;
        let useServerVoice = true;
        let recognition = null;
        let activeAudio = null;

        // Initialize SpeechRecognition
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            recognition.onstart = () => {
                setStatus('listening');
                setOrbState('listening');
            };
            
            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                console.log("Speech recognition transcript:", text);
                ws.send(JSON.stringify({ type: 'stop_recording', text: text }));
                setStatus('processing');
                setOrbState('processing');
            };
            
            recognition.onerror = (err) => {
                console.error("Speech recognition error:", err);
                setStatus('listening');
                setOrbState('ready');
            };
            
            recognition.onend = () => {
                if (isRecording) {
                    recognition.start();
                }
            };
        }

        function setStatus(status) {
            const badge = document.getElementById('statusBadge');
            badge.className = 'status-badge ' + status;
            badge.innerText = status;
        }

        function setOrbState(state) {
            const orb = document.getElementById('orb');
            const ring = document.getElementById('orbRing');
            
            orb.className = 'orb';
            ring.className = 'orb-ring';
            
            if (state === 'speaking') {
                orb.classList.add('speaking');
                orb.innerText = '🔊';
            } else if (state === 'listening') {
                orb.classList.add('listening');
                orb.innerText = '🔴';
                ring.classList.add('active');
            } else if (state === 'processing') {
                orb.classList.add('processing');
                orb.innerText = '⚙️';
                ring.classList.add('active');
            } else if (state === 'ready') {
                orb.innerText = '🎙️';
            } else if (state === 'completed') {
                orb.innerText = '🏆';
            }
        }

        function setVoiceMode(serverMode) {
            useServerVoice = serverMode;
            document.getElementById('btnServerVoice').className = serverMode ? 'toggle-btn active' : 'toggle-btn';
            document.getElementById('btnLocalVoice').className = !serverMode ? 'toggle-btn active' : 'toggle-btn';
        }

        function initSession() {
            // Unlock AudioContext for HTML5 audio playback policies
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            audioCtx.resume();

            document.getElementById('startScreen').classList.add('hidden');
            document.getElementById('consoleContent').classList.remove('hidden');
            
            connectWebSocket();
        }

        function connectWebSocket() {
            setStatus('connecting');
            
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws';
            const host = window.location.hostname;
            const wsUrl = wsProtocol + '://' + host + ':8000/api/v1/interview/voice-stream/' + session_id;
            
            ws = new WebSocket(wsUrl);
            ws.binaryType = 'arraybuffer';
            
            ws.onopen = () => {
                setStatus('connected');
                setOrbState('ready');
            };
            
            ws.onmessage = async (event) => {
                if (event.data instanceof ArrayBuffer) {
                    // Stop any ongoing playbacks
                    if (activeAudio) activeAudio.pause();
                    
                    const blob = new Blob([event.data], { type: 'audio/mp3' });
                    const audioUrl = URL.createObjectURL(blob);
                    activeAudio = new Audio(audioUrl);
                    
                    activeAudio.onplay = () => {
                        setStatus('speaking');
                        setOrbState('speaking');
                    };
                    
                    activeAudio.onended = () => {
                        setStatus('connected');
                        setOrbState('ready');
                        URL.revokeObjectURL(audioUrl);
                        activeAudio = null;
                    };
                    
                    activeAudio.play().catch(err => {
                        console.error("Autoplay failed:", err);
                        setStatus('connected');
                        setOrbState('ready');
                    });
                } else {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'text') {
                        document.getElementById('questionCard').innerText = data.text;
                        
                        // Speak locally if local mode active
                        if (!useServerVoice && recognition) {
                            speakLocal(data.text);
                        }
                    } else if (data.type === 'transcript') {
                        const transcriptCard = document.getElementById('transcriptCard');
                        transcriptCard.classList.remove('hidden');
                        transcriptCard.innerText = "You said: \"" + data.text + "\"";
                    } else if (data.type === 'state') {
                        setStatus(data.status);
                        if (data.status === 'completed') {
                            setOrbState('completed');
                            document.getElementById('questionCard').innerHTML = "<b>🎉 Voice Interview Complete!</b><br>Great job! You can now review your report. Please click the <b>'End Interview & View Final Report'</b> button above.";
                        }
                    } else if (data.type === 'feedback') {
                        const fbCard = document.getElementById('feedbackCard');
                        fbCard.classList.remove('hidden');
                        document.getElementById('feedbackScore').innerText = data.feedback.score;
                        
                        let tip = data.feedback.improvements && data.feedback.improvements.length > 0
                            ? data.feedback.improvements[0]
                            : "Excellent response!";
                        
                        document.getElementById('feedbackSummary').innerHTML = 
                            "<b>Strengths:</b> " + data.feedback.strengths.slice(0, 2).join(", ") + 
                            "<br><b>Gap Tip:</b> " + tip;
                    } else if (data.type === 'error') {
                        alert("Error: " + data.message);
                        setStatus('connected');
                        setOrbState('ready');
                    }
                }
            };
            
            ws.onclose = () => {
                setStatus('disconnected');
                setOrbState('ready');
            };
        }

        function speakLocal(text) {
            if (!('speechSynthesis' in window)) return;
            window.speechSynthesis.cancel();
            
            const cleanText = text.replace(/\\*\\*.*?\\*\\*/g, '').replace(/[❓👋🎉💡-]/g, '').trim();
            const utterance = new SpeechSynthesisUtterance(cleanText);
            
            utterance.onstart = () => {
                setStatus('speaking');
                setOrbState('speaking');
            };
            
            utterance.onend = () => {
                setStatus('connected');
                setOrbState('ready');
            };
            
            window.speechSynthesis.speak(utterance);
        }

        async function toggleSpeak() {
            if (isRecording) {
                // Stop Speaking
                isRecording = false;
                document.getElementById('btnAction').innerText = 'Speak Answer';
                document.getElementById('btnAction').className = 'btn primary';
                
                if (useServerVoice) {
                    stopServerRecording();
                } else if (recognition) {
                    recognition.stop();
                }
            } else {
                // Start Speaking
                if (activeAudio) {
                    activeAudio.pause();
                    activeAudio = null;
                }
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                }
                
                isRecording = true;
                document.getElementById('btnAction').innerText = 'Stop Speaking';
                document.getElementById('btnAction').className = 'btn record recording';
                
                if (useServerVoice) {
                    await startServerRecording();
                } else if (recognition) {
                    recognition.start();
                }
            }
        }

        async function startServerRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0 && ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(event.data);
                    }
                };
                
                mediaRecorder.onstop = () => {
                    stream.getTracks().forEach(track => track.stop());
                };
                
                ws.send(JSON.stringify({ type: 'start_recording' }));
                mediaRecorder.start(250);
                
                setStatus('listening');
                setOrbState('listening');
            } catch (err) {
                console.error("Mic error:", err);
                alert("Could not access microphone. Please check browser microphone permissions.");
                isRecording = false;
                document.getElementById('btnAction').innerText = 'Speak Answer';
                document.getElementById('btnAction').className = 'btn primary';
                setOrbState('ready');
            }
        }

        function stopServerRecording() {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                ws.send(JSON.stringify({ type: 'stop_recording' }));
                setStatus('processing');
                setOrbState('processing');
            }
        }
    </script>
</body>
</html>
"""


def render_step3_interview():
    """Step 3: The Mock Interview Chat Interface"""
    # Start interview if not started yet
    if not st.session_state.interview_started:
        with st.spinner("Setting up your interview..."):
            result = api_start_interview(st.session_state.session_id)
        
        if result.get("success"):
            st.session_state.interview_started = True
            st.session_state.total_questions = result.get("total_questions", 8)
            st.session_state.current_question_num = 1
            
            # Add first message to chat history
            st.session_state.chat_history.append({
                "role": "ai",
                "content": result.get("message", "Let's begin your interview!")
            })
        else:
            st.error(f"❌ {result.get('message', 'Failed to start interview.')}")
            return
            
    # Header with Mode Toggle
    col_title, col_toggle = st.columns([2, 1])
    with col_title:
        st.markdown("## 💬 Step 3: Mock Interview")
    with col_toggle:
        mode = st.radio(
            "Interview Mode",
            ["💬 Text Chat", "🎙️ Voice Session"],
            horizontal=True,
            label_visibility="collapsed",
            key="interview_mode"
        )
        
    if mode == "🎙️ Voice Session":
        # Format HTML with session ID
        html_content = VOICE_CONSOLE_HTML.replace("{session_id}", st.session_state.session_id)
        components.html(html_content, height=540)
        
        st.divider()
        if st.button("🏆 End Interview & View Final Report", use_container_width=True, key="btn_voice_summary"):
            st.session_state.step = 4
            st.rerun()
            
    else:
        # ---- Chat Display Area ----
        chat_container = st.container()
        
        with chat_container:
            # Display ONLY the latest AI message as a clear question block
            last_ai_msg = next((msg for msg in reversed(st.session_state.chat_history) if msg["role"] == "ai"), None)
            if last_ai_msg:
                st.markdown(f"""
                <div class="step-card active" style="font-size: 1.1rem; line-height: 1.6; padding: 2rem;">
                    {last_ai_msg["content"]}
                </div>
                """, unsafe_allow_html=True)
                
        st.divider()
        
        # ---- Answer Input Area ----
        if not st.session_state.interview_complete:
            with st.form(key="answer_form", clear_on_submit=True):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    user_input = st.text_area(
                        "Your Answer:",
                        placeholder="Type your answer here... Be specific and use examples from your experience.",
                        height=120,
                        key="answer_input",
                        label_visibility="collapsed",
                    )
                
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    submit = st.form_submit_button("📨 Submit", use_container_width=True)
            
            if submit and user_input.strip():
                # Add user message to chat
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input.strip()
                })
                
                with st.spinner("🤔 AI is evaluating your answer..."):
                    result = api_chat(st.session_state.session_id, user_input.strip())
                
                if result.get("success"):
                    # Update progress
                    st.session_state.current_question_num = result.get("current_question_number", 0)
                    st.session_state.interview_complete = result.get("is_interview_complete", False)
                    
                    # Add AI response + feedback to chat
                    ai_msg = {
                        "role": "ai",
                        "content": result.get("message", ""),
                        "feedback": result.get("feedback"),
                    }
                    st.session_state.chat_history.append(ai_msg)
                    
                    # If interview complete, jump straight to summary step
                    if st.session_state.interview_complete:
                        st.session_state.step = 4
                    
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('message', 'Failed to process answer.')}")
            # Empty submit — silently ignore; no warning shown

        
        else:
            # Interview complete - show summary button
            st.success("🎉 Interview complete! View your final summary below.")
            if st.button("🏆 View Final Summary", use_container_width=True, key="btn_summary"):
                st.session_state.step = 4
                st.rerun()


def render_step4_coding():
    """Step 4: Coding Assessment"""
    st.markdown("## 💻 Step 4: Coding Assessment")
    st.info(
        "💡 **Instructions**: Select a coding challenge from the list below. "
        "Write your solution in the Monaco Editor interface on the right. "
        "Ensure you click **'Submit Solution'** to submit your final code. "
        "Once done, click the verification button at the bottom to continue."
    )
    
    # Check if challenges are in session state, if not fetch them
    if "challenges_list" not in st.session_state or not st.session_state.challenges_list:
        with st.spinner("Fetching challenges..."):
            res = api_get_challenges()
            if res.get("success"):
                st.session_state.challenges_list = res.get("challenges", [])
            else:
                st.error(f"Failed to fetch challenges: {res.get('message')}")
                st.session_state.challenges_list = []
                
    if not st.session_state.challenges_list:
        st.warning("No coding challenges available.")
        return
        
    challenges = st.session_state.challenges_list
    challenge_titles = [c["title"] for c in challenges]
    
    # Selected challenge index
    selected_title = st.selectbox("Select Challenge:", challenge_titles, key="challenge_select")
    selected_challenge = next(c for c in challenges if c["title"] == selected_title)
    
    # Render Monaco IDE in iframe
    challenge_id = selected_challenge["id"]
    session_id = st.session_state.session_id
    
    # Format the Monaco Editor HTML content
    default_templates_js = json.dumps(selected_challenge["template_code"])
    title_js = json.dumps(selected_challenge["title"])
    desc_js = json.dumps(selected_challenge["description"])
    diff_js = json.dumps(selected_challenge["difficulty"])
    
    # Replace placeholders in MONACO_EDITOR_HTML
    formatted_html = MONACO_EDITOR_HTML.replace("{challenge_id}", str(challenge_id))
    formatted_html = formatted_html.replace("{session_id}", str(session_id))
    formatted_html = formatted_html.replace("{backend_url}", BACKEND_URL)
    formatted_html = formatted_html.replace("{default_templates}", default_templates_js)
    formatted_html = formatted_html.replace("{challenge_title}", title_js)
    formatted_html = formatted_html.replace("{challenge_description}", desc_js)
    formatted_html = formatted_html.replace("{challenge_difficulty}", diff_js)
    
    # Render the IDE iframe
    components.html(formatted_html, height=700)
    
    st.divider()
    
    # Verification area
    col_v, col_n = st.columns([1, 1])
    with col_v:
        if st.button("🔍 Verify Submission Status", use_container_width=True):
            with st.spinner("Checking submissions..."):
                sub_res = api_get_coding_submissions(session_id)
                if sub_res.get("success") and sub_res.get("submissions"):
                    subs = sub_res.get("submissions")
                    # Check if there is a submission for the current challenge
                    curr_subs = [s for s in subs if str(s["challenge_id"]) == str(challenge_id)]
                    if curr_subs:
                        latest_sub = curr_subs[0]
                        st.session_state.coding_submission_verified = True
                        st.session_state.latest_coding_score = latest_sub["score"]
                        st.session_state.latest_coding_status = latest_sub["status"]
                        st.success(
                            f"✅ Verified! Submission found. Score: **{latest_sub['score']}/100** | Status: **{latest_sub['status']}**"
                        )
                    else:
                        st.warning("⚠️ No submission found for this selected challenge yet. Make sure to click 'Submit Solution' inside the editor.")
                else:
                    st.warning("⚠️ No submissions found for this session. Please submit your solution in the editor first.")
                    
    with col_n:
        # Continue to Step 5
        btn_enabled = st.session_state.get("coding_submission_verified", False)
        if st.button("🏆 Proceed to Final Summary", disabled=not btn_enabled, use_container_width=True):
            st.session_state.step = 5
            # Force regeneration of summary since coding was added
            st.session_state.final_summary = None
            st.rerun()


def render_report_details(summary: dict, show_actions: bool = True):
    """Render details of a candidate report. Reused in step 5 and analytics dashboard."""
    avg_score = summary.get("average_score", 0)
    recommendation = summary.get("recommendation", "")
    candidate_name = summary.get("candidate_name", "Candidate")
    
    # Determine color based on score
    if avg_score >= 8:
        score_gradient = "linear-gradient(135deg, #10b981, #059669)"
    elif avg_score >= 5:
        score_gradient = "linear-gradient(135deg, #f59e0b, #d97706)"
    else:
        score_gradient = "linear-gradient(135deg, #ef4444, #dc2626)"
    
    st.markdown(f"""
    <div class="summary-header">
        <h2 style="color: #e2e8f0; margin-bottom: 1rem;">🎯 Interview Report for {candidate_name}</h2>
        <div style="display: flex; justify-content: center; gap: 3rem; flex-wrap: wrap;">
            <div>
                <div class="score-display">{avg_score}/10</div>
                <div class="score-label">Average Score</div>
            </div>
            <div>
                <div style="font-size: 2rem; font-weight: 800; 
                     background: {score_gradient};
                     -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                     background-clip: text;">
                    {recommendation}
                </div>
                <div class="score-label">Recommendation</div>
            </div>
            <div>
                <div style="font-size: 2rem; font-weight: 800; color: #818cf8;">
                    {summary.get("answered_questions", 0)}/{summary.get("total_questions", 0)}
                </div>
                <div class="score-label">Questions Answered</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ---- Metrics Row ----
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Average Score", f"{avg_score}/10")
    with col2:
        answered = summary.get("answered_questions", 0)
        total = summary.get("total_questions", 0)
        completion = f"{int((answered/total)*100)}%" if total > 0 else "0%"
        st.metric("✅ Completion", completion)
    with col3:
        scores = [s.get("score", 0) for s in summary.get("score_breakdown", [])]
        if scores:
            st.metric("🎯 Highest Score", f"{max(scores)}/10")
    
    st.divider()
    
    # ---- Overall Feedback ----
    overall_feedback = summary.get("overall_feedback", "")
    if overall_feedback:
        st.markdown("### 📝 Overall Feedback")
        st.markdown(f"""
        <div class="feedback-card">
            <p style="color: #e2e8f0; line-height: 1.8; margin: 0;">{overall_feedback}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ---- Coding Assessment Section ----
    coding_subs = summary.get("coding_submissions", [])
    if coding_subs:
        st.markdown("### 💻 Coding Assessment Submissions")
        for sub in coding_subs:
            title = sub.get("challenge_title", "Coding Challenge")
            status = sub.get("status", "Unknown")
            score = sub.get("score", 0)
            lang = sub.get("language", "python").upper()
            code = sub.get("code", "")
            
            # Color status
            if status == "Passed":
                status_color = "#10b981"
            elif status in ["Time Limit Exceeded", "Memory Limit Exceeded", "Compile Error", "Runtime Error"]:
                status_color = "#ef4444"
            else:
                status_color = "#f59e0b"
                
            with st.expander(f"💻 {title} ({lang}) — Status: {status} — Score: {score}/100"):
                st.markdown(f"**Status:** <span style='color: {status_color}; font-weight: bold;'>{status}</span>", unsafe_allow_html=True)
                st.markdown(f"**Score:** **{score}/100**")
                st.markdown("**Submitted Code:**")
                st.code(code, language=lang.lower())
                
                # Show results breakdown if available
                res_details = sub.get("results", {})
                if res_details and "results" in res_details:
                    st.markdown("**Test Case Run Details:**")
                    tc_runs = res_details["results"]
                    for idx, tc in enumerate(tc_runs):
                        tc_status = "PASSED" if tc.get("passed") else tc.get("status", "FAILED")
                        tc_color = "#10b981" if tc.get("passed") else "#ef4444"
                        st.markdown(
                            f"- Test Case {idx + 1}: <span style='color: {tc_color}; font-weight: bold;'>{tc_status}</span> "
                            f"({tc.get('run_time_ms', 0)} ms)",
                            unsafe_allow_html=True
                        )
        st.divider()
    
    # ---- Question-by-Question Breakdown ----
    st.markdown("### 📋 Question-by-Question Breakdown")
    
    breakdown = summary.get("score_breakdown", [])
    for item in breakdown:
        q_num = item.get("question_number", "?")
        q_text = item.get("question", "")
        q_score = item.get("score", 0)
        q_type = item.get("question_type", "technical")
        strengths = item.get("strengths", [])
        improvements = item.get("improvements", [])
        
        # Score color
        if q_score >= 8:
            color = "#10b981"
        elif q_score >= 5:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        
        badge_class = "badge-technical" if q_type == "technical" else "badge-hr"
        badge_label = "TECHNICAL" if q_type == "technical" else "HR"
        
        with st.expander(f"Q{q_num}. {q_text[:80]}{'...' if len(q_text) > 80 else ''} — Score: {q_score}/10"):
            col_a, col_b = st.columns([1, 3])
            
            with col_a:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 3rem; font-weight: 800; color: {color};">{q_score}</div>
                    <div style="color: #94a3b8; font-size: 0.8rem;">out of 10</div>
                    <span class="question-badge {badge_class}">{badge_label}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col_b:
                if strengths:
                    st.markdown("**✅ Strengths:**")
                    for s in strengths:
                        st.markdown(f"- {s}")
                
                if improvements:
                    st.markdown("**💡 Areas to Improve:**")
                    for i in improvements:
                        st.markdown(f"- {i}")
    
    st.divider()
    
    if show_actions:
        # ---- Action Buttons ----
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Start a New Interview", use_container_width=True, key="btn_new"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        with col2:
            # Allow reviewing the interview chat
            if st.button("💬 Review Interview Chat", use_container_width=True, key="btn_review"):
                st.session_state.step = 3
                st.rerun()


def render_step5_summary():
    """Step 5: Final Summary & Score"""
    st.markdown("## 🏆 Step 5: Final Interview Summary")
    
    # Fetch summary from backend
    if not st.session_state.final_summary:
        with st.spinner("🔄 Generating your final report..."):
            summary = api_get_summary(st.session_state.session_id)
            st.session_state.final_summary = summary
    
    summary = st.session_state.final_summary
    
    if not summary or not summary.get("success"):
        st.warning("⚠️ No interview data found. Please complete the interview first.")
        return
        
    render_report_details(summary, show_actions=True)


def render_analytics_dashboard():
    """Render the Recruitment Analytics & Proctoring Dashboard"""
    import pandas as pd
    
    # If a candidate drill down is selected
    selected_session_id = st.session_state.get("analytics_selected_session_id")
    if selected_session_id:
        if st.button("⬅️ Back to Analytics Dashboard", key="btn_back_analytics"):
            st.session_state.analytics_selected_session_id = None
            st.rerun()
        
        with st.spinner("🔄 Fetching candidate details..."):
            summary = api_get_summary(selected_session_id)
            if summary and summary.get("success"):
                render_report_details(summary, show_actions=False)
            else:
                st.error("⚠️ Failed to load candidate report detail.")
        return

    # Load high-level overview metrics
    with st.spinner("🔄 Loading dashboard data..."):
        overview = api_get_analytics_overview()
        
    if not overview or not overview.get("success"):
        st.error("⚠️ Failed to connect to backend analytics API. Please verify that the FastAPI backend server is running and database is seeded.")
        return
        
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Interviews", overview.get("total_interviews", 0))
    with col2:
        st.metric("🎯 Avg Candidate Score", f"{overview.get('average_score', 0.0)}/10")
    with col3:
        st.metric("📈 Pass Rate", f"{overview.get('pass_rate', 0.0)}%")
    with col4:
        st.metric("🛡️ Total Proctor Violations", overview.get("total_violations", 0))
        
    # Tabs layout
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Performance & Trends", 
        "🛡️ Proctoring & Integrity", 
        "🧠 Skills & Insights", 
        "📋 Candidate Audit Logs"
    ])
    
    # ── TAB 1: Performance & Trends ─────────────────────────────────────
    with tab1:
        # Score Trend
        trend_res = api_get_analytics_performance_trend()
        if trend_res.get("success") and trend_res.get("trend"):
            trend_df = pd.DataFrame(trend_res["trend"])
            trend_df = trend_df.rename(columns={"date": "Date", "average_score": "Average Score"})
            trend_df = trend_df.set_index("Date")
            st.markdown("### 📈 Candidate Score Trend over Time")
            st.line_chart(trend_df["Average Score"])
        else:
            st.info("No trend data available yet.")
            
        # Skill distribution
        st.divider()
        skills_res = api_get_analytics_skills()
        if skills_res.get("success") and skills_res.get("skills"):
            skills_df = pd.DataFrame(skills_res["skills"])
            
            col_sk1, col_sk2 = st.columns(2)
            with col_sk1:
                st.markdown("### 📊 Skill Frequency (Number of Candidates)")
                skills_freq_df = skills_df[["skill", "candidate_count"]].rename(columns={"skill": "Skill", "candidate_count": "Candidates"})
                st.bar_chart(skills_freq_df.set_index("Skill"))
            with col_sk2:
                st.markdown("### 🎯 Average Score by Skill")
                skills_score_df = skills_df[["skill", "average_score"]].rename(columns={"skill": "Skill", "average_score": "Avg Score"})
                st.bar_chart(skills_score_df.set_index("Skill"))
        else:
            st.info("No skill distribution data available yet.")
            
    # ── TAB 2: Proctoring & Integrity ───────────────────────────────────
    with tab2:
        proctor_res = api_get_analytics_proctor_violations()
        if proctor_res.get("success"):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("### ⚠️ Violations by Event Type")
                by_type = proctor_res.get("by_type", [])
                if by_type:
                    type_df = pd.DataFrame(by_type)
                    type_df = type_df.rename(columns={"event_type": "Violation Type", "count": "Count"})
                    st.bar_chart(type_df.set_index("Violation Type"))
                else:
                    st.info("No violations recorded.")
            with col_p2:
                st.markdown("### 🚨 Candidates with Most Violations")
                high_risk = proctor_res.get("high_risk_candidates", [])
                if high_risk:
                    hr_df = pd.DataFrame(high_risk)
                    hr_df = hr_df.rename(columns={"candidate_name": "Candidate", "count": "Violations"})
                    st.bar_chart(hr_df.set_index("Candidate")["Violations"])
                else:
                    st.info("No violations recorded.")
            
            st.divider()
            st.markdown("### 📋 Recent Proctoring Logs Feed")
            recent_logs = proctor_res.get("recent_logs", [])
            if recent_logs:
                logs_df = pd.DataFrame(recent_logs)
                logs_df["created_at"] = pd.to_datetime(logs_df["created_at"]).dt.strftime("%Y-%m-%d %H:%M:%S")
                logs_df["details"] = logs_df["details"].apply(lambda x: x.get("violation", str(x)) if isinstance(x, dict) else str(x))
                logs_df = logs_df.rename(columns={
                    "candidate_name": "Candidate",
                    "event_type": "Event Type",
                    "created_at": "Timestamp",
                    "details": "Description"
                })
                st.dataframe(logs_df[["Timestamp", "Candidate", "Event Type", "Description"]], use_container_width=True)
            else:
                st.info("No proctor logs recorded.")
        else:
            st.error("Failed to load proctoring analytics.")
            
    # ── TAB 3: Skills & Insights ────────────────────────────────────────
    with tab3:
        sw_res = api_get_analytics_strengths_weaknesses()
        if sw_res.get("success"):
            col_sw1, col_sw2 = st.columns(2)
            with col_sw1:
                st.markdown("### ✅ Top Candidate Strengths")
                strengths = sw_res.get("strengths", [])
                if strengths:
                    for idx, s in enumerate(strengths):
                        st.markdown(f"**{idx + 1}. {s['text']}** — ({s['count']} candidates)")
                else:
                    st.info("No strengths data recorded.")
            with col_sw2:
                st.markdown("### 💡 Key Areas for Improvement")
                weaknesses = sw_res.get("weaknesses", [])
                if weaknesses:
                    for idx, w in enumerate(weaknesses):
                        st.markdown(f"**{idx + 1}. {w['text']}** — ({w['count']} candidates)")
                else:
                    st.info("No improvement data recorded.")
        else:
            st.error("Failed to load strengths & weaknesses insights.")
            
    # ── TAB 4: Candidate Audit Logs ──────────────────────────────────────
    with tab4:
        history_res = api_get_analytics_history()
        if history_res.get("success") and history_res.get("history"):
            history = history_res.get("history", [])
            hist_df = pd.DataFrame(history)
            
            hist_df["created_at"] = pd.to_datetime(hist_df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
            display_df = hist_df.copy()
            display_df["skills_detected"] = display_df["skills_detected"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
            display_df = display_df.rename(columns={
                "candidate_name": "Candidate",
                "experience_years": "Experience",
                "skills_detected": "Skills",
                "average_score": "Score",
                "recommendation": "Recommendation",
                "violations_count": "Violations",
                "created_at": "Date",
                "status": "Status"
            })
            st.dataframe(
                display_df[["Date", "Candidate", "Experience", "Skills", "Score", "Recommendation", "Violations", "Status"]],
                use_container_width=True
            )
            
            st.divider()
            st.markdown("### 🔍 Drill Down Candidate Audit Report")
            cand_options = {
                f"{c['candidate_name']} ({c['created_at'][:16].replace('T', ' ')}) - Score: {c['average_score']}": c['session_id']
                for c in history
            }
            selected_cand = st.selectbox(
                "Select a candidate to view their complete report:",
                ["-- Select Candidate --"] + list(cand_options.keys()),
                key="analytics_cand_select"
            )
            if selected_cand != "-- Select Candidate --":
                st.session_state.analytics_selected_session_id = cand_options[selected_cand]
                st.rerun()
        else:
            st.info("No candidate interview logs found.")


# ============================================
# Main App Entry Point
# ============================================
def main():
    """Main app controller"""
    init_session_state()
    
    render_hero()
    mode = render_sidebar_steps()
    
    if mode == "Analytics Dashboard":
        render_analytics_dashboard()
        return
        
    # Route to current step
    current_step = st.session_state.step
    
    if current_step == 1:
        render_step1_upload()
    elif current_step == 2:
        render_step2_questions()
    elif current_step == 3:
        render_step3_interview()
    elif current_step == 4:
        render_step4_coding()
    elif current_step == 5:
        render_step5_summary()
    else:
        st.error("Invalid step. Please refresh the page.")


if __name__ == "__main__":
    main()
