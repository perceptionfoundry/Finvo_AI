"""Professional logging setup for Finvo AI."""

import sys
from pathlib import Path
from typing import Optional

import structlog
from structlog.stdlib import LoggerFactory

from config.settings import settings


def configure_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """Configure structured logging for the application."""
    
    log_level = log_level or settings.log_level
    log_format = log_format or settings.log_format
    log_file = log_file or settings.log_file
    
    # Configure timestamper
    timestamper = structlog.processors.TimeStamper(fmt="ISO")
    
    # Configure shared processors
    shared_processors = [
        structlog.stdlib.filter_by_level,
        timestamper,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Configure output format
    if log_format == "json":
        processor = structlog.processors.JSONRenderer()
    else:
        processor = structlog.dev.ConsoleRenderer(colors=True)
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure stdlib logging
    import logging.config
    
    handlers = {
        "default": {
            "level": log_level,
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "processor",
        }
    }
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "level": log_level,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_path),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "processor",
        }
    
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "processor": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": processor,
            },
        },
        "handlers": handlers,
        "loggers": {
            "": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": True,
            },
            "uvicorn.access": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
        },
    })


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


# Configure logging on module import
configure_logging()