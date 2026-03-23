"""Bootstrap script to create a user in app.users.

Usage:
    python -m scripts.create_user --username admin --password secret123
    # or from project root:
    python scripts/create_user.py --username admin --password secret123
"""
import argparse
import sys
import os

# Allow running both as module and as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import repository
from app.auth import hash_password


def main():
    parser = argparse.ArgumentParser(description="Create a user in app.users")
    parser.add_argument("--username", required=True, help="Username for the new user")
    parser.add_argument("--password", required=True, help="Password (will be bcrypt-hashed)")
    args = parser.parse_args()

    if not args.username.strip() or not args.password.strip():
        print("Error: username and password must not be empty")
        sys.exit(1)

    repository.ensure_app_schema()

    password_hash = hash_password(args.password)
    try:
        user = repository.create_user(args.username.strip(), password_hash)
        print(f"User created: id={user['id']}, username={user['username']}")
    except Exception as e:
        print(f"Error creating user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
