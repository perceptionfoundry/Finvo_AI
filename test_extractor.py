"""
Test script for the invoice extractor module.
Run this after setting your OPENAI_API_KEY in .env file.
"""
import asyncio
from invoice_extractor import InvoiceExtractor

async def test_extractor():
    try:
        extractor = InvoiceExtractor()
        print("✅ InvoiceExtractor initialized successfully")
        
        # Test JSON schema
        from invoice_extractor import InvoiceData
        schema = InvoiceData.model_json_schema()
        print("✅ JSON schema generated successfully")
        print(f"Schema has {len(schema.get('properties', {}))} main fields")
        
        print("\n📋 Available API endpoints:")
        print("- POST /extract/upload - Upload invoice file")
        print("- POST /extract/base64 - Send base64 encoded image")
        print("- GET /schema - Get JSON schema")
        print("- GET /health - Health check")
        
        print("\n🚀 Ready to process invoices!")
        print("Start the server with: uv run uvicorn app:app --reload")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(test_extractor())