"""
Resume Service - Handles PDF parsing, embedding, and FAISS storage.

Steps:
1. Parse PDF text with PyPDF
2. Split text into chunks
3. Create embeddings with OpenAI
4. Store in FAISS vector store
"""

import os
import re
import uuid
from typing import Tuple, List

from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

from utils.config import settings
from utils.session_store import session_store


def parse_pdf(file_bytes: bytes) -> str:
    """
    Extract raw text from PDF bytes using PyPDF.
    
    Args:
        file_bytes: The raw PDF file content as bytes
        
    Returns:
        Extracted text as a single string
    """
    import io
    reader = PdfReader(io.BytesIO(file_bytes))
    
    full_text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text.append(page_text)
    
    return "\n".join(full_text)


def extract_candidate_name(resume_text: str) -> str:
    """
    Try to extract candidate name from the top of the resume.
    Simple heuristic: first non-empty line is usually the name.
    
    Args:
        resume_text: Raw resume text
        
    Returns:
        Candidate name or "Candidate" as fallback
    """
    lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
    
    # First line is often the name (usually 2-3 words, all caps or title case)
    if lines:
        first_line = lines[0]
        # Check if it looks like a name (2-4 words, no special chars except spaces)
        words = first_line.split()
        if 2 <= len(words) <= 4 and all(w.replace(".", "").isalpha() for w in words):
            return first_line.title()
    
    return "Candidate"


def extract_skills(resume_text: str) -> List[str]:
    """
    Extract key skills mentioned in the resume.
    Looks for common skill keywords.
    
    Args:
        resume_text: Raw resume text
        
    Returns:
        List of detected skills
    """
    # Common tech skills to look for (case-insensitive)
    skill_keywords = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
        "React", "Angular", "Vue", "Node.js", "Django", "FastAPI", "Flask",
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
        "TensorFlow", "PyTorch", "Scikit-learn", "OpenAI", "LangChain",
        "Data Science", "Data Analysis", "Pandas", "NumPy", "Spark",
        "Git", "CI/CD", "Agile", "Scrum", "REST API", "GraphQL",
        "Linux", "Bash", "PowerShell", "Microservices", "System Design",
    ]
    
    detected = []
    resume_lower = resume_text.lower()
    
    for skill in skill_keywords:
        if skill.lower() in resume_lower:
            detected.append(skill)
    
    return detected[:15]  # Return top 15 skills max


def extract_experience_years(resume_text: str) -> str:
    """
    Try to detect years of experience from the resume text.
    
    Args:
        resume_text: Raw resume text
        
    Returns:
        Experience string like "3 years" or "Not specified"
    """
    # Look for patterns like "3 years", "5+ years", "X years of experience"
    patterns = [
        r"(\d+)\+?\s*years?\s*of\s*(?:work\s*)?experience",
        r"(\d+)\+?\s*years?\s*experience",
        r"experience\s*of\s*(\d+)\+?\s*years?",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, resume_text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}+ years"
    
    return "Not specified"


def create_vector_store(resume_text: str) -> FAISS:
    """
    Convert resume text into embeddings and store in FAISS.
    
    Steps:
    1. Split text into overlapping chunks for better retrieval
    2. Create embeddings using OpenAI
    3. Store in FAISS in-memory vector store
    
    Args:
        resume_text: The full resume text
        
    Returns:
        FAISS vector store object
    """
    # Step 1: Split text into manageable chunks
    # chunk_size=500 means each chunk is ~500 characters
    # chunk_overlap=50 ensures context continuity between chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_text(resume_text)
    
    # Wrap chunks in LangChain Document objects
    documents = [
        Document(page_content=chunk, metadata={"source": "resume", "chunk_id": i})
        for i, chunk in enumerate(chunks)
    ]
    
    # Step 2 & 3: Create embeddings and store in FAISS
    embeddings = OpenAIEmbeddings(
        model=settings.OPENROUTER_EMBEDDING_MODEL,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-OpenRouter-Title": settings.OPENROUTER_SITE_NAME,
        }
    )
    
    vector_store = FAISS.from_documents(documents, embeddings)
    
    return vector_store


def process_resume(file_bytes: bytes) -> Tuple[str, dict]:
    """
    Main function to process a resume PDF.
    - Parse PDF -> Extract text -> Create embeddings -> Store in FAISS
    - Creates a unique session ID for this interview
    
    Args:
        file_bytes: Raw PDF file bytes
        
    Returns:
        Tuple of (session_id, metadata_dict)
    """
    # Parse the PDF
    resume_text = parse_pdf(file_bytes)
    
    if not resume_text.strip():
        raise ValueError("Could not extract text from the PDF. Please ensure it's a text-based PDF.")
    
    # Extract metadata from resume
    candidate_name = extract_candidate_name(resume_text)
    skills = extract_skills(resume_text)
    experience = extract_experience_years(resume_text)
    
    # Create FAISS vector store
    vector_store = create_vector_store(resume_text)
    
    # Generate a unique session ID for this interview
    session_id = str(uuid.uuid4())
    
    # Save everything to our in-memory session store
    session_store.create_session(
        session_id=session_id,
        resume_text=resume_text,
        vector_store=vector_store,
        candidate_name=candidate_name,
        skills=skills,
        experience=experience,
    )
    
    metadata = {
        "candidate_name": candidate_name,
        "skills_detected": skills,
        "experience_years": experience,
    }
    
    return session_id, metadata
