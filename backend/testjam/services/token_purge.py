from datetime import datetime, timezone

from sqlalchemy.orm import Session

from testjam.models.token import ApiToken


def purge_expired_tokens(db: Session, dry_run: bool = False) -> int:
    now = datetime.now(timezone.utc)
    expired = (
        db.query(ApiToken)
        .filter(ApiToken.expires_at.is_not(None), ApiToken.expires_at <= now)
        .all()
    )
    count = len(expired)
    if dry_run:
        return count
    for token in expired:
        db.delete(token)
    db.commit()
    return count
