from __future__ import annotations


class DomainError(Exception):
    """Base class for typed domain failures."""


class DomainValidationError(DomainError, ValueError):
    """Raised when a domain value is malformed or incomplete."""


class CrossWorkspaceError(DomainError):
    """Raised when related aggregates belong to different workspaces."""


class InvalidTransitionError(DomainError):
    """Raised when an aggregate state transition is not allowed."""
