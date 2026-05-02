#!/usr/bin/env python
"""
Usage:
    python scripts/create_admin.py --username admin --email admin@example.com --password secret
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from testjam.database import engine
from testjam.models import User, Project, ProjectMember
from testjam.auth.security import hash_password


def create_admin(username: str, email: str, password: str) -> None:
    with Session(engine) as db:
        if db.query(User).filter(User.username == username).first():
            print(f"User '{username}' already exists.")
            return

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Admin user '{username}' created with id={user.id}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create initial admin user")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    create_admin(args.username, args.email, args.password)
