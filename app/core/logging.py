"""Logging configuration for the application."""

import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application logging.

    Sets up structured logging to stdout with consistent formatting.
    Configures the "app" logger hierarchy for all application modules.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Defaults to INFO.

    Note:
        This function should be called once at application startup,
        before any loggers are used. Multiple calls are safe due to
        handler existence check.
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Get application logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(numeric_level)
    app_logger.propagate = False

    # Protect against duplicate handler registration
    if not app_logger.handlers:
        # Create formatter with timestamp, level, logger name, and message
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Create console handler for stdout (Docker-friendly)
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)

        app_logger.addHandler(console_handler)
