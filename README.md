# Finvo AI - Beyond Budgeting, Into Living.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-Powered-green.svg)](https://langchain.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-teal.svg)](https://fastapi.tiangolo.com)

A professional AI system for extracting financial data from invoices, receipts, and financial documents using modern AI frameworks including LangChain and OpenAI.

## Features

- **Multi-Format Support**: PDF, JPG, PNG, GIF, BMP, WEBP, TIFF
- **Structured Data Extraction**: JSON output with comprehensive financial information
- **FastAPI REST API**: Production-ready web API with comprehensive endpoints
- **LangChain Integration**: Professional AI pipeline with document processing
- **Type Safety**: Full Pydantic validation and type hints
- **Professional Architecture**: Modular design with error handling and logging

## Prerequisites

- Python 3.12+
- OpenAI API key
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd Finvo_AI
   uv sync
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Usage

### Start the Application

```bash
# Development mode
uv run python app.py

# Production mode with auto-reload
uv run uvicorn app:app --reload

# Production deployment
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

### API Endpoints

#### Upload File Extraction
```bash
curl -X POST "http://localhost:8000/api/v1/extract/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@invoice.pdf" \
     -F "extract_fuel_info=true" \
     -F "extract_line_items=true"
```

#### Base64 Image Extraction
```bash
curl -X POST "http://localhost:8000/api/v1/extract/base64" \
     -H "Content-Type: application/json" \
     -d '{
       "image_data": "base64_encoded_image",
       "filename": "receipt.jpg",
       "extract_fuel_info": true,
       "extract_line_items": true
     }'
```

### Response Format

```json
{
  "status": "success",
  "data": {
    "merchant_name": "Shell Gas Station",
    "transaction_date": "2024-01-15",
    "transaction_time": "14:30",
    "total_amount": 45.67,
    "tax_amount": 3.42,
    "subtotal": 42.25,
    "items": [
      {
        "item_name": "Regular Gasoline",
        "quantity": 12.5,
        "unit_price": 3.38,
        "total_price": 42.25,
        "category": "fuel"
      }
    ],
    "fuel_info": {
      "fuel_type": "gasoline",
      "gallons_filled": 12.5,
      "price_per_gallon": 3.38
    },
    "invoice_number": "12345678",
    "payment_method": "credit_card",
    "currency": "USD",
    "confidence_score": 0.95
  },
  "processing_time": 2.34,
  "file_info": {
    "filename": "receipt.jpg",
    "size": 1024000,
    "format": ".jpg"
  }
}
```

## Project Structure

```
Finvo_AI/
├── src/
│   └── finvo_ai/
│       ├── agents/       # LangChain agents for extraction
│       ├── api/          # FastAPI routes and endpoints
│       ├── core/         # Core utilities and exceptions
│       ├── models/       # Pydantic schemas and data models
│       ├── services/     # Business logic and processing
│       └── utils/        # Logging and utility functions
├── config/               # Configuration management
├── tests/                # Test suite
├── app.py               # Main application entry point
├── pyproject.toml       # Project configuration
└── README.md
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-your-api-key-here

# Optional (with defaults)
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.1
MAX_TOKENS=1500
MAX_FILE_SIZE_MB=10
LOG_LEVEL=INFO
ENVIRONMENT=production
DEBUG=false
```

## Development

### Code Quality

```bash
# Format code
uv run black .

# Sort imports
uv run isort .

# Lint code
uv run flake8

# Type checking
uv run mypy src/
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/finvo_ai
```

## Core Dependencies

- **LangChain**: LLM framework for AI applications
- **OpenAI**: GPT models integration
- **FastAPI**: Modern web framework for APIs
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for FastAPI
- **python-dotenv**: Environment variable management

## License

MIT License

---

**Built with LangChain, FastAPI, and OpenAI**