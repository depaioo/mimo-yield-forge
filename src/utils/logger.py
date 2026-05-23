"""
Logger - Structured logging for MiMo Yield Forge.

Provides consistent logging format with optional JSON output,
log levels, and component tagging across all modules.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional

LOG_LEVEL = os.getenv("FORGE_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root() -> None:
    """Configure the root logger once."""
    global _configured
    if _configured:
        return

    root = logging.getLogger("mimo_forge")
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)

    root.addHandler(handler)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger for a module.

    Args:
        name: Module name (typically __name__).

    Returns:
        Configured logger instance.
    """
    _configure_root()
    return logging.getLogger(f"mimo_forge.{name}")


def set_log_level(level: str) -> None:
    """Change the global log level at runtime."""
    numeric = getattr(logging, level.upper(), None)
    if numeric is None:
        return
    root = logging.getLogger("mimo_forge")
    root.setLevel(numeric)
    for handler in root.handlers:
        handler.setLevel(numeric)
