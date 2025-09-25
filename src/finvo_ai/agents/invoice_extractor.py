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

Your task is to analyze the provided document content and extract ALL visible information with maximum accuracy, focusing on complete financial data for personal expense tracking.

CRITICAL REQUIREMENTS (IN ORDER OF IMPORTANCE):

1. **TRANSACTION FINANCIALS (HIGHEST PRIORITY - MANDATORY)**:
   - **TOTAL AMOUNT**: Find "TOTAL 8.18" patterns → extract 8.18 as total_amount
   - **TAX AMOUNT**: Find "TAX 10.00% .074" patterns → extract 0.074 as tax_amount
   - **SUBTOTAL**: Find "SUBTOTAL 7.44" patterns → extract 7.44 as subtotal  
   - **DATE**: Find transaction/purchase date in ANY format
   - **TIME**: Find transaction time (HH:MM or HH:MM:SS format)
   
   **EXTRACTION IS MANDATORY - DO NOT LEAVE NULL IF NUMBERS ARE VISIBLE**
   
2. **INDIVIDUAL ITEM PRICES (CRITICAL)**:
   - Extract item name AND its corresponding price
   - Look for patterns like "HAND TOWEL 2.97", "Item Name $5.99", "Product 1x $10.00"
   - Find prices next to, above, or below item names
   - Include unit prices, quantities, and total prices per item
   - Examples: "HAND TOWEL" with price "2.97", "GATORADE" with price "1.50"
   
3. **LINE ITEMS EXTRACTION**: 
   - Extract EVERY single item/product/service listed
   - Include complete pricing information for each item
   - Look for itemized sections, product lists, line-by-line breakdowns
   
4. **MERCHANT & TRANSACTION INFO**:
   - Extract business name, location, addresses, phone numbers
   - Extract invoice/receipt/transaction numbers
   
5. **PAYMENT INFORMATION**:
   - Identify payment method (Interac, Visa, Cash, etc.)
   - Extract last 4 digits of card if visible

PRICE EXTRACTION PATTERNS:
- **Adjacent Numbers**: "HAND TOWEL 2.97", "GATORADE 1.50"
- **With Currency**: "ITEM $5.99", "Product CAD 10.00"
- **Quantity Patterns**: "2x ITEM @ 3.50", "ITEM 1x 7.25"
- **Columnar Layout**: Item name in one column, price in another
- **Multiple Prices**: Unit price AND total price per item

MANDATORY FINANCIAL EXTRACTION PATTERNS:
- **SUBTOTAL**: "SUBTOTAL 7.44", "Sub Total: 12.50", "Subtotal $15.99"
- **TAX**: "TAX 10.00% .074", "GST: 1.25", "Tax Amount: 2.35", "HST 13%: 3.45"  
- **TOTAL**: "TOTAL 8.18", "Total: $15.47", "Amount Due: $45.99", "AMOUNT: 23.50"
- **ITEM PRICES**: "PEANUTS 2.46", "TOMATOES 4.98", "ITEM NAME price_number"

CRITICAL EXTRACTION RULES:
- **SCAN FOR NUMBERS**: Look for ANY decimal number that could be a price
- **MATCH PATTERNS**: "SUBTOTAL 7.44" means subtotal = 7.44, "TOTAL 8.18" means total_amount = 8.18
- **ITEM-PRICE ASSOCIATION**: "PEANUTS 2.46" means PEANUTS has unit_price = 2.46
- **TAX PARSING**: "TAX 10.00% .074" means tax_amount = 0.074 (extract the final number)
- **NEVER IGNORE FINANCIAL NUMBERS**: Every visible price/amount MUST be extracted

SPECIFIC WALMART-STYLE PATTERNS:
- Look for "SUBTOTAL [amount]" → extract the amount
- Look for "TAX [percentage] [amount]" → extract the final amount
- Look for "TOTAL [amount]" → extract the amount
- Look for "[ITEM NAME] [price]" → extract both name and price

SPECIAL HANDLING:
- **Retail receipts**: Extract every item with its individual price
- **Restaurant bills**: Get each menu item price, tax, and total
- **Fuel receipts**: Gallons, price per gallon, total fuel cost
- **Grocery receipts**: All food items with individual and total prices

Return a valid JSON object with the "items" array populated with ALL extracted products/services.

EXACT JSON SCHEMA FOR ITEMS:
Each item in the "items" array must have these exact field names:
- "item_name" (required): Product/service name
- "quantity": Number of items (can be null)
- "unit_price": Price per unit (can be null) 
- "total_price": Total price for this item (can be null)
- "category": Expense category from: food, fuel, utilities, transportation, groceries, entertainment, healthcare, shopping, services, other

VALID CATEGORIES:
- "food": Restaurant meals, snacks, beverages, prepared food
- "groceries": Raw ingredients, supermarket items, household food
- "shopping": Clothing, electronics, furniture, general retail
- "fuel": Gasoline, diesel, car fuel
- "transportation": Transit, parking, car services
- "utilities": Electricity, water, internet, phone
- "healthcare": Medical, pharmacy, personal care
- "entertainment": Movies, games, recreation
- "services": Professional services, repairs, maintenance
- "other": Miscellaneous items

EXAMPLE ITEM FORMAT:
{{
  "item_name": "HAND TOWEL",
  "quantity": 1,
  "unit_price": 5.99,
  "total_price": 5.99,
  "category": "shopping"
}}

USE "item_name" NOT "name" - This is critical for validation."""
    
    def _create_extraction_chain(self):
        """Create the LangChain extraction chain."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """EXTRACT COMPLETE FINANCIAL DATA FROM THIS RECEIPT/INVOICE:

{document_content}

CRITICAL FINANCIAL EXTRACTION PRIORITIES:

1. **MUST FIND THESE FINANCIAL VALUES** (DO NOT leave as null if visible):
   - **transaction_date**: Any date on the receipt (purchase date, transaction date)
   - **transaction_time**: Time of purchase/transaction  
   - **total_amount**: Final total amount paid
   - **tax_amount**: Tax/GST/HST amount
   - **subtotal**: Amount before tax

2. **ITEM PRICING IS CRITICAL**: 
   - For each item, find its price (e.g., "HAND TOWEL 2.97" means HAND TOWEL costs 2.97)
   - Look for prices immediately after item names, in columns, or nearby
   - Extract unit_price and total_price for each item when visible

3. **EXTRACTION PARAMETERS**: 
   - Extract fuel information: {extract_fuel_info}
   - Extract line items: {extract_line_items}
4. **DOCUMENT METADATA**: {document_metadata}

EXACT PATTERNS YOU MUST EXTRACT:
- "SUBTOTAL 7.44" → subtotal: 7.44
- "TAX 10.00% .074" → tax_amount: 0.074 (use the final number after %)
- "TOTAL 8.18" → total_amount: 8.18
- "PEANUTS 2.46" → item "PEANUTS" with unit_price: 2.46
- "TOMATOES 4.98" → item "TOMATOES" with unit_price: 4.98

WALMART-STYLE RECEIPT PATTERNS:
- Look for lines like "ITEM_NAME [space] PRICE_NUMBER"
- Look for "SUBTOTAL [amount]", "TAX [percentage] [final_amount]", "TOTAL [amount]"
- Extract the final number in tax lines (ignore percentage, get the actual tax amount)
- Every item should have its price - look right after the item name

**ZERO TOLERANCE FOR NULL FINANCIAL FIELDS** - If you see numbers that look like prices, extract them!

CRITICAL FIELD MAPPING:
Each item must use "item_name" (not "name") and follow this exact structure:
{{
  "item_name": "PRODUCT NAME HERE",
  "quantity": number_or_null,
  "unit_price": number_or_null,
  "total_price": number_or_null,
  "category": "category_or_null"
}}

Return the complete extracted information as a JSON object matching the InvoiceData schema with populated "items" array.""")
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