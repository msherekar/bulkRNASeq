"""Logging setup module."""

import logging
from rich.logging import RichHandler

def setup_logging():
    """Set up rich logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    return logging.getLogger("bulkrnaseq")
