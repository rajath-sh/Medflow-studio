"""
HealthOps Studio — Structured JSON Logging

Provides a centralized logging configuration that outputs structured JSON logs.
Each log entry includes: timestamp, level, message, request_id, user_id, and extras.

WHY JSON LOGGING?
- Machine-parseable (for ELK, Datadog, CloudWatch, etc.)
- Consistent format across all services
- Easy to filter, search, and aggregate

USAGE:
    from app.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Patient created", extra={"patient_id": "123"})
"""

import logging
import json
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON lines.
    
    Sensitive fields (passwords, tokens, PII) should NEVER be passed
    to the logger — filtering is the caller's responsibility.
    """

    SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "cookie", "ssn"}

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request context if available
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "route"):
            log_entry["route"] = record.route
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "latency_ms"):
            log_entry["latency_ms"] = record.latency_ms
        if hasattr(record, "client_ip"):
            log_entry["client_ip"] = record.client_ip

        # Add any extra fields (filter sensitive ones)
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            for k, v in record.extra_data.items():
                if k.lower() not in self.SENSITIVE_KEYS:
                    log_entry[k] = v

        # Add exception info if present
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, default=str)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure the root logger to use JSON formatting.
    Call this once at application startup.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Add JSON handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(name)
