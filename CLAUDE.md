# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Finvo_AI**, an AI module project built with Python 3.12+ using modern AI frameworks. The project is designed to develop AI capabilities using LangChain, OpenAI, and FastAPI.

## Package Management

This project uses **uv** as the package manager. All dependency management should be done through uv commands:

```bash
# Install dependencies
uv sync

# Add new dependencies
uv add <package-name>

# Add development dependencies
uv add --dev <package-name>

# Run Python scripts
uv run python main.py

# Run with specific Python module
uv run python -m <module>
```

## Development Commands

### Running the Application
```bash
# Run the main application
uv run python app.py

# Run FastAPI server (when implemented)
uv run uvicorn app:app --reload
```

### Environment Setup
```bash
# Activate virtual environment (if needed)
source .venv/bin/activate

# Check Python version
python --version
```

## Core Dependencies

The project is built around these key frameworks:
- **LangChain**: LLM framework for building AI applications
- **OpenAI**: OpenAI API client for GPT models
- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for FastAPI
- **Pydantic**: Data validation and serialization
- **python-dotenv**: Environment variable management

## Architecture Notes

- This is a fresh AI project with minimal boilerplate (currently just a hello world in `main.py`)
- The project is configured for AI module development with focus on LangChain and OpenAI integration
- FastAPI is included for building API endpoints around AI functionality
- Use environment variables for API keys and configuration (via python-dotenv)

## File Structure

- `app.py`: Main application entry point (currently minimal)
- `pyproject.toml`: Project configuration and dependencies
- `uv.lock`: Locked dependency versions
- `.python-version`: Python version specification