"""
Question Generation Service - Uses LangChain + FAISS to generate interview questions.

Process:
1. Retrieve relevant resume chunks from FAISS
2. Feed into OpenAI with a carefully crafted prompt
3. Parse and return structured questions
"""

from typing import List
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from utils.config import settings
from utils.session_store import session_store
from backend.models.schemas import InterviewQuestion, QuestionType


# ------------------------------------------------
# PROMPT TEMPLATE for Question Generation
# This prompt instructs the AI to generate structured questions
# ------------------------------------------------
QUESTION_GENERATION_PROMPT = """
You are an experienced technical interviewer. Based on the resume context provided below, 
generate exactly 8 interview questions for the candidate.

Generate:
- 5 TECHNICAL questions (based on their specific skills, projects, and technical experience)
- 3 HR/BEHAVIORAL questions (based on their background, career goals, and soft skills)

Resume Context:
{context}

Question: {question}

Instructions:
- Make questions specific to THIS candidate's resume (mention their actual skills/projects)
- Technical questions should test depth of knowledge
- HR questions should explore motivation, teamwork, and problem-solving
- Format your response EXACTLY like this:

TECHNICAL:
1. [question text] | TOPIC: [skill/topic name]
2. [question text] | TOPIC: [skill/topic name]
3. [question text] | TOPIC: [skill/topic name]
4. [question text] | TOPIC: [skill/topic name]
5. [question text] | TOPIC: [skill/topic name]

HR:
6. [question text] | TOPIC: [topic name]
7. [question text] | TOPIC: [topic name]
8. [question text] | TOPIC: [topic name]

Generate the questions now:
"""


def parse_questions_from_text(raw_text: str) -> List[InterviewQuestion]:
    """
    Parse the AI's raw text response into structured InterviewQuestion objects.
    
    The AI returns something like:
    "TECHNICAL:\n1. Tell me about Python... | TOPIC: Python\n..."
    
    Args:
        raw_text: Raw text from the AI
        
    Returns:
        List of InterviewQuestion objects
    """
    questions = []
    question_id = 1
    current_type = QuestionType.TECHNICAL
    
    lines = raw_text.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        
        # Detect section headers
        if line.upper().startswith("TECHNICAL:") or line.upper() == "TECHNICAL":
            current_type = QuestionType.TECHNICAL
            continue
        elif line.upper().startswith("HR:") or line.upper() == "HR":
            current_type = QuestionType.HR
            continue
        
        # Skip empty lines
        if not line:
            continue
        
        # Parse numbered questions like "1. Question text | TOPIC: Python"
        # Match patterns: "1. text", "1) text"
        import re
        match = re.match(r"^\d+[\.\)]\s*(.+)", line)
        if match:
            question_text = match.group(1).strip()
            topic = ""
            
            # Extract topic if present (format: "question | TOPIC: Python")
            if "| TOPIC:" in question_text:
                parts = question_text.split("| TOPIC:")
                question_text = parts[0].strip()
                topic = parts[1].strip() if len(parts) > 1 else ""
            elif "| Topic:" in question_text:
                parts = question_text.split("| Topic:")
                question_text = parts[0].strip()
                topic = parts[1].strip() if len(parts) > 1 else ""
            
            if question_text:
                questions.append(InterviewQuestion(
                    id=question_id,
                    question=question_text,
                    type=current_type,
                    topic=topic,
                ))
                question_id += 1
    
    # If parsing failed, create generic questions as fallback
    if not questions:
        fallback_questions = [
            InterviewQuestion(id=1, question="Tell me about your technical background and main skills.", type=QuestionType.TECHNICAL, topic="General"),
            InterviewQuestion(id=2, question="Describe a challenging project you've worked on and how you solved it.", type=QuestionType.TECHNICAL, topic="Problem Solving"),
            InterviewQuestion(id=3, question="How do you ensure code quality in your projects?", type=QuestionType.TECHNICAL, topic="Code Quality"),
            InterviewQuestion(id=4, question="Explain your experience with databases and data management.", type=QuestionType.TECHNICAL, topic="Databases"),
            InterviewQuestion(id=5, question="How do you stay updated with new technologies?", type=QuestionType.TECHNICAL, topic="Learning"),
            InterviewQuestion(id=6, question="Tell me about yourself and your career journey.", type=QuestionType.HR, topic="Background"),
            InterviewQuestion(id=7, question="Why are you interested in this role?", type=QuestionType.HR, topic="Motivation"),
            InterviewQuestion(id=8, question="Where do you see yourself in 5 years?", type=QuestionType.HR, topic="Career Goals"),
        ]
        return fallback_questions
    
    return questions[:8]  # Cap at 8 questions


def generate_questions(session_id: str) -> List[InterviewQuestion]:
    """
    Main function to generate interview questions for a session.
    Uses LangChain RetrievalQA to query the FAISS vector store.
    
    Args:
        session_id: The unique session ID (must have a processed resume)
        
    Returns:
        List of InterviewQuestion objects
    """
    # Get session data (includes vector store and resume info)
    session = session_store.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found. Please upload a resume first.")
    
    vector_store = session["vector_store"]
    
    # Initialize OpenAI chat model
    llm = ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        temperature=0.7,  # Slightly creative for varied questions
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-OpenRouter-Title": settings.OPENROUTER_SITE_NAME,
        }
    )
    
    # Create a retriever from the FAISS vector store
    # k=5 means retrieve top 5 most relevant chunks
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    # Create the prompt template
    prompt = PromptTemplate(
        template=QUESTION_GENERATION_PROMPT,
        input_variables=["context", "question"]
    )
    
    # Build RetrievalQA chain
    # This retrieves relevant resume chunks and feeds them to the LLM
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # "stuff" = put all context in one prompt
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
    )
    
    # Run the chain - the "question" here is just the instruction
    result = qa_chain.invoke({
        "query": "Generate 5 technical and 3 HR interview questions based on this resume."
    })
    
    # Parse the AI response into structured questions
    raw_text = result.get("result", "")
    questions = parse_questions_from_text(raw_text)
    
    # Save questions to session for use during the interview
    session_store.set_questions(session_id, questions)
    
    return questions
