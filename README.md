# 🎯 AI Interview Assistant (Agentic AI)

> An AI-powered mock interview system that analyzes your resume, generates personalized questions, conducts a conversational interview, and provides real-time scoring and feedback.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-0.2-orange?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.36-red?style=flat-square&logo=streamlit)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-purple?style=flat-square)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **Resume Upload** | Upload PDF, extract text with PyPDF |
| 🧠 **AI Analysis** | OpenAI embeddings + FAISS vector store |
| ❓ **Smart Questions** | 5 technical + 3 HR questions generated via LangChain RAG |
| 💬 **Mock Interview** | Conversational chat, one question at a time |
| 📊 **Live Feedback** | Score 0–10 + strengths + improvements per answer |
| 🧠 **Memory** | ConversationBufferMemory maintains full context |
| 🏆 **Final Summary** | Overall score + recommendation + breakdown |

---

## 📂 Project Structure

```
ai-interview-assistant/
│
├── backend/
│   ├── __init__.py
│   ├── main.py                  ← FastAPI app entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── resume_routes.py     ← POST /resume/upload
│   │   └── interview_routes.py  ← POST /interview/generate-questions, /chat, /summary
│   ├── services/
│   │   ├── __init__.py
│   │   ├── resume_service.py    ← PDF parsing, FAISS embedding
│   │   ├── question_service.py  ← LangChain RetrievalQA question generation
│   │   └── interview_service.py ← Conversation chain, scoring, summary
│   └── models/
│       ├── __init__.py
│       └── schemas.py           ← Pydantic models
│
├── frontend/
│   └── app.py                   ← Streamlit UI (4-step wizard)
│
├── utils/
│   ├── __init__.py
│   ├── config.py                ← Pydantic settings (.env loader)
│   └── session_store.py         ← In-memory session management
│
├── run_backend.py               ← Quick backend launcher
├── run_frontend.py              ← Quick frontend launcher
├── requirements.txt
├── .env.example
├── .env                         ← Your API keys (not committed to git)
└── README.md
```

---

## 🚀 Quick Start

### Step 1: Clone & Setup

```bash
# Navigate to project
cd "AI Interview Assistant"

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure API Key

Edit the `.env` file and add your OpenAI API key:

```env
OPENROUTER_API_KEY=sk-your-actual-api-key-here
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-small
```

> Get your API key at: https://platform.openai.com/api-keys

### Step 4: Run the Backend (Terminal 1)

```bash
python run_backend.py
```

You should see:
```
🚀 AI Interview Assistant - Backend Server
📡 API URL:   http://localhost:8000
📚 API Docs:  http://localhost:8000/docs
```

### Step 5: Run the Frontend (Terminal 2)

```bash
python run_frontend.py
```

This opens: **http://localhost:8501**

---

## 🎯 How to Use

1. **Upload Resume** → Upload your PDF resume
2. **Generate Questions** → AI creates 8 personalized questions
3. **Mock Interview** → Answer each question in the chat
4. **View Summary** → See your score, feedback, and recommendation

---

## 🧠 AI Architecture

```
Resume PDF
    │
    ▼
PyPDF (text extraction)
    │
    ▼
RecursiveCharacterTextSplitter (500-char chunks)
    │
    ▼
OpenAI text-embedding-3-small (vector embeddings)
    │
    ▼
FAISS VectorStore (similarity search)
    │
    ▼
LangChain RetrievalQA (question generation)
    │
    ▼
ConversationChain + ConversationBufferMemory (interview)
    │
    ▼
GPT-4o-mini (scoring + feedback + summary)
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/resume/upload` | Upload PDF resume |
| `POST` | `/api/v1/interview/generate-questions/{session_id}` | Generate questions |
| `POST` | `/api/v1/interview/start/{session_id}` | Start interview |
| `POST` | `/api/v1/interview/chat` | Send answer, get feedback |
| `GET`  | `/api/v1/interview/summary/{session_id}` | Final summary |
| `GET`  | `/health` | Health check |
| `GET`  | `/docs` | Swagger UI |

---

## 💡 Sample Prompts Used Internally

### Question Generation Prompt
```
You are an experienced technical interviewer. Based on the resume context provided below, 
generate exactly 8 interview questions:
- 5 TECHNICAL questions (based on skills, projects, technical experience)
- 3 HR/BEHAVIORAL questions (based on background, career goals, soft skills)
```

### Scoring Prompt
```
You are a professional AI interview coach named "Alex".
Score the candidate's answer from 0-10.
Return JSON: { score, strengths, improvements, model_answer_hint, acknowledgment }
```

### Summary Prompt
```
Based on this complete interview session, provide a final assessment with:
overall performance, top strengths, key areas for improvement, 
and hiring recommendation (Strong Hire / Consider / No Hire)
```

---

## ⚙️ Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Required | Your OpenRouter key |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Chat model |
| `OPENROUTER_EMBEDDING_MODEL` | `openai/text-embedding-3-small` | Embedding model |
| `BACKEND_PORT` | `8000` | FastAPI server port |

---

## 🔧 Troubleshooting

**"Cannot connect to backend"**
→ Make sure `python run_backend.py` is running in a separate terminal.

**"OpenAI/OpenRouter API key not valid"**
→ Check your `.env` file has the correct `OPENROUTER_API_KEY`.

**"Could not extract text from PDF"**
→ Ensure your PDF is text-based (not a scanned image). Try copy-pasting text from the PDF first.

**Questions seem generic**
→ Make sure your resume PDF contains detailed text (skills, projects, experience).

---

## 📝 License

MIT License — Free to use and modify.

---

*Built with ❤️ using FastAPI, LangChain, OpenAI, FAISS, and Streamlit*
