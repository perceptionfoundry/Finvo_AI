import base64
import os
from typing import Optional, Union, Dict, Any, List
from pathlib import Path
import json
from io import BytesIO

from PIL import Image
import PyPDF2
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class ExpenseItem(BaseModel):
    item_name: str = Field(description="Name of the purchased item or service")
    quantity: Optional[float] = Field(default=None, description="Quantity of the item")
    unit_price: Optional[float] = Field(default=None, description="Price per unit")
    total_price: Optional[float] = Field(default=None, description="Total price for this item")
    category: Optional[str] = Field(default=None, description="Category of expense (food, fuel, utilities, etc.)")

class FuelInfo(BaseModel):
    fuel_type: Optional[str] = Field(default=None, description="Type of fuel (gasoline, diesel, etc.)")
    gallons_filled: Optional[float] = Field(default=None, description="Amount of fuel in gallons")
    price_per_gallon: Optional[float] = Field(default=None, description="Price per gallon")

class InvoiceData(BaseModel):
    merchant_name: Optional[str] = Field(default=None, description="Name of the merchant/business")
    transaction_date: Optional[str] = Field(default=None, description="Date of transaction (YYYY-MM-DD format)")
    transaction_time: Optional[str] = Field(default=None, description="Time of transaction")
    total_amount: Optional[float] = Field(default=None, description="Total amount of the invoice")
    tax_amount: Optional[float] = Field(default=None, description="Tax amount if specified")
    subtotal: Optional[float] = Field(default=None, description="Subtotal before tax")
    items: List[ExpenseItem] = Field(default_factory=list, description="List of purchased items")
    fuel_info: Optional[FuelInfo] = Field(default=None, description="Fuel-specific information if applicable")
    invoice_number: Optional[str] = Field(default=None, description="Invoice or receipt number")
    payment_method: Optional[str] = Field(default=None, description="Payment method used")
    currency: Optional[str] = Field(default="USD", description="Currency of the transaction")
    confidence_score: Optional[float] = Field(default=None, description="AI confidence in extraction accuracy (0-1)")

class InvoiceExtractor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if not self.client.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
    
    def encode_image_to_base64(self, image_path_or_bytes: Union[str, bytes, BytesIO]) -> str:
        if isinstance(image_path_or_bytes, str):
            with open(image_path_or_bytes, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        elif isinstance(image_path_or_bytes, bytes):
            return base64.b64encode(image_path_or_bytes).decode('utf-8')
        elif isinstance(image_path_or_bytes, BytesIO):
            return base64.b64encode(image_path_or_bytes.getvalue()).decode('utf-8')
        else:
            raise ValueError("Unsupported image format")
    
    def pdf_to_images(self, pdf_path: str) -> List[bytes]:
        images = []
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    if '/XObject' in page['/Resources']:
                        xObject = page['/Resources']['/XObject'].get_object()
                        for obj in xObject:
                            if xObject[obj]['/Subtype'] == '/Image':
                                size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
                                data = xObject[obj].get_data()
                                if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                                    mode = "RGB"
                                else:
                                    mode = "P"
                                img = Image.frombytes(mode, size, data)
                                img_bytes = BytesIO()
                                img.save(img_bytes, format='PNG')
                                images.append(img_bytes.getvalue())
        except Exception as e:
            print(f"Error extracting images from PDF: {e}")
        return images
    
    def extract_from_image(self, image_data: Union[str, bytes, BytesIO]) -> Dict[str, Any]:
        base64_image = self.encode_image_to_base64(image_data)
        
        system_prompt = """You are an expert at extracting financial information from invoices, receipts, and bills. 
        Analyze the image and extract all relevant financial data including:
        - Merchant/business information
        - Date and time of transaction  
        - Individual items with quantities and prices
        - Total amounts, taxes, subtotals
        - Payment methods
        - Special attention to fuel/gas receipts (gallons, price per gallon, fuel type)
        - Invoice/receipt numbers
        
        Return the information in a structured JSON format that matches this schema:
        {
            "merchant_name": "string",
            "transaction_date": "YYYY-MM-DD",
            "transaction_time": "HH:MM",
            "total_amount": number,
            "tax_amount": number,
            "subtotal": number,
            "items": [
                {
                    "item_name": "string",
                    "quantity": number,
                    "unit_price": number,
                    "total_price": number,
                    "category": "string"
                }
            ],
            "fuel_info": {
                "fuel_type": "string",
                "gallons_filled": number,
                "price_per_gallon": number
            },
            "invoice_number": "string",
            "payment_method": "string",
            "currency": "USD",
            "confidence_score": number
        }
        
        Only include fields that are clearly visible in the image. Use null for missing information.
        For confidence_score, rate your confidence in the extraction accuracy from 0.0 to 1.0."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please extract all financial information from this invoice/receipt image."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            try:
                extracted_data = json.loads(content)
                return extracted_data
            except json.JSONDecodeError:
                content_start = content.find('{')
                content_end = content.rfind('}') + 1
                if content_start != -1 and content_end != 0:
                    json_content = content[content_start:content_end]
                    return json.loads(json_content)
                else:
                    raise ValueError("Could not parse JSON from OpenAI response")
                    
        except Exception as e:
            return {
                "error": f"Failed to extract data: {str(e)}",
                "confidence_score": 0.0
            }
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        file_path = Path(file_path)
        if not file_path.exists():
            return {"error": "File not found", "confidence_score": 0.0}
        
        file_extension = file_path.suffix.lower()
        
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return self.extract_from_image(str(file_path))
        
        elif file_extension == '.pdf':
            images = self.pdf_to_images(str(file_path))
            if not images:
                return {"error": "No images found in PDF", "confidence_score": 0.0}
            
            all_extractions = []
            for i, image_bytes in enumerate(images):
                extraction = self.extract_from_image(image_bytes)
                if "error" not in extraction:
                    all_extractions.append(extraction)
            
            if not all_extractions:
                return {"error": "Failed to extract data from PDF pages", "confidence_score": 0.0}
            
            return all_extractions[0] if len(all_extractions) == 1 else {
                "multiple_pages": all_extractions,
                "confidence_score": sum(e.get("confidence_score", 0) for e in all_extractions) / len(all_extractions)
            }
        
        else:
            return {"error": f"Unsupported file format: {file_extension}", "confidence_score": 0.0}
    
    def validate_extraction(self, data: Dict[str, Any]) -> InvoiceData:
        try:
            return InvoiceData(**data)
        except Exception as e:
            return InvoiceData(confidence_score=0.0)