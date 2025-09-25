"""Professional LangChain-based invoice extraction agent."""

import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from src.finvo_ai.core.exceptions import ExtractionError, AIServiceError, ValidationError
from src.finvo_ai.models.schemas import InvoiceData, ExtractionRequest
from src.finvo_ai.services.document_loader import DocumentLoaderService
from src.finvo_ai.utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


class InvoiceExtractionAgent:
    """Professional LangChain-powered invoice extraction agent."""
    
    def __init__(self):
        """Initialize the invoice extraction agent."""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key
        )
        self.document_loader = DocumentLoaderService()
        self.output_parser = JsonOutputParser(pydantic_object=InvoiceData)
        
        self.system_prompt = self._create_system_prompt()
        self.extraction_chain = self._create_extraction_chain()
        
        logger.info(
            "Invoice extraction agent initialized",
            model=settings.openai_model,
            temperature=settings.openai_temperature
        )
    
    def extract_from_file(self, file_path: Path, request: Optional[ExtractionRequest] = None) -> InvoiceData:
        """
        Extract invoice data from a file.
        
        Args:
            file_path: Path to the invoice file
            request: Optional extraction request parameters
            
        Returns:
            Extracted invoice data
            
        Raises:
            ExtractionError: If extraction fails
        """
        start_time = time.time()
        
        try:
            # Load document
            documents = self.document_loader.load_from_path(file_path)
            
            # Process documents
            result = self._process_documents(documents, request)
            
            processing_time = time.time() - start_time
            result.processing_metadata = {
                "processing_time": processing_time,
                "source_file": str(file_path),
                "document_count": len(documents),
                "model_used": settings.openai_model
            }
            
            logger.info(
                "File extraction completed",
                file_path=str(file_path),
                processing_time=processing_time,
                confidence_score=result.confidence_score
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "File extraction failed",
                file_path=str(file_path),
                error=str(e),
                exc_info=True
            )
            raise ExtractionError(f"Failed to extract data from file: {str(e)}") from e
    
    def extract_from_bytes(
        self, 
        file_bytes: bytes, 
        filename: str, 
        request: Optional[ExtractionRequest] = None
    ) -> InvoiceData:
        """
        Extract invoice data from file bytes.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            request: Optional extraction request parameters
            
        Returns:
            Extracted invoice data
        """
        start_time = time.time()
        
        try:
            # Load document from bytes
            documents = self.document_loader.load_from_bytes(file_bytes, filename)
            
            # Process documents
            result = self._process_documents(documents, request)
            
            processing_time = time.time() - start_time
            result.processing_metadata = {
                "processing_time": processing_time,
                "source_filename": filename,
                "file_size": len(file_bytes),
                "document_count": len(documents),
                "model_used": settings.openai_model
            }
            
            logger.info(
                "Bytes extraction completed",
                filename=filename,
                file_size=len(file_bytes),
                processing_time=processing_time,
                confidence_score=result.confidence_score
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Bytes extraction failed",
                filename=filename,
                error=str(e),
                exc_info=True
            )
            raise ExtractionError(f"Failed to extract data from bytes: {str(e)}") from e
    
    def extract_from_base64(
        self, 
        base64_data: str, 
        filename: str, 
        request: Optional[ExtractionRequest] = None
    ) -> InvoiceData:
        """
        Extract invoice data from base64 encoded file.
        
        Args:
            base64_data: Base64 encoded file content
            filename: Original filename
            request: Optional extraction request parameters
            
        Returns:
            Extracted invoice data
        """
        try:
            documents = self.document_loader.load_from_base64(base64_data, filename)
            return self._process_documents(documents, request)
            
        except Exception as e:
            logger.error(
                "Base64 extraction failed",
                filename=filename,
                error=str(e),
                exc_info=True
            )
            raise ExtractionError(f"Failed to extract data from base64: {str(e)}") from e
    
    def _process_documents(
        self, 
        documents: List[Document], 
        request: Optional[ExtractionRequest] = None
    ) -> InvoiceData:
        """Process loaded documents and extract invoice data."""
        if not documents:
            raise ExtractionError("No documents to process")
        
        try:
            # Prepare document content
            document_content = self._prepare_document_content(documents)
            
            # Create extraction context
            context = {
                "document_content": document_content,
                "extract_fuel_info": request.extract_fuel_info if request else True,
                "extract_line_items": request.extract_line_items if request else True,
                "document_metadata": [doc.metadata for doc in documents]
            }
            
            # Run extraction chain
            result = self.extraction_chain.invoke(context)
            
            # Validate and return result
            return self._validate_result(result)
            
        except Exception as e:
            raise ExtractionError(f"Document processing failed: {str(e)}") from e
    
    def _prepare_document_content(self, documents: List[Document]) -> str:
        """Prepare document content for processing."""
        content_parts = []
        
        for i, doc in enumerate(documents, 1):
            metadata_str = ", ".join(f"{k}={v}" for k, v in doc.metadata.items())
            content_parts.append(f"Document {i} (Metadata: {metadata_str}):\\n{doc.page_content}")
        
        return "\\n\\n".join(content_parts)
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for invoice extraction."""
        return """You are an expert financial document analysis AI specializing in invoice and receipt data extraction.

Your task is to analyze the provided document content and extract structured financial information with high accuracy.

EXTRACTION REQUIREMENTS:
1. Extract merchant/business information
2. Extract transaction date and time
3. Extract individual line items with quantities and prices
4. Extract total amounts, taxes, and subtotals
5. Identify payment methods
6. Special attention to fuel/gas receipts (gallons, price per gallon, fuel type)
7. Extract invoice/receipt numbers
8. Categorize expenses appropriately

QUALITY STANDARDS:
- Only extract information that is clearly visible and legible
- Use null/None for missing or unclear information
- Provide confidence scores based on text clarity and completeness
- Handle multiple document pages if present
- Normalize data formats (dates as YYYY-MM-DD, times as HH:MM)

OUTPUT FORMAT:
Return a valid JSON object matching the InvoiceData schema. Include confidence_score from 0.0 to 1.0 based on extraction accuracy and text quality.

SPECIAL CONSIDERATIONS:
- For fuel receipts: Extract gallons, price per gallon, and fuel type
- For restaurants: Extract individual menu items when possible
- For retail: Extract item names, quantities, and unit prices
- Handle multi-currency transactions appropriately
- Identify recurring charges or subscriptions"""
    
    def _create_extraction_chain(self):
        """Create the LangChain extraction chain."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """Please extract all financial information from the following document content:

{document_content}

Extraction Parameters:
- Extract fuel information: {extract_fuel_info}
- Extract line items: {extract_line_items}

Document Metadata: {document_metadata}

Return the extracted information as a JSON object matching the InvoiceData schema.""")
        ])
        
        return (
            {"document_content": RunnablePassthrough(), 
             "extract_fuel_info": RunnablePassthrough(), 
             "extract_line_items": RunnablePassthrough(),
             "document_metadata": RunnablePassthrough()}
            | prompt 
            | self.llm 
            | self.output_parser
        )
    
    def _validate_result(self, result: Dict[str, Any]) -> InvoiceData:
        """Validate and convert extraction result to InvoiceData."""
        try:
            # Handle the case where result might be wrapped in additional structure
            if isinstance(result, dict) and "data" in result:
                result = result["data"]
            
            # Create InvoiceData instance with validation
            invoice_data = InvoiceData(**result)
            
            # Perform additional validation
            if invoice_data.confidence_score is None:
                invoice_data.confidence_score = 0.8  # Default confidence
            
            return invoice_data
            
        except Exception as e:
            logger.error(
                "Result validation failed",
                result=result,
                error=str(e),
                exc_info=True
            )
            raise ValidationError(f"Failed to validate extraction result: {str(e)}") from e
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return self.document_loader.get_supported_formats()