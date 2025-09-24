"""Pydantic models for Finvo AI data structures."""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, validator


class ExpenseCategory(str, Enum):
    """Predefined expense categories."""
    FOOD = "food"
    FUEL = "fuel"
    UTILITIES = "utilities"
    TRANSPORTATION = "transportation"
    GROCERIES = "groceries"
    ENTERTAINMENT = "entertainment"
    HEALTHCARE = "healthcare"
    SHOPPING = "shopping"
    SERVICES = "services"
    OTHER = "other"


class PaymentMethod(str, Enum):
    """Supported payment methods."""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    MOBILE_PAYMENT = "mobile_payment"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    OTHER = "other"


class FuelType(str, Enum):
    """Fuel types."""
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    OTHER = "other"


class ExpenseItem(BaseModel):
    """Individual expense item model."""
    
    item_name: str = Field(
        ..., 
        description="Name of the purchased item or service",
        min_length=1,
        max_length=200
    )
    quantity: Optional[float] = Field(
        default=None, 
        description="Quantity of the item",
        ge=0
    )
    unit_price: Optional[float] = Field(
        default=None, 
        description="Price per unit",
        ge=0
    )
    total_price: Optional[float] = Field(
        default=None, 
        description="Total price for this item",
        ge=0
    )
    category: Optional[ExpenseCategory] = Field(
        default=ExpenseCategory.OTHER,
        description="Category of expense"
    )


class FuelInfo(BaseModel):
    """Fuel-specific transaction information."""
    
    fuel_type: Optional[FuelType] = Field(
        default=None,
        description="Type of fuel"
    )
    gallons_filled: Optional[float] = Field(
        default=None,
        description="Amount of fuel in gallons",
        ge=0
    )
    price_per_gallon: Optional[float] = Field(
        default=None,
        description="Price per gallon",
        ge=0
    )


class InvoiceData(BaseModel):
    """Complete invoice/receipt data model."""
    
    merchant_name: Optional[str] = Field(
        default=None,
        description="Name of the merchant/business",
        max_length=200
    )
    transaction_date: Optional[str] = Field(
        default=None,
        description="Date of transaction (YYYY-MM-DD format)"
    )
    transaction_time: Optional[str] = Field(
        default=None,
        description="Time of transaction (HH:MM format)"
    )
    total_amount: Optional[float] = Field(
        default=None,
        description="Total amount of the invoice",
        ge=0
    )
    tax_amount: Optional[float] = Field(
        default=None,
        description="Tax amount if specified",
        ge=0
    )
    subtotal: Optional[float] = Field(
        default=None,
        description="Subtotal before tax",
        ge=0
    )
    items: List[ExpenseItem] = Field(
        default_factory=list,
        description="List of purchased items"
    )
    fuel_info: Optional[FuelInfo] = Field(
        default=None,
        description="Fuel-specific information if applicable"
    )
    invoice_number: Optional[str] = Field(
        default=None,
        description="Invoice or receipt number",
        max_length=100
    )
    payment_method: Optional[PaymentMethod] = Field(
        default=None,
        description="Payment method used"
    )
    currency: str = Field(
        default="USD",
        description="Currency of the transaction",
        max_length=3
    )
    confidence_score: Optional[float] = Field(
        default=None,
        description="AI confidence in extraction accuracy (0-1)",
        ge=0.0,
        le=1.0
    )
    processing_metadata: Optional[dict] = Field(
        default_factory=dict,
        description="Metadata about the processing"
    )
    
    @validator("transaction_date")
    def validate_transaction_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate date format."""
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
    
    @validator("transaction_time")
    def validate_transaction_time(cls, v: Optional[str]) -> Optional[str]:
        """Validate time format."""
        if v is None:
            return v
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError("Time must be in HH:MM format")
    
    @validator("currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        return v.upper()


class ExtractionRequest(BaseModel):
    """Request model for extraction operations."""
    
    file_name: str = Field(..., description="Name of the file to process")
    file_size: Optional[int] = Field(default=None, description="Size of the file in bytes")
    extract_fuel_info: bool = Field(default=True, description="Whether to extract fuel information")
    extract_line_items: bool = Field(default=True, description="Whether to extract individual line items")


class ExtractionResponse(BaseModel):
    """Response model for extraction operations."""
    
    status: str = Field(..., description="Processing status")
    data: Optional[InvoiceData] = Field(default=None, description="Extracted data")
    error: Optional[str] = Field(default=None, description="Error message if processing failed")
    processing_time: Optional[float] = Field(default=None, description="Processing time in seconds")
    file_info: Optional[dict] = Field(default=None, description="File metadata")