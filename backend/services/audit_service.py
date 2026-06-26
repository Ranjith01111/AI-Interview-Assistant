"""
Audit Logging Service — Non-blocking stub.

Logs events to structlog only. Does NOT write to database.
This ensures auth flows (login/register) never crash due to missing tables.

To enable DB audit logging, run: 
  psql -U postgres -d interview_assistant -f scripts/migrate_add_missing_columns.sql
"""

from typing import Optional
from uuid import UUID
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger

logger = get_logger("backend.services.audit")


async def log_audit_event(
    db: AsyncSession,
    action: str,
    status: str,
    user_id: Optional[UUID] = None,
    request: Optional[Request] = None,
    details: Optional[dict] = None,
) -> None:
    """
    Log an audit event. Currently logs to console only (no DB write).
    This prevents HTTP 500 errors when audit_logs table doesn't exist.
    """
    ip = None
    if request and request.client:
        ip = request.client.host

    logger.info(
        "audit_event",
        action=action,
        status=status,
        user_id=str(user_id) if user_id else "anonymous",
        ip=ip,
        details=details,
    )
