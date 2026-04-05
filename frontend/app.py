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
        "step": 1,                # Current step: 1=Upload, 2=Questions, 3=Interview, 4=Summary
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


# ============================================
# UI Component Functions
# ============================================
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
    st.sidebar.markdown("## 📋 Interview Workflow")
    
    step = st.session_state.step
    
    steps = [
        (1, "📄", "Upload Resume"),
        (2, "🧠", "Generate Questions"),
        (3, "💬", "Mock Interview"),
        (4, "🏆", "Final Summary"),
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
                    st.success(f"✅ Generated {result['total_questions']} personalized interview questions!")
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('message', 'Failed to generate questions.')}")
        
        else:
            # Show generated questions
            st.markdown("### ❓ Your Interview Questions")
            
            technical_qs = [q for q in st.session_state.questions if q.get("type") == "technical"]
            hr_qs = [q for q in st.session_state.questions if q.get("type") == "hr"]
            
            if technical_qs:
                st.markdown("#### 💻 Technical Questions")
                for q in technical_qs:
                    topic = q.get("topic", "")
                    badge = f'<span class="question-badge badge-technical">TECHNICAL{" | " + topic if topic else ""}</span>'
                    st.markdown(f"""
                    <div class="step-card">
                        {badge}<br>
                        <span style="color: #e2e8f0; margin-top: 0.5rem; display: block;">
                            Q{q.get('id', '?')}. {q.get('question', '')}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            
            if hr_qs:
                st.markdown("#### 🤝 HR / Behavioral Questions")
                for q in hr_qs:
                    topic = q.get("topic", "")
                    badge = f'<span class="question-badge badge-hr">HR{" | " + topic if topic else ""}</span>'
                    st.markdown(f"""
                    <div class="step-card">
                        {badge}<br>
                        <span style="color: #e2e8f0; margin-top: 0.5rem; display: block;">
                            Q{q.get('id', '?')}. {q.get('question', '')}
                        </span>
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


def render_step3_interview():
    """Step 3: The Mock Interview Chat Interface"""
    st.markdown("## 💬 Step 3: Mock Interview")
    
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
    
    # ---- Chat Display Area ----
    chat_container = st.container()
    
    with chat_container:
        # Display ONLY the latest AI message as a clear question block
        # Removes Chat-style UI and hides live scoring during the interview per user request
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
                
                # If interview complete, move to step 4
                if st.session_state.interview_complete:
                    st.session_state.step = 4
                
                st.rerun()
            else:
                st.error(f"❌ {result.get('message', 'Failed to process answer.')}")
        
        elif submit and not user_input.strip():
            st.warning("⚠️ Please type your answer before submitting.")
    
    else:
        # Interview complete - show summary button
        st.success("🎉 Interview complete! View your final summary below.")
        if st.button("🏆 View Final Summary", use_container_width=True, key="btn_summary"):
            st.session_state.step = 4
            st.rerun()


def render_step4_summary():
    """Step 4: Final Summary & Score"""
    st.markdown("## 🏆 Step 4: Final Interview Summary")
    
    # Fetch summary from backend
    if not st.session_state.final_summary:
        with st.spinner("🔄 Generating your final report..."):
            summary = api_get_summary(st.session_state.session_id)
            st.session_state.final_summary = summary
    
    summary = st.session_state.final_summary
    
    if not summary or not summary.get("success"):
        st.warning("⚠️ No interview data found. Please complete the interview first.")
        return
    
    # ---- Overall Score Header ----
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


# ============================================
# Main App Entry Point
# ============================================
def main():
    """Main app controller"""
    init_session_state()
    
    render_hero()
    render_sidebar_steps()
    
    # Route to current step
    current_step = st.session_state.step
    
    if current_step == 1:
        render_step1_upload()
    elif current_step == 2:
        render_step2_questions()
    elif current_step == 3:
        render_step3_interview()
    elif current_step == 4:
        render_step4_summary()
    else:
        st.error("Invalid step. Please refresh the page.")


if __name__ == "__main__":
    main()
