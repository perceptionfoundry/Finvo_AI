"""Custom exceptions for Finvo AI application."""

from typing import Any, Dict, Optional


class FinvoAIException(Exception):
    """Base exception for Finvo AI application."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(FinvoAIException):
    """Raised when there's a configuration error."""
    pass


class FileProcessingError(FinvoAIException):
    """Raised when file processing fails."""
    pass


class UnsupportedFileFormatError(FileProcessingError):
    """Raised when an unsupported file format is encountered."""
    pass


class FileSizeError(FileProcessingError):
    """Raised when a file is too large."""
    pass


class ExtractionError(FinvoAIException):
    """Raised when data extraction fails."""
    pass


class AIServiceError(FinvoAIException):
    """Raised when AI service encounters an error."""
    pass


class ValidationError(FinvoAIException):
    """Raised when data validation fails."""
    pass


class DocumentLoaderError(FinvoAIException):
    """Raised when document loading fails."""
    pass


class ChainExecutionError(FinvoAIException):
    """Raised when LangChain execution fails."""
    pass