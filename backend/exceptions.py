"""
Custom exception classes for CiperCare backend with detailed error handling
"""

class CiperCareException(Exception):
    """Base exception for all CiperCare errors"""
    def __init__(self, message: str, error_code: str = "UNKNOWN", details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ServiceInitializationError(CiperCareException):
    """Raised when a service fails to initialize"""
    def __init__(self, service_name: str, reason: str, details: dict = None):
        super().__init__(
            f"{service_name} failed to initialize: {reason}",
            error_code="SERVICE_INIT_ERROR",
            details=details or {"service": service_name}
        )


class DatabaseError(CiperCareException):
    """Raised when database operation fails"""
    def __init__(self, operation: str, reason: str, details: dict = None):
        super().__init__(
            f"Database {operation} failed: {reason}",
            error_code="DATABASE_ERROR",
            details=details or {"operation": operation}
        )


class SearchError(DatabaseError):
    """Raised when vector search fails"""
    def __init__(self, reason: str, patient_id: str = None, details: dict = None):
        details = details or {}
        if patient_id:
            details["patient_id"] = patient_id
        super().__init__(
            "search",
            reason,
            details=details
        )
        self.error_code = "SEARCH_ERROR"


class EmbeddingError(CiperCareException):
    """Raised when embedding generation fails"""
    def __init__(self, reason: str, query_length: int = None, details: dict = None):
        details = details or {}
        if query_length:
            details["query_length"] = query_length
        super().__init__(
            f"Failed to generate embedding: {reason}",
            error_code="EMBEDDING_ERROR",
            details=details
        )


class LLMError(CiperCareException):
    """Raised when LLM operation fails"""
    def __init__(self, reason: str, provider: str = None, details: dict = None):
        details = details or {}
        if provider:
            details["provider"] = provider
        super().__init__(
            f"LLM operation failed: {reason}",
            error_code="LLM_ERROR",
            details=details
        )


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out"""
    def __init__(self, timeout_seconds: int, provider: str = None):
        super().__init__(
            f"Request timed out after {timeout_seconds}s",
            provider=provider,
            details={"timeout": timeout_seconds}
        )
        self.error_code = "LLM_TIMEOUT"


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded"""
    def __init__(self, retry_after: int = None, provider: str = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            f"Rate limit exceeded",
            provider=provider,
            details=details
        )
        self.error_code = "LLM_RATE_LIMIT"


class AuthenticationError(CiperCareException):
    """Raised when authentication fails"""
    def __init__(self, reason: str, user: str = None, details: dict = None):
        details = details or {}
        if user:
            details["user"] = user
        super().__init__(
            f"Authentication failed: {reason}",
            error_code="AUTH_ERROR",
            details=details
        )


class AuthorizationError(CiperCareException):
    """Raised when user lacks required permissions"""
    def __init__(self, required_role: str, user: str = None, details: dict = None):
        details = details or {"required_role": required_role}
        if user:
            details["user"] = user
        super().__init__(
            f"Insufficient permissions. Required role: {required_role}",
            error_code="AUTHZ_ERROR",
            details=details
        )


class PatientAccessDeniedError(AuthorizationError):
    """Raised when user cannot access a patient record"""
    def __init__(self, patient_id: str, user: str = None, reason: str = None, details: dict = None):
        details = details or {"patient_id": patient_id}
        if reason:
            details["reason"] = reason
        super().__init__(
            required_role="attending",
            user=user,
            details=details
        )
        self.error_code = "PATIENT_ACCESS_DENIED"
        self.message = f"Access denied to patient {patient_id}"


class ValidationError(CiperCareException):
    """Raised when input validation fails"""
    def __init__(self, field: str, reason: str, value = None, details: dict = None):
        details = details or {"field": field}
        if value is not None:
            details["value"] = str(value)[:100]  # Limit value length in logs
        super().__init__(
            f"Validation error in field '{field}': {reason}",
            error_code="VALIDATION_ERROR",
            details=details
        )


class ConnectionError(CiperCareException):
    """Raised when connection to external service fails"""
    def __init__(self, service: str, url: str, reason: str, details: dict = None):
        details = details or {"service": service, "url": url}
        super().__init__(
            f"Failed to connect to {service}: {reason}",
            error_code="CONNECTION_ERROR",
            details=details
        )


class TimeoutError(CiperCareException):
    """Raised when operation times out"""
    def __init__(self, operation: str, timeout_seconds: float, details: dict = None):
        details = details or {"operation": operation, "timeout": timeout_seconds}
        super().__init__(
            f"{operation} timed out after {timeout_seconds}s",
            error_code="TIMEOUT_ERROR",
            details=details
        )


class ResourceNotFoundError(CiperCareException):
    """Raised when a requested resource is not found"""
    def __init__(self, resource_type: str, resource_id: str, details: dict = None):
        details = details or {"resource_type": resource_type, "resource_id": resource_id}
        super().__init__(
            f"{resource_type} '{resource_id}' not found",
            error_code="NOT_FOUND",
            details=details
        )
