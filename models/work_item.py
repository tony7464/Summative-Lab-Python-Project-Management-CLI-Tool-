"""Base class for items that track completion status."""

from utils.validators import normalize_status, require_text


class WorkItem:
    """A titled item with a workflow status.

    Task inherits this so status rules stay in one place.
    """

    VALID_STATUSES = ("todo", "in_progress", "complete")

    def __init__(self, title, status="todo"):
        """Initialize title and status.

        Args:
            title: Short name for the work item.
            status: Workflow state. Defaults to todo.
        """
        self.title = title
        self.status = status

    @property
    def title(self):
        """Return the work item title."""
        return self._title

    @title.setter
    def title(self, value):
        """Set the title after rejecting blank values.

        Args:
            value: Proposed title.

        Raises:
            ValueError: If the title is empty.
        """
        self._title = require_text(value, "Title")

    @property
    def status(self):
        """Return the current workflow status."""
        return self._status

    @status.setter
    def status(self, value):
        """Validate and store a supported status.

        Args:
            value: Raw status text.

        Raises:
            ValueError: If the status is not supported.
        """
        self._status = normalize_status(value)

    @property
    def is_complete(self):
        """Return whether the item is marked complete."""
        return self._status == "complete"

    def mark_complete(self):
        """Move the item to the complete status.

        Returns:
            WorkItem: The updated item for chaining.
        """
        self.status = "complete"
        return self

    def start(self):
        """Move a todo item into in_progress.

        Returns:
            WorkItem: The updated item for chaining.
        """
        if not self.is_complete:
            self.status = "in_progress"
        return self

    def __str__(self):
        """Return a compact title and status label."""
        return f"{self.title} [{self.status}]"
