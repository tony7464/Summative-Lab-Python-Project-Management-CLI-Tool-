"""JSON persistence for users, projects, and tasks."""

import json
import logging
from pathlib import Path

from models.project import Project
from models.task import Task
from models.user import User
from utils.errors import PersistenceError

logger = logging.getLogger(__name__)


class StorageService:
    """Load and save the full object graph to a local JSON file."""

    def __init__(self, path=None):
        """Create a storage service pointed at the data file.

        Args:
            path: Optional custom path. Defaults to data/project_data.json.
        """
        root = Path(__file__).resolve().parent.parent
        self.path = Path(path) if path else root / "data" / "project_data.json"
        self.users = []
        self.projects = []
        self.tasks = []

    def load(self):
        """Load persisted records or create a clean file when needed.

        Missing files are initialized. Malformed JSON is backed up and
        replaced so the CLI can continue instead of crashing.

        Returns:
            StorageService: The loaded service for chaining.
        """
        if not self.path.exists():
            logger.info("Data file missing at %s; creating a new store.", self.path)
            self._reset()
            self.save()
            return self

        try:
            raw = self.path.read_text(encoding="utf-8")
        except OSError as exc:
            raise PersistenceError(f"Could not read data file: {exc}") from exc

        if not raw.strip():
            logger.warning("Data file was empty. Starting with a blank store.")
            self._reset()
            return self

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            backup = self.path.with_suffix(".json.corrupt")
            try:
                backup.write_text(raw, encoding="utf-8")
            except OSError:
                backup = None
            location = f" A backup was saved to {backup}." if backup else ""
            raise PersistenceError(
                f"Data file is malformed JSON.{location} Fix or delete "
                f"{self.path} and try again. Details: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise PersistenceError("Data file must contain a JSON object.")

        try:
            self._hydrate(data)
        except (KeyError, TypeError, ValueError) as exc:
            raise PersistenceError(
                f"Data file is missing required fields: {exc}"
            ) from exc
        return self

    def save(self):
        """Write the current object graph using an atomic replace.

        Raises:
            PersistenceError: If the file cannot be written.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), indent=2)
        tmp_path = self.path.with_suffix(".json.tmp")
        try:
            tmp_path.write_text(payload + "\n", encoding="utf-8")
            tmp_path.replace(self.path)
        except OSError as exc:
            raise PersistenceError(f"Could not save data file: {exc}") from exc
        logger.info("Saved tracker data to %s", self.path)

    def to_dict(self):
        """Serialize users, projects, tasks, and ID counters.

        Returns:
            dict: Persistable store payload.
        """
        return {
            "users": [user.to_dict() for user in self.users],
            "projects": [project.to_dict() for project in self.projects],
            "tasks": [task.to_dict() for task in self.tasks],
            "meta": {
                "user_id_counter": User._id_counter,
                "project_id_counter": Project._id_counter,
                "task_id_counter": Task._id_counter,
            },
        }

    def add_user(self, name, email):
        """Create and persist a user.

        Args:
            name: Display name.
            email: Unique email address.

        Returns:
            User: The created user.

        Raises:
            ValueError: If the email is already in use.
        """
        if User.find_by_email(self.users, email):
            raise ValueError(f"A user with email '{email}' already exists.")
        if User.find_by_name(self.users, name):
            raise ValueError(f"A user named '{name}' already exists.")
        user = User(name=name, email=email)
        self.users.append(user)
        self.save()
        return user

    def add_project(self, user, title, description="", due_date=None):
        """Create a project owned by the given user.

        Args:
            user: Owning User.
            title: Unique project title.
            description: Optional summary.
            due_date: Optional due date.

        Returns:
            Project: The created project.

        Raises:
            ValueError: If the title is already used.
        """
        if Project.find_by_title(self.projects, title):
            raise ValueError(f"A project titled '{title}' already exists.")
        project = Project(title=title, description=description, due_date=due_date, owner=user)
        user.add_project(project)
        self.projects.append(project)
        self.save()
        return project

    def add_task(self, project, title, assigned_to=None, status="todo"):
        """Create a task on a project.

        Args:
            project: Parent Project.
            title: Task title unique within the project.
            assigned_to: Optional User assignee.
            status: Initial workflow status.

        Returns:
            Task: The created task.

        Raises:
            ValueError: If the project already has this task title.
        """
        if project.find_task(title):
            raise ValueError(
                f"Project '{project.title}' already has a task titled '{title}'."
            )
        task = Task(title=title, status=status, assigned_to=assigned_to, project=project)
        project.add_task(task)
        self.tasks.append(task)
        self.save()
        return task

    def require_user(self, name):
        """Return a user by name or raise a clear error.

        Args:
            name: User display name.

        Returns:
            User: The matching user.

        Raises:
            ValueError: If no user matches.
        """
        user = User.find_by_name(self.users, name)
        if user is None:
            raise ValueError(f"No user named '{name}' was found.")
        return user

    def require_project(self, title):
        """Return a project by title or raise a clear error.

        Args:
            title: Project title.

        Returns:
            Project: The matching project.

        Raises:
            ValueError: If no project matches.
        """
        project = Project.find_by_title(self.projects, title)
        if project is None:
            raise ValueError(f"No project titled '{title}' was found.")
        return project

    def require_task(self, project, title):
        """Return a task on a project or raise a clear error.

        Args:
            project: Parent Project.
            title: Task title.

        Returns:
            Task: The matching task.

        Raises:
            ValueError: If no task matches.
        """
        task = project.find_task(title)
        if task is None:
            raise ValueError(
                f"No task titled '{title}' was found on project '{project.title}'."
            )
        return task

    def _reset(self):
        """Clear in-memory collections and ID counters."""
        self.users = []
        self.projects = []
        self.tasks = []
        User.reset_id_counter(1)
        Project.reset_id_counter(1)
        Task.reset_id_counter(1)

    def _hydrate(self, data):
        """Rebuild objects and wire relationships from raw JSON.

        Args:
            data: Decoded JSON object.
        """
        self._reset()
        users_by_id = {}
        for item in data.get("users", []):
            user = User.from_dict(item)
            self.users.append(user)
            users_by_id[user.id] = user

        projects_by_id = {}
        for item in data.get("projects", []):
            project = Project.from_dict(item)
            owner = users_by_id.get(item.get("owner_id"))
            if owner is not None:
                owner.add_project(project)
            self.projects.append(project)
            projects_by_id[project.id] = project

        for item in data.get("tasks", []):
            task = Task.from_dict(item)
            project = projects_by_id.get(item.get("project_id"))
            if project is not None:
                project.add_task(task)
            assignee = users_by_id.get(item.get("assigned_to_id"))
            if assignee is not None:
                task.assigned_to = assignee
            for contributor_id in item.get("contributor_ids", []):
                contributor = users_by_id.get(contributor_id)
                if contributor is not None:
                    task.add_contributor(contributor)
            self.tasks.append(task)

        meta = data.get("meta", {})
        User.reset_id_counter(max(meta.get("user_id_counter", 1), _next_id(self.users)))
        Project.reset_id_counter(
            max(meta.get("project_id_counter", 1), _next_id(self.projects))
        )
        Task.reset_id_counter(max(meta.get("task_id_counter", 1), _next_id(self.tasks)))


def _next_id(items):
    """Return the next ID after the highest currently used value.

    Args:
        items: Objects that expose an id attribute.

    Returns:
        int: Next available ID, or 1 when the collection is empty.
    """
    if not items:
        return 1
    return max(item.id for item in items) + 1
