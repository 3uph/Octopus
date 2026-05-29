"""Central logger with automatic secret redaction."""
import logging
import sys

from .redactor import redact


class _RedactingFormatter(logging.Formatter):
    """Formatter that redacts secrets from log messages."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        return redact(msg)


def _build_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        _RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    return handler


def get_logger(name: str) -> logging.Logger:
    """Return a logger with redacting formatter attached."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addHandler(_build_handler())
    return logger


def configure_root_logger(level: str = "INFO") -> None:
    """Configure root logger for the application."""
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(_build_handler())
    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
