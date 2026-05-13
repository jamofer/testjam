#!/usr/bin/env python
"""
Delete API tokens whose `expires_at` is in the past. Run periodically
(cron, Kubernetes CronJob, etc.) to keep the api_tokens table clean.

Usage:
    python scripts/purge_expired_tokens.py [--dry-run]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from testjam.database import engine
from testjam.services.token_purge import purge_expired_tokens


def main() -> None:
    parser = argparse.ArgumentParser(description="Purge expired API tokens")
    parser.add_argument("--dry-run", action="store_true", help="Report count without deleting")
    args = parser.parse_args()

    with Session(engine) as db:
        count = purge_expired_tokens(db, dry_run=args.dry_run)
    verb = "would delete" if args.dry_run else "deleted"
    print(f"{verb} {count} expired token(s)")


if __name__ == "__main__":
    main()
