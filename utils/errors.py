"""Custom exceptions used across the project tracker."""


class TrackerError(Exception):
    """Base error for user-facing tracker failures."""


class NotFoundError(TrackerError):
    """Raised when a requested user, project, or task cannot be found."""


class PersistenceError(TrackerError):
    """Raised when data cannot be loaded or saved safely."""


class ServiceError(TrackerError):
    """Raised when an external service call fails."""
