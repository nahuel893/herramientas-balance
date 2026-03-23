"""One-time migration: reads selections.json and inserts into app.user_selections.

Usage:
    python -m scripts.migrate_selections --user-id 1
    python -m scripts.migrate_selections --username admin

Requires the app to have been started at least once (so app schema exists).
"""

import argparse
import json
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from app import repository


SELECTIONS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "selections.json",
)


def main():
    parser = argparse.ArgumentParser(description="Migrate selections.json to database")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--user-id", type=int, help="Target user ID to assign selections to")
    group.add_argument("--username", type=str, help="Target username to assign selections to")
    args = parser.parse_args()

    # Ensure schema exists
    repository.ensure_app_schema()

    # Resolve user
    if args.username:
        user = repository.get_user_by_username(args.username)
        if not user:
            print(f"Error: user '{args.username}' not found. Create the user first.")
            sys.exit(1)
        user_id = user["id"]
    else:
        user = repository.get_user_by_id(args.user_id)
        if not user:
            print(f"Error: user with id {args.user_id} not found.")
            sys.exit(1)
        user_id = args.user_id

    # Read selections.json
    if not os.path.exists(SELECTIONS_FILE):
        print(f"Error: {SELECTIONS_FILE} not found. Nothing to migrate.")
        sys.exit(1)

    with open(SELECTIONS_FILE, "r", encoding="utf-8") as f:
        selections = json.load(f)

    if not selections:
        print("selections.json is empty. Nothing to migrate.")
        return

    # Insert each selection
    migrated = 0
    for name, data in selections.items():
        table = data.get("table", "")
        columns = data.get("columns", [])
        if not table or not columns:
            print(f"  Skipping '{name}': missing table or columns")
            continue

        repository.save_user_selection(user_id, name, table, columns)
        print(f"  Migrated: '{name}' ({table}, {len(columns)} columns)")
        migrated += 1

    print(f"\nDone. {migrated}/{len(selections)} selections migrated to user_id={user_id}.")


if __name__ == "__main__":
    main()
