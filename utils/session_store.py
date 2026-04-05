"""
In-Memory Session Store

Manages all active interview sessions in memory.
Each session contains:
- Resume text
- FAISS vector store
- Generated questions
- Conversation chain (with memory)
- Answer feedback history
- Current question index

NOTE: This is an in-memory store, so sessions are lost on server restart.
For production, use Redis or a database.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class SessionStore:
    """
    Simple in-memory store for interview sessions.
    Thread-safe for single-process deployments.
    """
    
    def __init__(self):
        # Main session storage: {session_id: session_data}
        self._sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(
        self,
        session_id: str,
        resume_text: str,
        vector_store: Any,
        candidate_name: str,
        skills: List[str],
        experience: str,
    ) -> None:
        """
        Create a new session after resume upload.
        
        Args:
            session_id: Unique session identifier
            resume_text: Raw extracted resume text
            vector_store: FAISS vector store object
            candidate_name: Detected candidate name
            skills: List of detected skills
            experience: Detected experience string
        """
        self._sessions[session_id] = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "resume_text": resume_text,
            "vector_store": vector_store,
            "candidate_name": candidate_name,
            "skills": skills,
            "experience": experience,
            "questions": [],              # Will be set after question generation
            "current_question_index": 0,  # Tracks which question we're on
            "answers_feedback": [],       # List of {question, score, feedback}
            "conversation_chain": None,   # LangChain conversational chain
        }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: The session ID to look up
            
        Returns:
            Session dict or None if not found
        """
        return self._sessions.get(session_id)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        return session_id in self._sessions
    
    def set_questions(self, session_id: str, questions: List[Any]) -> None:
        """
        Store generated questions in the session.
        
        Args:
            session_id: The session ID
            questions: List of InterviewQuestion objects
        """
        if session_id in self._sessions:
            self._sessions[session_id]["questions"] = questions
            self._sessions[session_id]["current_question_index"] = 0
    
    def set_conversation_chain(self, session_id: str, chain: Any) -> None:
        """
        Store the LangChain conversation chain (with memory) in session.
        
        Args:
            session_id: The session ID
            chain: LangChain ConversationChain object
        """
        if session_id in self._sessions:
            self._sessions[session_id]["conversation_chain"] = chain
    
    def set_current_question_index(self, session_id: str, index: int) -> None:
        """
        Update the current question index.
        
        Args:
            session_id: The session ID
            index: New question index
        """
        if session_id in self._sessions:
            self._sessions[session_id]["current_question_index"] = index
    
    def add_answer_feedback(self, session_id: str, feedback_data: dict) -> None:
        """
        Append feedback for a completed answer.
        
        Args:
            session_id: The session ID
            feedback_data: Dict with question, score, and feedback
        """
        if session_id in self._sessions:
            self._sessions[session_id]["answers_feedback"].append(feedback_data)
    
    def clear_answer_feedback(self, session_id: str) -> None:
        """
        Clear all stored answers (used when restarting interview).
        
        Args:
            session_id: The session ID
        """
        if session_id in self._sessions:
            self._sessions[session_id]["answers_feedback"] = []
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session to free memory.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[str]:
        """Return list of all active session IDs"""
        return list(self._sessions.keys())
    
    def get_session_count(self) -> int:
        """Return number of active sessions"""
        return len(self._sessions)


# Global session store instance - imported by services
session_store = SessionStore()
