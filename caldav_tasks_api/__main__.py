"""
CLI entry point for the Tasks API.

This module uses the `fire` library to expose functionalities of the TasksAPI
as command-line interface commands.
"""

import fire
import os
# import pprint as pp # No longer used
import code  # For interactive debugging
from typing import List, Optional  # For type hinting

from loguru import logger # Import logger

from .caldav_tasks_api import TasksAPI  # Assuming tasks_api.py is in the same package
# Ensure logging is configured if this module is run directly or imported before package __init__
# from . import logging_config # This is now handled by package __init__


class CliCommands:
    """
    A CLI for interacting with the TasksAPI.

    Credentials (url, username, password) can be provided as arguments
    or loaded from CALDAV_URL, CALDAV_USERNAME, CALDAV_PASSWORD environment variables.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        nextcloud_mode: bool = True,
        debug: bool = False,
        list: Optional[List[str]] = None,
    ):  # Added 'list' argument
        """
        Initializes the CLI commands.

        Args:
            url: The base URL of the CalDAV server. Defaults to CALDAV_URL env var.
            username: The username for authentication. Defaults to CALDAV_USERNAME env var.
            password: The password for authentication. Defaults to CALDAV_PASSWORD env var.
            nextcloud_mode: If True, adjusts URL for Nextcloud's specific path.
            debug: If True, enables PDB post-mortem debugging and interactive console.
            list: Optional list of task list names or UIDs to load.
        """
        self._url = url or os.environ.get("CALDAV_URL")
        self._username = username or os.environ.get("CALDAV_USERNAME")
        self._password = password or os.environ.get("CALDAV_PASSWORD")
        self._nextcloud_mode = nextcloud_mode
        self._debug = debug  # Store the debug flag
        self._target_lists = list  # Store the target lists

        self._api: TasksAPI | None = None
        logger.debug(f"CliCommands initialized with url: {'***' if self._url else None}, user: {self._username}, nc_mode: {self._nextcloud_mode}, debug: {self._debug}, lists: {self._target_lists}")


    def _validate_credentials(self) -> None:
        """Checks if necessary credentials are set."""
        if not self._url:
            logger.error("CalDAV server URL not provided.")
            raise ValueError(
                "CalDAV server URL must be provided via --url argument or CALDAV_URL environment variable."
            )
        if not self._username:
            logger.error("CalDAV username not provided.")
            raise ValueError(
                "CalDAV username must be provided via --username argument or CALDAV_USERNAME environment variable."
            )
        if not self._password:
            logger.error("CalDAV password not provided.")
            # For password, we might allow it to be prompted for interactively in a real CLI,
            # but for now, require it via arg or env var.
            raise ValueError(
                "CalDAV password must be provided via --password argument or CALDAV_PASSWORD environment variable."
            )
        logger.debug("Credentials validated successfully.")

    def _get_api(self) -> TasksAPI:
        """
        Initializes and returns the TasksAPI instance.
        Raises ValueError if credentials are not set.
        """
        self._validate_credentials()  # Ensure credentials are set before trying to connect

        if self._api is None:
            logger.info(f"Initializing TasksAPI for CalDAV server at: {self._url}")
            self._api = TasksAPI(
                url=self._url,  # type: ignore
                username=self._username,  # type: ignore
                password=self._password,  # type: ignore
                nextcloud_mode=self._nextcloud_mode,
                debug=self._debug,  # Pass the debug flag to TasksAPI
                target_lists=self._target_lists,  # Pass the target lists
            )
        return self._api

    def show_summary(self) -> None:
        """
        Connects to the CalDAV server, loads all task lists and tasks,
        and prints a summary.
        """
        try:
            api = self._get_api()
            logger.info("Loading remote tasks...")
            api.load_remote_data()

            logger.info("--- Summary ---")
            logger.info(f"Total Task Lists loaded: {len(api.task_lists)}")
            total_tasks_count = 0
            for tl in api.task_lists:
                # tasks_in_list = api.get_tasks_by_list_uid(tl.uid) # This still works
                # Or directly access tl.tasks
                logger.info(
                    f"  List: '{tl.name}' (UID: {tl.uid}, Color: {tl.color}) - Tasks: {len(tl.tasks)}"
                )
                total_tasks_count += len(tl.tasks)

            logger.info(f"Total Tasks loaded: {total_tasks_count}")

            if self._debug:
                logger.info(
                    "Debug mode: Starting interactive console. API available as 'api'."
                )
                logger.info("Variables available: api, self (CliCommands instance), locals()")
                # Expose api and self to the interactive console
                # Also, all local variables of show_summary will be available.
                _globals = globals().copy()
                _locals = locals().copy()
                _globals.update(_locals)  # Make local variables accessible
                code.interact(local=_globals)

        except ConnectionError as ce:
            logger.error(f"Connection failed: {ce}")
        except ValueError as ve:  # For missing credentials or other value errors
            logger.error(f"Configuration error: {ve}")
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    # Note: If this script is run directly, logging_config might not have been initialized
    # if caldav_tasks_api package wasn't imported first.
    # However, our __init__.py handles this.
    # For robustness, one could add:
    # try:
    #     from . import logging_config
    # except ImportError: # If run as top-level script and not as part of package
    #     import logging_config # This would only work if logging_config.py is in PYTHONPATH
    fire.Fire(CliCommands)
