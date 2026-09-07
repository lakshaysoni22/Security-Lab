"""
LEATrace Structured Logging Configuration — Production.

Configures structured JSON logging for production deployment.
Outputs machine-parseable JSON logs for ELK/Datadog/CloudWatch ingestion.
Falls back to human-readable format in development.
"""

import os
import sys
import logging
import logging.config
from typing import Optional


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # "json" or "text"
LOG_FILE = os.getenv("LOG_FILE", "")  # Optional file output


def setup_logging(level: Optional[str] = None, fmt: Optional[str] = None):
    """
    Configures application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Default from LOG_LEVEL env.
        fmt: Format ("json" or "text"). Default from LOG_FORMAT env.
    """
    effective_level = level or LOG_LEVEL
    effective_format = fmt or LOG_FORMAT

    handlers = {}
    root_handlers = []

    if effective_format == "json":
        # JSON structured logging for production
        json_formatter = {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter" if _has_json_logger() else logging.Formatter,
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        }

        if _has_json_logger():
            json_formatter = {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(funcName)s %(lineno)d",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
                "rename_fields": {"asctime": "timestamp", "name": "logger", "levelname": "level"},
            }
        else:
            json_formatter = {
                "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            }

        handlers["console"] = {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
            "level": effective_level,
        }
        root_handlers.append("console")

    else:
        # Human-readable text format for development
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "text",
            "level": effective_level,
        }
        root_handlers.append("console")

    # Optional file handler
    if LOG_FILE:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_FILE,
            "maxBytes": 50 * 1024 * 1024,  # 50 MB
            "backupCount": 5,
            "formatter": "json" if effective_format == "json" else "text",
            "level": effective_level,
        }
        root_handlers.append("file")

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": (
                {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                }
                if _has_json_logger()
                else {
                    "format": '{"timestamp":"%(asctime)s","logger":"%(name)s","level":"%(levelname)s","message":"%(message)s"}',
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                }
            ),
            "text": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": handlers,
        "root": {
            "level": effective_level,
            "handlers": root_handlers,
        },
        "loggers": {
            "leatrace": {"level": effective_level, "propagate": True},
            "uvicorn": {"level": "WARNING", "propagate": True},
            "sqlalchemy.engine": {"level": "WARNING", "propagate": True},
            "httpx": {"level": "WARNING", "propagate": True},
        },
    }

    logging.config.dictConfig(config)

    logger = logging.getLogger("leatrace.logging")
    logger.info(f"Logging configured: level={effective_level}, format={effective_format}")


def _has_json_logger() -> bool:
    """Checks if python-json-logger is available."""
    try:
        import pythonjsonlogger
        return True
    except ImportError:
        return False


# Auto-configure on import
setup_logging()
