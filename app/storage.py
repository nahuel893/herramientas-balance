import json
import os
from datetime import datetime

SELECTIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "selections.json")


def load_selections() -> dict:
    if os.path.exists(SELECTIONS_FILE):
        with open(SELECTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_selection(name: str, table: str, columns: list[str]) -> None:
    selections = load_selections()
    selections[name] = {
        "table": table,
        "columns": columns,
        "created_at": datetime.now().isoformat(),
    }
    with open(SELECTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(selections, f, indent=2, ensure_ascii=False)


def delete_selection(name: str) -> bool:
    selections = load_selections()
    if name not in selections:
        return False
    del selections[name]
    with open(SELECTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(selections, f, indent=2, ensure_ascii=False)
    return True
