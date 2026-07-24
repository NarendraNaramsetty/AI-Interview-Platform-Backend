class AIException(Exception):
    """Base class for all AI generation errors."""
    pass

class AITimeoutError(AIException):
    """Raised when the AI generation request times out."""
    pass

class AIParsingError(AIException):
    """Raised when the response cannot be parsed or fails JSON schema validation."""
    pass

class AIProviderError(AIException):
    """Raised when the AI provider returns a non-2xx status, rate limit, or auth failure."""
    pass
