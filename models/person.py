"""Base person types shared by tracker users."""

from utils.validators import require_text


class Person:
    """A named person. User inherits this to add account details."""

    def __init__(self, name):
        """Initialize a person with a validated name.

        Args:
            name: Display name for the person.
        """
        self.name = name

    @property
    def name(self):
        """Return the person's display name."""
        return self._name

    @name.setter
    def name(self, value):
        """Set the display name after rejecting blank values.

        Args:
            value: Proposed name.

        Raises:
            ValueError: If the name is empty.
        """
        self._name = require_text(value, "Name")

    def display_name(self):
        """Return a friendly label used in CLI output.

        Returns:
            str: The person's name.
        """
        return self.name

    def __str__(self):
        """Return the display name."""
        return self.display_name()

    def __repr__(self):
        """Return a debug representation."""
        return f"{self.__class__.__name__}(name={self.name!r})"
