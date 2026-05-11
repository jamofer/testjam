from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from testjam.database import Base


class UserNotificationPreference(Base):
    __tablename__ = "user_notification_preferences"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "event_type",
            name="uq_user_notification_preferences_user_event",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    in_app: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
    )
    email: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
    )
