"""Projects owned by a user and containing many tasks."""

from datetime import date

from utils.validators import parse_due_date, require_text


class Project:
    """A project with a title, description, due date, and child tasks.

    Relationships:
        - Many projects belong to one owner.
        - One-to-many: a project contains many tasks.
    """

    _id_counter = 1

    def __init__(
        self,
        title,
        description="",
        due_date=None,
        project_id=None,
        owner=None,
    ):
        """Create a project and assign the next available ID when needed.

        Args:
            title: Unique project title.
            description: Optional project summary.
            due_date: Optional due date as a date or parseable string.
            project_id: Optional persisted identifier.
            owner: Optional owning User.
        """
        self._tasks = []
        self.owner = owner
        self.id = project_id if project_id is not None else Project.next_id()
        self.title = title
        self.description = description
        self.due_date = due_date

    @classmethod
    def next_id(cls):
        """Allocate the next project ID from the class-level counter.

        Returns:
            int: A new unique project ID.
        """
        current = cls._id_counter
        cls._id_counter += 1
        return current

    @classmethod
    def reset_id_counter(cls, next_value=1):
        """Reset the ID counter after loading persisted records.

        Args:
            next_value: Value the next new project should receive.
        """
        cls._id_counter = next_value

    @classmethod
    def from_dict(cls, data):
        """Build a Project from a stored dictionary.

        Args:
            data: Mapping with id, title, description, and due_date.

        Returns:
            Project: A hydrated project without relationships attached yet.
        """
        return cls(
            title=data["title"],
            description=data.get("description", ""),
            due_date=data.get("due_date"),
            project_id=data["id"],
        )

    @classmethod
    def find_by_title(cls, projects, title):
        """Find a project by case-insensitive title.

        Args:
            projects: Collection of Project objects.
            title: Title to match.

        Returns:
            Project | None: The first matching project, if any.
        """
        needle = (title or "").strip().lower()
        for project in projects:
            if project.title.lower() == needle:
                return project
        return None

    @property
    def title(self):
        """Return the project title."""
        return self._title

    @title.setter
    def title(self, value):
        """Set the project title after rejecting blank values.

        Args:
            value: Proposed title.

        Raises:
            ValueError: If the title is empty.
        """
        self._title = require_text(value, "Project title")

    @property
    def description(self):
        """Return the project description."""
        return self._description

    @description.setter
    def description(self, value):
        """Store a trimmed description, allowing an empty string.

        Args:
            value: Proposed description.
        """
        self._description = (value or "").strip()

    @property
    def due_date(self):
        """Return the project due date, if set."""
        return self._due_date

    @due_date.setter
    def due_date(self, value):
        """Parse and store a flexible due date.

        Args:
            value: Date, string, or None.
        """
        self._due_date = parse_due_date(value)

    @property
    def tasks(self):
        """Return a copy of tasks assigned to this project."""
        return list(self._tasks)

    @property
    def progress(self):
        """Return the percentage of tasks that are complete.

        Returns:
            float: Completion percentage from 0 to 100.
        """
        if not self._tasks:
            return 0.0
        done = sum(1 for task in self._tasks if task.is_complete)
        return round((done / len(self._tasks)) * 100, 1)

    @property
    def is_overdue(self):
        """Return whether the project is past due with open work."""
        if self._due_date is None:
            return False
        return date.today() > self._due_date and self.progress < 100

    @property
    def open_tasks(self):
        """Return tasks that are not complete."""
        return [task for task in self._tasks if not task.is_complete]

    def add_task(self, task):
        """Attach a task to this project (one-to-many).

        Args:
            task: Task instance to include.
        """
        if task not in self._tasks:
            self._tasks.append(task)
        task.project = self

    def find_task(self, title):
        """Find a child task by title.

        Args:
            title: Task title to match.

        Returns:
            Task | None: The matching task, if any.
        """
        needle = (title or "").strip().lower()
        for task in self._tasks:
            if task.title.lower() == needle:
                return task
        return None

    def next_recommended_task(self):
        """Choose a sensible next task using current statuses.

        Returns:
            Task | None: An in-progress task, otherwise the first todo item.
        """
        in_progress = [task for task in self._tasks if task.status == "in_progress"]
        if in_progress:
            return in_progress[0]
        todos = [task for task in self._tasks if task.status == "todo"]
        return todos[0] if todos else None

    def context_payload(self):
        """Return structured data for insight/AI clients.

        Returns:
            dict: JSON-friendly project and task fields.
        """
        return {
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "owner": self.owner.name if self.owner else None,
            "progress": self.progress,
            "is_overdue": self.is_overdue,
            "task_count": len(self._tasks),
            "open_task_count": len(self.open_tasks),
            "tasks": [task.context_payload() for task in self._tasks],
        }

    def to_dict(self):
        """Serialize the project with relationship IDs.

        Returns:
            dict: Persistable project fields.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "owner_id": self.owner.id if self.owner else None,
            "task_ids": [task.id for task in self._tasks],
        }

    def __str__(self):
        """Return a compact project label."""
        owner = self.owner.name if self.owner else "unassigned"
        due = self.due_date.isoformat() if self.due_date else "no due date"
        return f"{self.title} ({owner}, {due}, {self.progress}% complete)"

    def __repr__(self):
        """Return a debug representation."""
        return (
            f"Project(id={self.id}, title={self.title!r}, "
            f"due_date={self.due_date!r}, owner={getattr(self.owner, 'name', None)!r})"
        )
