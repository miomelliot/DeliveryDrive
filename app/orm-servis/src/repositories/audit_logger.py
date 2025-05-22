# src/repositories/audit_logger.py
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AuditLog


class AuditLogger:
    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        self.session: AsyncSession = session
        self.user_id: UUID = user_id

    def _safe_dict(self, obj: Any) -> dict[Any, Any]:
        if isinstance(obj, dict):
            return obj
        d = dict(obj.__dict__)
        d.pop("_sa_instance_state", None)
        return d

    async def log_create(self, obj: Any) -> None:
        await self._log(event="create", target=obj.__tablename__, new_values=self._safe_dict(obj))

    async def log_update(self, obj: Any, old: Any) -> None:
        await self._log(
            event="update",
            target=obj.__tablename__,
            old_values=self._safe_dict(old),
            new_values=self._safe_dict(obj),
        )

    async def log_delete(self, obj: Any) -> None:
        await self._log(event="delete", target=obj.__tablename__, old_values=self._safe_dict(obj))

    async def _log(
        self,
        event: str,
        target: str,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
    ) -> None:
        audit = AuditLog(
            user_id=self.user_id,
            event=event,
            target_table=target,
            timestamp=datetime.now(timezone.utc),
            old_values=old_values,
            new_values=new_values,
        )
        self.session.add(audit)
