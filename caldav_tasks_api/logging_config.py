import os
import sys
from pathlib import Path

from loguru import logger
from platformdirs import user_log_dir

def setup_logging():
    """Configures loguru loggers for console and file output."""
    logger.remove()  # Remove default handler to avoid duplicate messages if re-configured

    # Console logger
    # Determine console log level from environment variable, default to INFO
    console_log_level = os.environ.get("CALDAV_TASKS_API_LOG_LEVEL", "INFO").upper()
    try:
        logger.add(
            sys.stderr,
            level=console_log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True, # Enable colorization for the console
        )
    except ValueError: # Handle invalid log level from env var
        logger.add(
            sys.stderr,
            level="INFO", # Default to INFO if env var is invalid
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
        )
        logger.warning(f"Invalid CALDAV_TASKS_API_LOG_LEVEL '{console_log_level}'. Defaulting to INFO for console.")
        console_log_level = "INFO" # Update for the info message below

    # File logger
    # Using appname and appauthor (you might want to centralize these, e.g., from setup.py or a config)
    app_name = "caldav-tasks-api"
    app_author = "thiswillbeyourgithub" # As per your setup.py author (or a generic org name)
    
    try:
        log_file_dir = Path(user_log_dir(app_name, app_author))
        # Ensure directory exists
        log_file_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_file_dir / "app.log"

        logger.add(
            log_file_path,
            level="DEBUG",  # Always DEBUG for file
            rotation="10 MB",  # Rotate after 10 MB
            retention="10 days",  # Keep logs for 10 days
            compression="zip",  # Compress rotated files
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {process}:{thread} | {name}:{function}:{line} - {message}",
            encoding="utf-8",
        )
        # Initial log message after setup
        logger.info(f"Logging initialized. Console level: {console_log_level}. Log file: {log_file_path}")
    except Exception as e:
        # Use a basic print here, as logger might not be fully set up or itself failing
        print(f"CRITICAL: Failed to initialize file logger: {e}", file=sys.stderr)
        # Attempt to add a console handler for this specific error if not already done
        if not any(handler for handler_id, handler in logger._core.handlers.items() if handler._name == sys.stderr.name): # type: ignore
            logger.add(sys.stderr, level="ERROR", format="{time} {level} {message}", colorize=True)
        logger.error(f"Failed to initialize file logger: {e}")
        logger.warning("File logging disabled due to an error. Check permissions or disk space.")


# Automatically configure logging when this module is imported
setup_logging()

# Make logger available for import from this module if desired, though direct `from loguru import logger` is also fine.
__all__ = ["logger"]
