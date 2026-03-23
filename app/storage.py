from . import repository


def load_selections(user_id: int) -> dict:
    """Load all selections for a given user from the database."""
    return repository.get_user_selections(user_id)


def save_selection(user_id: int, name: str, table: str, columns: list[str]) -> None:
    """Save (upsert) a selection for a given user."""
    repository.save_user_selection(user_id, name, table, columns)


def delete_selection(user_id: int, name: str) -> bool:
    """Delete a selection by name for a given user. Returns True if deleted."""
    return repository.delete_user_selection(user_id, name)
