class ContextEngineError(Exception):
    """Base exception for all errors raised by the Context Engine."""


class InvalidContextItemError(ContextEngineError):
    """Raised when a ContextItem fails schema, content, or lifecycle validation."""


class ContextItemNotFoundError(ContextEngineError):
    """Raised when an expected ContextItem is not found in the storage backend."""


class StorageError(ContextEngineError):
    """Raised when an underlying context storage operation fails."""


class InvalidQueryError(ContextEngineError):
    """Raised when a context query specification is malformed or invalid."""


class TokenBudgetExceededError(ContextEngineError):
    """Raised when context requirements exceed a non-negotiable hard token budget."""


class PolicyViolationError(ContextEngineError):
    """Raised when an operation breaches an active context policy (e.g. size, TTL, type)."""


class ScopeAccessViolationError(ContextEngineError):
    """Raised when an operation attempts to access, modify, or leak across tenant/session scopes."""


class ContextConfigurationError(ContextEngineError):
    """Raised when the Context Engine configuration is invalid."""
