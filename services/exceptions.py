"""Custom exceptions for the application"""


class DocumentAnalyzerException(Exception):
    """Base exception for Document Analyzer"""
    def __init__(self, message: str, error_code: str = "GENERAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ConfigurationError(DocumentAnalyzerException):
    """Configuration error"""
    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR")


class ValidationError(DocumentAnalyzerException):
    """Validation error"""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class LLMServiceError(DocumentAnalyzerException):
    """LLM service error"""
    def __init__(self, message: str):
        super().__init__(message, "LLM_ERROR")


class DatabaseError(DocumentAnalyzerException):
    """Database operation error"""
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")


class FileProcessingError(DocumentAnalyzerException):
    """File processing error"""
    def __init__(self, message: str):
        super().__init__(message, "FILE_PROCESSING_ERROR")


class StorageError(DocumentAnalyzerException):
    """Storage (S3) error"""
    def __init__(self, message: str):
        super().__init__(message, "STORAGE_ERROR")


class PineconeError(DocumentAnalyzerException):
    """Pinecone service error"""
    def __init__(self, message: str):
        super().__init__(message, "PINECONE_ERROR")


class NotFoundError(DocumentAnalyzerException):
    """Resource not found"""
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, "NOT_FOUND")


class AuthenticationError(DocumentAnalyzerException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")

