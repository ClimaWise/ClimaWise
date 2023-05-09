"""Library custom exceptions"""


class APIKeyNotFoundError(Exception):
    """Raised when the API key is not defined/declared."""


class MethodNotImplementedError(Exception):
    """Raised when a method is not implemented."""
