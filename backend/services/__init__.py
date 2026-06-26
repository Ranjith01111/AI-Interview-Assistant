"""
Services package — business logic layer.

Services orchestrate:
  • Resume processing (PDF → FAISS → DB)
  • Question generation (LangChain RAG → DB)
  • Interview Agent (LangChain GPT-4o — memory, follow-ups, scoring)
  • Interview chat (Agent-powered conversation → DB)
  • Session management (Redis cache)
"""
