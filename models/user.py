"""User accounts that own projects and contribute to tasks."""

import re

from models.person import Person


class User(Person):
    """A tracker user with an email, owned projects, and contributed tasks.

    Relationships:
        - One-to-many: a user owns many projects.
        - Many-to-many: a user can contribute to many tasks.
    """

    _id_counter = 1
    _email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, name, email, user_id=None):
        """Create a user and assign the next available ID when needed.

        Args:
            name: Display name inherited from Person.
            email: Unique contact email.
            user_id: Optional persisted identifier.
        """
        super().__init__(name)
        self._projects = []
        self._tasks = []
        self.id = user_id if user_id is not None else User.next_id()
        self.email = email

    @classmethod
    def next_id(cls):
        """Allocate the next user ID from the class-level counter.

        Returns:
            int: A new unique user ID.
        """
        current = cls._id_counter
        cls._id_counter += 1
        return current

    @classmethod
    def reset_id_counter(cls, next_value=1):
        """Reset the ID counter after loading persisted records.

        Args:
            next_value: Value the next new user should receive.
        """
        cls._id_counter = next_value

    @classmethod
    def from_dict(cls, data):
        """Build a User from a stored dictionary.

        Args:
            data: Mapping with id, name, and email.

        Returns:
            User: A hydrated user without relationships attached yet.
        """
        return cls(name=data["name"], email=data["email"], user_id=data["id"])

    @classmethod
    def find_by_name(cls, users, name):
        """Find a user by case-insensitive name.

        Args:
            users: Collection of User objects.
            name: Name to match.

        Returns:
            User | None: The first matching user, if any.
        """
        needle = (name or "").strip().lower()
        for user in users:
            if user.name.lower() == needle:
                return user
        return None

    @classmethod
    def find_by_email(cls, users, email):
        """Find a user by email address.

        Args:
            users: Collection of User objects.
            email: Email to match.

        Returns:
            User | None: The matching user, if any.
        """
        needle = (email or "").strip().lower()
        for user in users:
            if user.email == needle:
                return user
        return None

    @property
    def email(self):
        """Return the user's normalized email."""
        return self._email

    @email.setter
    def email(self, value):
        """Validate and store a lowercase email address.

        Args:
            value: Proposed email.

        Raises:
            ValueError: If the email format is invalid.
        """
        candidate = (value or "").strip().lower()
        if not self._email_pattern.match(candidate):
            raise ValueError(f"Invalid email address: {value}")
        self._email = candidate

    @property
    def projects(self):
        """Return a copy of projects owned by this user."""
        return list(self._projects)

    @property
    def contributed_tasks(self):
        """Return tasks this user owns or contributes to."""
        return list(self._tasks)

    def add_project(self, project):
        """Attach a project to this user (one-to-many).

        Args:
            project: Project instance to own.
        """
        if project not in self._projects:
            self._projects.append(project)
        project.owner = self

    def add_task(self, task):
        """Record a many-to-many contribution to a task.

        Args:
            task: Task this user is assigned to or helping with.
        """
        if task not in self._tasks:
            self._tasks.append(task)

    def find_project(self, title):
        """Find an owned project by title.

        Args:
            title: Project title to match.

        Returns:
            Project | None: The matching project, if owned by this user.
        """
        needle = (title or "").strip().lower()
        for project in self._projects:
            if project.title.lower() == needle:
                return project
        return None

    def to_dict(self):
        """Serialize the user without nested relationship objects.

        Returns:
            dict: Persistable user fields.
        """
        return {"id": self.id, "name": self.name, "email": self.email}

    def __repr__(self):
        """Return a debug representation including the email."""
        return f"User(id={self.id}, name={self.name!r}, email={self.email!r})"
