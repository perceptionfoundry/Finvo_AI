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
    INTERAC = "interac"
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
    
    @validator("category", pre=True)
    def validate_category(cls, v) -> Optional[ExpenseCategory]:
        """Validate and map category to valid enum values."""
        if v is None:
            return ExpenseCategory.OTHER
        
        if isinstance(v, ExpenseCategory):
            return v
            
        # Convert to lowercase string for mapping
        v_lower = str(v).lower().strip()
        
        # Category mappings for common variations
        category_mappings = {
            # Beverages
            "beverage": ExpenseCategory.FOOD,
            "beverages": ExpenseCategory.FOOD,
            "drinks": ExpenseCategory.FOOD,
            "drink": ExpenseCategory.FOOD,
            
            # Clothing
            "clothing": ExpenseCategory.SHOPPING,
            "clothes": ExpenseCategory.SHOPPING,
            "apparel": ExpenseCategory.SHOPPING,
            "fashion": ExpenseCategory.SHOPPING,
            "accessories": ExpenseCategory.SHOPPING,
            
            # Stationery/Office
            "stationery": ExpenseCategory.SHOPPING,
            "office": ExpenseCategory.SHOPPING,
            "office supplies": ExpenseCategory.SHOPPING,
            "supplies": ExpenseCategory.SHOPPING,
            
            # Electronics
            "electronics": ExpenseCategory.SHOPPING,
            "tech": ExpenseCategory.SHOPPING,
            "technology": ExpenseCategory.SHOPPING,
            
            # Personal care
            "personal care": ExpenseCategory.HEALTHCARE,
            "hygiene": ExpenseCategory.HEALTHCARE,
            "beauty": ExpenseCategory.SHOPPING,
            "cosmetics": ExpenseCategory.SHOPPING,
            
            # Home/Household
            "household": ExpenseCategory.SHOPPING,
            "home": ExpenseCategory.SHOPPING,
            "furniture": ExpenseCategory.SHOPPING,
            "appliances": ExpenseCategory.SHOPPING,
            
            # Restaurant/Dining
            "restaurant": ExpenseCategory.FOOD,
            "dining": ExpenseCategory.FOOD,
            "takeout": ExpenseCategory.FOOD,
            "fast food": ExpenseCategory.FOOD,
        }
        
        # Check direct mappings first
        if v_lower in category_mappings:
            return category_mappings[v_lower]
        
        # Try to match enum values directly
        for category in ExpenseCategory:
            if v_lower == category.value.lower():
                return category
        
        # If no match found, return OTHER
        return ExpenseCategory.OTHER


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
        """Validate date format and normalize to YYYY-MM-DD."""
        if v is None:
            return v
        
        # Try different date formats and normalize to YYYY-MM-DD
        date_formats = [
            "%Y-%m-%d",      # 2023-12-25
            "%m/%d/%Y",      # 12/25/2023
            "%d/%m/%Y",      # 25/12/2023
            "%m-%d-%Y",      # 12-25-2023
            "%d-%m-%Y",      # 25-12-2023
            "%Y/%m/%d",      # 2023/12/25
            "%m/%d/%y",      # 12/25/23
            "%d/%m/%y",      # 25/12/23
            "%b %d, %Y",     # Dec 25, 2023
            "%B %d, %Y",     # December 25, 2023
            "%d %b %Y",      # 25 Dec 2023
            "%d %B %Y",      # 25 December 2023
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(v, fmt)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        raise ValueError(f"Date format not recognized. Got: {v}. Expected common date formats")
    
    @validator("transaction_time")
    def validate_transaction_time(cls, v: Optional[str]) -> Optional[str]:
        """Validate time format and normalize to HH:MM."""
        if v is None:
            return v
        
        # Clean and prepare the time string
        v_clean = str(v).strip()
        
        # Try different time formats and normalize to HH:MM
        time_formats = [
            "%H:%M:%S",          # 13:30:45
            "%H:%M",             # 13:30
            "%I:%M:%S %p",       # 1:30:45 PM
            "%I:%M %p",          # 1:30 PM
            "%I:%M:%S%p",        # 1:30:45PM (no space)
            "%I:%M%p",           # 1:30PM (no space)
            "%H:%M:%S %p",       # 13:30:45 PM (sometimes mixed)
            "%H:%M %p",          # 13:30 PM (sometimes mixed)
        ]
        
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(v_clean, fmt)
                return parsed_time.strftime("%H:%M")
            except ValueError:
                continue
        
        # Try to handle edge cases by adding space before AM/PM
        if any(suffix in v_clean.upper() for suffix in ['AM', 'PM']):
            # Add space before AM/PM if missing: "05:52PM" -> "05:52 PM"
            import re
            v_with_space = re.sub(r'(\d+):(\d+)(AM|PM)', r'\1:\2 \3', v_clean, flags=re.IGNORECASE)
            if v_with_space != v_clean:
                for fmt in ["%I:%M %p", "%I:%M:%S %p"]:
                    try:
                        parsed_time = datetime.strptime(v_with_space, fmt)
                        return parsed_time.strftime("%H:%M")
                    except ValueError:
                        continue
        
        raise ValueError(f"Time format not recognized. Got: {v}. Supported: HH:MM, HH:MM:SS, 12-hour with/without space")
    
    @validator("payment_method", pre=True)
    def validate_payment_method(cls, v) -> Optional[PaymentMethod]:
        """Validate payment method and handle case-insensitive matching."""
        if v is None:
            return v
        
        if isinstance(v, PaymentMethod):
            return v
            
        # Convert to lowercase string for matching
        v_lower = str(v).lower().strip()
        
        # Direct mapping for common variations
        payment_mappings = {
            "interac": PaymentMethod.INTERAC,
            "visa": PaymentMethod.CREDIT_CARD,
            "mastercard": PaymentMethod.CREDIT_CARD,
            "amex": PaymentMethod.CREDIT_CARD,
            "american express": PaymentMethod.CREDIT_CARD,
            "discover": PaymentMethod.CREDIT_CARD,
            "debit": PaymentMethod.DEBIT_CARD,
            "credit": PaymentMethod.CREDIT_CARD,
            "e-transfer": PaymentMethod.BANK_TRANSFER,
            "etransfer": PaymentMethod.BANK_TRANSFER,
            "wire": PaymentMethod.BANK_TRANSFER,
            "apple pay": PaymentMethod.MOBILE_PAYMENT,
            "google pay": PaymentMethod.MOBILE_PAYMENT,
            "paypal": PaymentMethod.MOBILE_PAYMENT,
            "venmo": PaymentMethod.MOBILE_PAYMENT,
            "cash": PaymentMethod.CASH,
            "cheque": PaymentMethod.CHECK,
            "check": PaymentMethod.CHECK,
        }
        
        # Check direct mappings first
        if v_lower in payment_mappings:
            return payment_mappings[v_lower]
        
        # Try to match enum values
        for payment_method in PaymentMethod:
            if v_lower == payment_method.value.lower():
                return payment_method
        
        # If no match found, return OTHER
        return PaymentMethod.OTHER
    
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