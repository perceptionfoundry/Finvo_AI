"""Professional FastAPI routes for Finvo AI invoice extraction service."""

import time
from typing import Dict, Any
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.finvo_ai.agents.invoice_extractor import InvoiceExtractionAgent
from src.finvo_ai.models.schemas import (
    InvoiceData,
    ExtractionRequest,
    ExtractionResponse,
    ErrorDetails
)
from src.finvo_ai.core.exceptions import (
    FinvoAIException,
    UnsupportedFileFormatError,
    FileSizeError,
    ExtractionError
)
from src.finvo_ai.utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["invoice-extraction"])


def get_extraction_agent() -> InvoiceExtractionAgent:
    """Dependency to get invoice extraction agent."""
    return InvoiceExtractionAgent()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "finvo-ai",
        "version": settings.app_version,
        "environment": settings.environment
    }


@router.get("/supported-formats")
async def get_supported_formats(
    agent: InvoiceExtractionAgent = Depends(get_extraction_agent)
):
    """Get list of supported file formats."""
    try:
        formats = agent.get_supported_formats()
        return {
            "supported_formats": formats,
            "total_formats": len(formats)
        }
    except Exception as e:
        logger.error("Failed to get supported formats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get supported formats")


@router.get("/schema")
async def get_extraction_schema():
    """Get the JSON schema for extracted invoice data."""
    try:
        return {
            "invoice_data_schema": InvoiceData.model_json_schema(),
            "extraction_request_schema": ExtractionRequest.model_json_schema(),
            "extraction_response_schema": ExtractionResponse.model_json_schema()
        }
    except Exception as e:
        logger.error("Failed to get schema", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get schema")


@router.post("/extract/upload", response_model=ExtractionResponse)
async def extract_from_upload(
    file: UploadFile = File(...),
    extract_fuel_info: bool = True,
    extract_line_items: bool = True,
    agent: InvoiceExtractionAgent = Depends(get_extraction_agent)
):
    """
    Extract financial data from uploaded invoice/receipt file.
    
    Supports: JPG, JPEG, PNG, PDF, GIF, BMP, WEBP
    """
    start_time = time.time()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    try:
        # Validate file format
        file_extension = Path(file.filename).suffix.lower()
        supported_formats = agent.get_supported_formats()
        
        if file_extension not in supported_formats:
            raise UnsupportedFileFormatError(
                f"Unsupported file format. Supported: {', '.join(supported_formats)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Create extraction request
        request = ExtractionRequest(
            file_name=file.filename,
            file_size=len(file_content),
            extract_fuel_info=extract_fuel_info,
            extract_line_items=extract_line_items
        )
        
        # Perform extraction
        result = agent.extract_from_bytes(file_content, file.filename, request)
        
        processing_time = time.time() - start_time
        
        logger.info(
            "Upload extraction completed",
            filename=file.filename,
            file_size=len(file_content),
            processing_time=processing_time,
            confidence_score=result.confidence_score
        )
        
        return ExtractionResponse(
            status="success",
            data=result,
            processing_time=processing_time,
            file_info={
                "filename": file.filename,
                "size": len(file_content),
                "format": file_extension,
                "content_type": file.content_type
            }
        )
        
    except FinvoAIException as e:
        logger.warning(
            "Extraction failed with known error",
            filename=file.filename if file.filename else "unknown",
            error=str(e),
            error_code=e.error_code
        )
        
        processing_time = time.time() - start_time
        
        # Determine error category and HTTP status
        if isinstance(e, UnsupportedFileFormatError):
            status_code = 400
            error_category = "UNSUPPORTED_FORMAT"
        elif isinstance(e, FileSizeError):
            status_code = 413
            error_category = "FILE_TOO_LARGE"
        elif isinstance(e, ExtractionError):
            status_code = 422
            error_category = "EXTRACTION_FAILED"
        else:
            status_code = 500
            error_category = "UNKNOWN_ERROR"
        
        # Return structured error response
        error_response = ExtractionResponse(
            status="error",
            data=None,
            error=ErrorDetails(
                message=str(e),
                category=error_category,
                code=getattr(e, 'error_code', None),
                details={
                    "filename": file.filename,
                    "file_size": len(file_content) if 'file_content' in locals() else None,
                    "processing_time": processing_time
                }
            ),
            processing_time=processing_time,
            file_info={
                "filename": file.filename,
                "size": len(file_content) if 'file_content' in locals() else None,
                "format": Path(file.filename).suffix.lower() if file.filename else None,
                "content_type": file.content_type
            }
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump()
        )
    
    except Exception as e:
        logger.error(
            "Unexpected error during upload extraction",
            filename=file.filename if file.filename else "unknown",
            error=str(e),
            exc_info=True
        )
        
        processing_time = time.time() - start_time
        
        # Return structured error response for unexpected errors
        error_response = ExtractionResponse(
            status="error",
            data=None,
            error=ErrorDetails(
                message=f"Unexpected processing error: {str(e)}",
                category="SYSTEM_ERROR",
                code="UNEXPECTED_ERROR",
                details={
                    "filename": file.filename if file.filename else "unknown",
                    "file_size": len(file_content) if 'file_content' in locals() else None,
                    "processing_time": processing_time,
                    "error_type": type(e).__name__
                }
            ),
            processing_time=processing_time,
            file_info={
                "filename": file.filename if file.filename else "unknown",
                "size": len(file_content) if 'file_content' in locals() else None,
                "format": Path(file.filename).suffix.lower() if file.filename else None,
                "content_type": getattr(file, 'content_type', None)
            }
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump()
        )



@router.get("/stats")
async def get_service_stats():
    """Get service statistics and information."""
    try:
        return {
            "service_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "model_info": {
                "model": settings.openai_model,
                "temperature": settings.openai_temperature,
                "max_tokens": settings.max_tokens
            },
            "limits": {
                "max_file_size_mb": settings.max_file_size_mb,
                "supported_formats": settings.allowed_file_extensions
            }
        }
    except Exception as e:
        logger.error("Failed to get service stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get service stats")