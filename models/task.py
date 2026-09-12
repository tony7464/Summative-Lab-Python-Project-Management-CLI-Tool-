"""Tasks that belong to a project and can have many contributors."""

from models.work_item import WorkItem


class Task(WorkItem):
    """A project task with an assignee and optional contributors.

    Relationships:
        - Many tasks belong to one project.
        - Many-to-many: a task can have many contributing users.
    """

    _id_counter = 1

    def __init__(
        self,
        title,
        status="todo",
        assigned_to=None,
        task_id=None,
        project=None,
    ):
        """Create a task and attach optional owner/project links.

        Args:
            title: Task title.
            status: Workflow status inherited from WorkItem.
            assigned_to: Primary User responsible for the task.
            task_id: Optional persisted identifier.
            project: Optional parent Project.
        """
        super().__init__(title, status=status)
        self.id = task_id if task_id is not None else Task.next_id()
        self._assigned_to = None
        self._contributors = []
        self.project = project
        self.assigned_to = assigned_to

    @classmethod
    def next_id(cls):
        """Allocate the next task ID from the class-level counter.

        Returns:
            int: A new unique task ID.
        """
        current = cls._id_counter
        cls._id_counter += 1
        return current

    @classmethod
    def reset_id_counter(cls, next_value=1):
        """Reset the ID counter after loading persisted records.

        Args:
            next_value: Value the next new task should receive.
        """
        cls._id_counter = next_value

    @classmethod
    def from_dict(cls, data):
        """Build a Task from a stored dictionary.

        Args:
            data: Mapping with id, title, and status.

        Returns:
            Task: A hydrated task without relationships attached yet.
        """
        return cls(title=data["title"], status=data.get("status", "todo"), task_id=data["id"])

    @classmethod
    def find_by_title(cls, tasks, title):
        """Find a task by case-insensitive title.

        Args:
            tasks: Collection of Task objects.
            title: Title to match.

        Returns:
            Task | None: The first matching task, if any.
        """
        needle = (title or "").strip().lower()
        for task in tasks:
            if task.title.lower() == needle:
                return task
        return None

    @property
    def assigned_to(self):
        """Return the primary assignee, if one is set."""
        return self._assigned_to

    @assigned_to.setter
    def assigned_to(self, user):
        """Set the primary assignee and keep contributor links in sync.

        Args:
            user: User instance or None.
        """
        self._assigned_to = user
        if user is not None:
            self.add_contributor(user)

    @property
    def contributors(self):
        """Return users linked to this task."""
        return list(self._contributors)

    def add_contributor(self, user):
        """Add a user to this task's contributor set.

        Args:
            user: User who helps with the task.
        """
        if user is None:
            return
        if user not in self._contributors:
            self._contributors.append(user)
        user.add_task(self)

    def context_payload(self):
        """Return structured data for insight/AI clients.

        Returns:
            dict: JSON-friendly task fields.
        """
        assignee = self.assigned_to.name if self.assigned_to else None
        return {
            "title": self.title,
            "status": self.status,
            "assigned_to": assignee,
            "contributors": [user.name for user in self._contributors],
        }

    def to_dict(self):
        """Serialize the task with relationship IDs.

        Returns:
            dict: Persistable task fields.
        """
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "project_id": self.project.id if self.project else None,
            "assigned_to_id": self.assigned_to.id if self.assigned_to else None,
            "contributor_ids": [user.id for user in self._contributors],
        }

    def __repr__(self):
        """Return a debug representation."""
        assignee = self.assigned_to.name if self.assigned_to else None
        return (
            f"Task(id={self.id}, title={self.title!r}, "
            f"status={self.status!r}, assigned_to={assignee!r})"
        )
