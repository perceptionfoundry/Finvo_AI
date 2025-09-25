# Finvo AI - Beyond Budgeting, Into Living.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-Powered-green.svg)](https://langchain.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-teal.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-red.svg)](https://streamlit.io)

A comprehensive AI-powered financial platform that combines invoice extraction, financial advisory services, and intelligent document processing using modern AI frameworks including LangChain and OpenAI.

## 🚀 New Features

- **🖥️ Streamlit Web Interface**: Interactive web platform with intuitive UI
- **💰 Financial Advisor Chat**: ChatGPT-style conversational AI for financial advice
- **📄 Invoice Extractor**: Advanced document processing with real-time preview
- **🔄 API Integration**: Seamless connection between Streamlit frontend and FastAPI backend
- **🎯 User-Friendly Error Handling**: Structured error display with detailed debugging information

## Core Features

- **Multi-Format Support**: PDF, JPG, PNG, GIF, BMP, TIFF (WebP supported by API, Streamlit uploader limitation)
- **Dual Interface**: Both REST API and interactive web interface
- **Structured Data Extraction**: JSON output with comprehensive financial information
- **FastAPI REST API**: Production-ready web API with comprehensive endpoints
- **LangChain Integration**: Professional AI pipeline with document processing
- **Real-time Processing**: Live document preview and extraction status
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

### 🖥️ Streamlit Web Interface (Recommended)

**Start both FastAPI backend and Streamlit frontend:**

```bash
# Terminal 1: Start FastAPI backend
uv run python app.py

# Terminal 2: Start Streamlit frontend
python run_streamlit.py
# OR
uv run streamlit run src/finvo_ai_streamlit/app.py
```

**Access the applications:**
- **Streamlit Interface**: http://localhost:8501 (Main UI)
- **FastAPI Backend**: http://localhost:8000 (API)
- **API Documentation**: http://localhost:8000/docs (Swagger UI)

### 🎯 Streamlit Features

#### 📄 Invoice Extractor
- **File Upload**: Drag & drop PDF, JPG, PNG, GIF, BMP, TIFF files
- **Real-time Preview**: See uploaded documents instantly
- **API Status Monitor**: Live connection status with refresh option
- **Structured Results**: Clean JSON display with processing time
- **Error Handling**: User-friendly error messages with details

#### 💰 Financial Advisor
- **ChatGPT-style Interface**: Conversational AI for financial advice
- **Personalized Responses**: Context-aware financial guidance
- **Topic Categories**: Budget, savings, investment, tax advice
- **Chat History**: Persistent conversation within session
- **Clear Chat Option**: Reset conversation anytime

### ⚡ Quick Start API Mode

```bash
# Development mode
uv run python app.py

# Production mode with auto-reload
uv run uvicorn app:app --reload

# Production deployment
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

## 🔌 API Usage Guide

> **Note**: The Streamlit interface is primarily designed for testing and demonstrating the developed APIs. For production integration, use the FastAPI endpoints directly.

### 📋 Available API Endpoints

#### 1. **Health Check**
```bash
GET /health
curl http://localhost:8000/health
```

#### 2. **Service Information**
```bash
GET /
curl http://localhost:8000/
```

#### 3. **Get Supported File Formats**
```bash
GET /api/v1/supported-formats
curl http://localhost:8000/api/v1/supported-formats
```

#### 4. **Get Data Schemas**
```bash
GET /api/v1/schema
curl http://localhost:8000/api/v1/schema
```

#### 5. **Service Statistics**
```bash
GET /api/v1/stats
curl http://localhost:8000/api/v1/stats
```

### 💼 Main Invoice Extraction API

#### **File Upload Extraction**
```bash
POST /api/v1/extract/upload

# Basic usage
curl -X POST "http://localhost:8000/api/v1/extract/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@invoice.pdf"

# With extraction options
curl -X POST "http://localhost:8000/api/v1/extract/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@receipt.jpg" \
     -F "extract_fuel_info=true" \
     -F "extract_line_items=true"
```

#### **Parameters:**
- `file` (required): The invoice/receipt file to process
- `extract_fuel_info` (optional): Extract fuel-related information (default: true)
- `extract_line_items` (optional): Extract individual line items (default: true)

#### **Supported File Types:**
- **PDF**: `.pdf`
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff`

### 📱 Using Different Programming Languages

#### **Python with requests**
```python
import requests

url = "http://localhost:8000/api/v1/extract/upload"
files = {"file": open("invoice.pdf", "rb")}
data = {
    "extract_fuel_info": "true",
    "extract_line_items": "true"
}

response = requests.post(url, files=files, data=data)
result = response.json()
print(result)
```

#### **Python with httpx (async)**
```python
import httpx
import asyncio

async def extract_invoice():
    async with httpx.AsyncClient() as client:
        files = {"file": ("invoice.pdf", open("invoice.pdf", "rb"))}
        data = {"extract_fuel_info": "true", "extract_line_items": "true"}
        
        response = await client.post(
            "http://localhost:8000/api/v1/extract/upload",
            files=files,
            data=data
        )
        return response.json()

result = asyncio.run(extract_invoice())
```

#### **JavaScript/Node.js**
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('file', fs.createReadStream('invoice.pdf'));
form.append('extract_fuel_info', 'true');
form.append('extract_line_items', 'true');

axios.post('http://localhost:8000/api/v1/extract/upload', form, {
    headers: form.getHeaders()
})
.then(response => console.log(response.data))
.catch(error => console.error(error));
```

### 🔍 API Testing Tools

#### **Swagger UI (Interactive Documentation)**
- **URL**: http://localhost:8000/docs
- **Features**: Test all endpoints directly in browser
- **Authentication**: Not required for current endpoints

#### **ReDoc (Alternative Documentation)**
- **URL**: http://localhost:8000/redoc
- **Features**: Clean, readable API documentation

#### **Postman Collection**
```bash
# Import this curl command into Postman
curl -X POST "http://localhost:8000/api/v1/extract/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@invoice.pdf" \
     -F "extract_fuel_info=true" \
     -F "extract_line_items=true"
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
│   ├── finvo_ai/
│   │   ├── agents/           # LangChain agents for extraction
│   │   ├── api/              # FastAPI routes and endpoints
│   │   ├── core/             # Core utilities and exceptions
│   │   ├── models/           # Pydantic schemas and data models
│   │   ├── services/         # Business logic and processing
│   │   └── utils/            # Logging and utility functions
│   └── finvo_ai_streamlit/   # 🆕 Streamlit web interface
│       └── app.py            #     Main Streamlit application
├── config/                   # Configuration management
├── tests/                    # Test suite
├── app.py                   # FastAPI application entry point
├── run_streamlit.py         # 🆕 Streamlit launcher script
├── logo.png                 # 🆕 Application logo
├── pyproject.toml           # Project configuration
└── README.md
```

## 🆕 New Components

### Streamlit Interface (`src/finvo_ai_streamlit/`)
- **`app.py`**: Main Streamlit application with dual-mode interface
- **Invoice Extractor**: File upload, preview, and API-based processing
- **Financial Advisor**: ChatGPT-style conversational interface
- **API Integration**: Real-time connection monitoring and error handling

### Launch Scripts
- **`run_streamlit.py`**: Easy launcher for Streamlit interface
- **`logo.png`**: Centered application logo for web interface

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

### Backend (FastAPI)
- **LangChain**: LLM framework for AI applications
- **OpenAI**: GPT models integration
- **FastAPI**: Modern web framework for APIs
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for FastAPI
- **python-dotenv**: Environment variable management

### Frontend (Streamlit)
- **Streamlit**: Interactive web interface framework
- **httpx**: HTTP client for API communication
- **PIL/Pillow**: Image processing and display

### Document Processing
- **pytesseract**: OCR text extraction
- **UnstructuredImageLoader**: Advanced document parsing
- **PyPDFLoader**: PDF document processing

## 🔧 Recent Updates

### Version 2.0 - Streamlit Integration
- ✅ Added complete Streamlit web interface
- ✅ Implemented ChatGPT-style Financial Advisor
- ✅ Enhanced error handling with structured display
- ✅ Added real-time API connection monitoring
- ✅ Fixed import path issues and deprecation warnings
- ✅ Updated document loader for better image strategy
- ✅ Added support for multiple image formats in UI

### Technical Improvements
- ✅ Migrated from `use_column_width` to `width` parameter
- ✅ Enhanced error messages with expandable details
- ✅ Improved API-Streamlit integration architecture
- ✅ Added comprehensive file format support documentation
- ✅ Implemented robust fallback strategies for document processing

## License

MIT License

---

**Built with LangChain, FastAPI, and OpenAI**