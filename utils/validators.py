"""Input validation helpers used by models and CLI handlers."""

from datetime import date, datetime

from dateutil import parser as date_parser


def require_text(value, field_name):
    """Return a stripped string or raise ValueError when empty.

    Args:
        value: Raw user input.
        field_name: Label used in the error message.

    Returns:
        str: Cleaned non-empty text.

    Raises:
        ValueError: If the value is missing or blank.
    """
    if value is None:
        raise ValueError(f"{field_name} cannot be empty.")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} cannot be empty.")
    return text


def parse_due_date(value):
    """Parse flexible date input into a date object.

    Accepts ISO dates, common written dates, or an existing date.

    Args:
        value: A date, datetime, string, or None.

    Returns:
        date | None: A calendar date, or None when no due date is set.

    Raises:
        ValueError: If the value cannot be parsed as a date.
    """
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        parsed = date_parser.parse(str(value).strip(), fuzzy=False)
    except (ValueError, OverflowError, TypeError) as exc:
        raise ValueError(
            f"Could not parse due date '{value}'. Try YYYY-MM-DD."
        ) from exc
    return parsed.date()


def normalize_status(value):
    """Normalize a task status string to a supported value.

    Args:
        value: Raw status text.

    Returns:
        str: One of todo, in_progress, or complete.

    Raises:
        ValueError: If the status is not supported.
    """
    status = require_text(value, "Status").lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "todo": "todo",
        "to_do": "todo",
        "pending": "todo",
        "in_progress": "in_progress",
        "inprogress": "in_progress",
        "started": "in_progress",
        "complete": "complete",
        "completed": "complete",
        "done": "complete",
    }
    if status not in aliases:
        raise ValueError("Status must be todo, in_progress, or complete.")
    return aliases[status]
