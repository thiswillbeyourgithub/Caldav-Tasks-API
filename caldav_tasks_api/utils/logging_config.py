"""
Logging configuration for caldav-tasks-api.

Sets up two loguru sinks:
- Console (stderr): defaults to INFO level, overridable via CALDAV_TASKS_API_LOG_LEVEL
  env var or the --debug CLI flag (which sets it to DEBUG).
- Log file: always at DEBUG level, rotated at 10 MB, retained for 10 days.

The default loguru handler is removed on import to avoid duplicate output.
"""

import os
import sys
from pathlib import Path

from loguru import logger
from platformdirs import user_log_dir

# Track the console handler ID so we can swap it later (e.g. when --debug is passed)
_console_handler_id: int | None = None


def setup_logging() -> None:
    """Configure loguru loggers for console and file output.

    Called automatically on module import. The console level is determined by
    the CALDAV_TASKS_API_LOG_LEVEL env var (default: INFO). The file logger
    always records at DEBUG level.
    """
    global _console_handler_id

    # Remove loguru's default stderr handler (DEBUG level) to avoid duplicates
    logger.remove()

    # --- Console handler ---
    console_log_level = os.environ.get("CALDAV_TASKS_API_LOG_LEVEL", "INFO").upper()

    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> "
        "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
        "- <level>{message}</level>"
    )

    try:
        _console_handler_id = logger.add(
            sys.stderr,
            level=console_log_level,
            format=console_format,
            colorize=True,
        )
    except ValueError:
        # Invalid level string in env var — fall back to INFO
        _console_handler_id = logger.add(
            sys.stderr,
            level="INFO",
            format=console_format,
            colorize=True,
        )
        logger.warning(
            f"Invalid CALDAV_TASKS_API_LOG_LEVEL '{console_log_level}'. "
            "Defaulting to INFO for console."
        )
        console_log_level = "INFO"

    # --- File handler (always DEBUG) ---
    app_name = "caldav-tasks-api"
    app_author = "thiswillbeyourgithub"

    try:
        log_file_dir = Path(user_log_dir(app_name, app_author))
        log_file_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_file_dir / "app.log"

        logger.add(
            log_file_path,
            level="DEBUG",
            rotation="10 MB",
            retention="10 days",
            compression="zip",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {process}:{thread} "
                "| {name}:{function}:{line} - {message}"
            ),
            encoding="utf-8",
        )
        logger.info(
            f"Logging initialized. Console level: {console_log_level}. "
            f"Log file: {log_file_path}"
        )
    except Exception as e:
        print(f"CRITICAL: Failed to initialize file logger: {e}", file=sys.stderr)
        logger.error(f"Failed to initialize file logger: {e}")
        logger.warning(
            "File logging disabled due to an error. " "Check permissions or disk space."
        )


def enable_debug_logging() -> None:
    """Switch the console handler to DEBUG level.

    Intended to be called when the CLI --debug flag is passed, so that
    debug messages appear on the terminal without needing the env var.
    """
    global _console_handler_id

    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> "
        "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
        "- <level>{message}</level>"
    )

    # Remove the current console handler and replace it with a DEBUG-level one
    if _console_handler_id is not None:
        try:
            logger.remove(_console_handler_id)
        except ValueError:
            pass  # Already removed, harmless

    _console_handler_id = logger.add(
        sys.stderr,
        level="DEBUG",
        format=console_format,
        colorize=True,
    )
    logger.debug("Console log level set to DEBUG via --debug flag.")


# Automatically configure logging when this module is imported
setup_logging()

__all__ = ["logger", "enable_debug_logging"]
