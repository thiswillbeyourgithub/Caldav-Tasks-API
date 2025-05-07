import pdb
import urllib3
import caldav
from caldav import DAVClient, Principal, Calendar, Todo
from caldav.elements import dav, ical
from icalendar import Calendar as IcsCalendar  # For fallback parsing
from typing import List, Optional

from loguru import logger # Import logger

from .utils.data import (
    TaskListData,
    TaskData,
)  # Assuming utils/data.py is in the same directory or accessible path
# Ensure logging is configured (handled by package __init__)


class TasksAPI:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        nextcloud_mode: bool = True,
        debug: bool = False,
        target_lists: Optional[List[str]] = None,
    ):
        """
        Initializes the TasksAPI and connects to the CalDAV server.

        Args:
            url: The base URL of the CalDAV server.
            username: The username for authentication.
            password: The password for authentication.
            nextcloud_mode: If True, adjusts URL for Nextcloud's specific path.
            debug: If True, enables PDB post-mortem debugging on specific errors.
            target_lists: Optional list of calendar names or UIDs to filter by.
        """
        self.url = url
        self.username = username
        self.password = password # Storing password in memory, consider security implications for long-running apps
        self.nextcloud_mode = nextcloud_mode
        self.debug = debug  # Store the debug flag
        self.target_lists = target_lists  # Store the target lists

        logger.debug(f"TasksAPI initializing with URL: {self.url}, User: {self.username}, Nextcloud Mode: {self.nextcloud_mode}, Debug: {self.debug}, Target Lists: {self.target_lists}")

        self._adjust_url()

        self.client: DAVClient | None = None
        self.principal: Principal | None = None
        self.raw_calendars: list[Calendar] = []  # Stores caldav.Calendar objects

        self.task_lists: list[TaskListData] = (
            []
        )  # Stores TaskListData objects, which will now contain their tasks

        self._connect()

    def _adjust_url(self) -> None:
        """Adjusts the URL, e.g., adding https or Nextcloud's CalDAV path."""
        original_url = self.url
        # Add scheme if missing
        if not self.url.startswith("http://") and not self.url.startswith("https://"):
            self.url = "https://" + self.url
            logger.debug(f"Adjusted URL: Added https scheme. Original: '{original_url}', New: '{self.url}'")

        # Add Nextcloud specific suffix if in nextcloud_mode and not present
        if self.nextcloud_mode and "remote.php/dav" not in self.url:
            if not self.url.endswith("/"):
                self.url += "/"
            self.url += "remote.php/dav/"
            logger.debug(f"Adjusted URL: Added Nextcloud suffix. Original: '{original_url}', New: '{self.url}'")
        elif self.nextcloud_mode and self.url.endswith(
            "remote.php/dav"
        ):  # Ensure trailing slash
            self.url += "/"
            logger.debug(f"Adjusted URL: Added trailing slash to Nextcloud path. Original: '{original_url}', New: '{self.url}'")
        
        if original_url != self.url:
            logger.info(f"URL adjusted from '{original_url}' to '{self.url}'")
        else:
            logger.debug(f"URL '{self.url}' did not require adjustment.")


    def _connect(self) -> None:
        """Establishes connection to the CalDAV server."""
        logger.info(f"Attempting to connect to CalDAV server at: {self.url}")
        urllib3.disable_warnings(
            urllib3.exceptions.InsecureRequestWarning
        )  # Optional: suppress SSL warnings for self-signed certs
        logger.debug("InsecureRequestWarning suppressed for urllib3.")

        try:
            # Note: caldav.DAVClient is a context manager, but we can use it directly
            # if we manage its lifecycle (e.g. no explicit close() needed for these operations)
            # For long-lived objects, consider how sessions are handled or re-authenticate if needed.
            self.client = DAVClient(
                url=self.url,
                username=self.username,
                password=self.password,
                ssl_verify_cert=False,  # Set to True in production with valid certs
            )
            logger.debug("DAVClient instantiated.")
            self.principal = self.client.principal()
            logger.info(
                f"Successfully connected to CalDAV server. Principal URL: {self.principal.url}"
            )
            self._fetch_raw_calendars()
        except Exception as e:
            logger.error(f"Error connecting to CalDAV server: {e}", exc_info=True)
            # Raise the exception or handle it as per application's needs
            raise ConnectionError(f"Failed to connect to CalDAV server: {e}")

    def _fetch_raw_calendars(self) -> None:
        """Fetches raw caldav.Calendar objects from the server."""
        if not self.principal:
            logger.warning("Cannot fetch calendars: Not connected (no principal).")
            return

        logger.debug("Fetching raw calendars from server.")
        try:
            all_calendars_from_server = self.principal.calendars()
            logger.debug(f"Found {len(all_calendars_from_server)} total calendars initially from principal.")
            
            all_calendars = [
                cal
                for cal in all_calendars_from_server # Iterate over the fetched list
                if "VTODO" in cal.get_supported_components()  # Ensure it's a task list
            ]
            logger.debug(f"Filtered to {len(all_calendars)} calendars supporting VTODO component.")


            if self.target_lists:
                logger.info(f"Filtering calendars based on target list: {self.target_lists}")
                self.raw_calendars = [
                    cal
                    for cal in all_calendars
                    if cal.name in self.target_lists or str(cal.id) in self.target_lists # cal.id can be non-string (e.g. URL object)
                ]
                logger.info(
                    f"Fetched {len(self.raw_calendars)} task-supporting calendars after filtering from {len(all_calendars)} VTODO-supporting calendars."
                )
            else:
                self.raw_calendars = all_calendars
                logger.info(f"Fetched {len(self.raw_calendars)} task-supporting calendars (no specific target lists).")

        except Exception as e:
            logger.error(f"Error fetching calendars from server: {e}", exc_info=True)
            self.raw_calendars = []  # Reset if error

    def load_remote_data(self) -> None:
        """
        Loads all task lists and tasks from the remote CalDAV server into memory.
        This will overwrite any existing local data in self.task_lists
        """
        if not self.principal:
            logger.error("Cannot load remote data: Not connected (no principal).")
            raise ConnectionError("Not connected to CalDAV server.")

        logger.info("Loading remote data...")
        self._fetch_raw_calendars()  # Refresh the list of raw calendars

        self.task_lists = [] # Clear existing task lists
        logger.debug("Cleared local task_lists cache.")


        for cal in self.raw_calendars:
            logger.debug(f"Processing calendar: {cal.name} (ID: {cal.id}, URL: {cal.url})")

            task_list_data = TaskListData(
                uid=str(cal.id),
                name=cal.name if cal.name else "Unnamed List",
                synced=True,
            )
            self.task_lists.append(task_list_data)
            logger.info(
                f"  Added task list: {task_list_data.name} (UID: {task_list_data.uid})"
            )

            tasks_added_to_list_count = 0
            failed_tasks_in_list_count = 0

            try:
                todos_from_caldav: list[Todo] = cal.todos(include_completed=True)
                logger.debug(
                    f"  Found {len(todos_from_caldav)} tasks in '{task_list_data.name}' via cal.todos()."
                )
                for todo_obj in todos_from_caldav:
                    try:
                        logger.trace(f"    Raw VTODO data from caldav.Todo (UID: {todo_obj.id}): {str(todo_obj.data)[:200]}...")
                        task_data = TaskData.from_ical(
                            todo_obj.data, list_uid=task_list_data.uid
                        )
                        task_data.synced = True
                        task_list_data.tasks.append(task_data)
                        tasks_added_to_list_count += 1
                        logger.trace(f"    Successfully parsed VTODO (UID: {task_data.uid}) and added to list '{task_list_data.name}'.")
                    except Exception as e_parse:
                        failed_tasks_in_list_count += 1
                        task_uid_str = todo_obj.id if todo_obj.id else "N/A (caldav Todo object)"
                        logger.error(
                            f"    Error parsing VTODO (caldav Todo ID: {task_uid_str}) in list '{task_list_data.name}': {e_parse}", exc_info=True
                        )

            except Exception as e_fetch_todos:
                logger.warning(
                    f"  cal.todos() failed for list '{task_list_data.name}': {e_fetch_todos}. Attempting fallback.", exc_info=True
                )
                calendar_raw_data = None
                try:
                    calendar_raw_data = cal.data
                    logger.debug(f"  Fallback: Accessed cal.data for '{task_list_data.name}'. Length: {len(calendar_raw_data) if calendar_raw_data else 0} chars.")
                except AttributeError:
                    logger.error(
                        f"    Fallback Error: Failed to access raw data using cal.data for list '{task_list_data.name}'. The 'data' attribute is missing."
                    )
                    continue
                except Exception as e_get_data:
                    logger.error(
                        f"    Fallback Error: An unexpected error occurred while trying to access cal.data for list '{task_list_data.name}': {e_get_data}", exc_info=True
                    )
                    continue

                if not calendar_raw_data:
                    logger.warning(
                        f"    Fallback: No raw calendar data (cal.data is empty or None) available for list '{task_list_data.name}'. Cannot perform fallback parsing."
                    )
                else:
                    try:
                        ics_calendar_obj = IcsCalendar.from_ical(calendar_raw_data)
                        vtodo_components_found = 0
                        for component in ics_calendar_obj.walk("VTODO"):
                            vtodo_components_found += 1
                            vtodo_ical_string: str = ""
                            try:
                                vtodo_ical_string_bytes = component.to_ical()
                                vtodo_ical_string = vtodo_ical_string_bytes.decode("utf-8", errors="replace")
                                logger.trace(f"    Fallback: Raw VTODO string from icalendar component: {vtodo_ical_string[:200]}...")
                                task_data = TaskData.from_ical(
                                    vtodo_ical_string, list_uid=task_list_data.uid
                                )
                                task_data.synced = True
                                task_list_data.tasks.append(task_data)
                                tasks_added_to_list_count += 1
                                logger.trace(f"    Fallback: Successfully parsed VTODO (UID: {task_data.uid}) and added to list '{task_list_data.name}'.")
                            except Exception as e_parse_fallback:
                                failed_tasks_in_list_count += 1
                                task_uid_str = component.get("UID", "N/A (icalendar component)")
                                logger.error(
                                    f"    Fallback Error: Parsing VTODO (UID from icalendar: {task_uid_str}) for list '{task_list_data.name}': {e_parse_fallback}", exc_info=True
                                )
                                if self.debug and vtodo_ical_string:
                                    logger.debug(
                                        f"      Problematic VTODO string (first 500 chars) during fallback:\n{vtodo_ical_string[:500]}..."
                                    )
                        logger.debug(
                            f"  Fallback parsing: Found {vtodo_components_found} VTODO components in raw data for '{task_list_data.name}'."
                        )
                    except Exception as e_parse_calendar_raw:
                        logger.error(
                            f"    Fallback Error: Failed to parse raw calendar data for list '{task_list_data.name}' with icalendar library: {e_parse_calendar_raw}", exc_info=True
                        )
                        logger.warning(
                            f"    Skipping all tasks for this list ('{task_list_data.name}') due to severe parsing error of the whole calendar data during fallback."
                        )
                        if self.debug:
                            logger.error(
                                f"    DEBUG mode enabled: Entering PDB post-mortem debugger for error in list '{task_list_data.name}' (raw calendar parse fallback)."
                            )
                            pdb.post_mortem()

            if tasks_added_to_list_count > 0:
                logger.info(
                    f"  Successfully loaded {tasks_added_to_list_count} tasks for list '{task_list_data.name}'."
                )
            if failed_tasks_in_list_count > 0:
                logger.warning(
                    f"  Failed to parse {failed_tasks_in_list_count} tasks in list '{task_list_data.name}'. Check logs for details."
                )
            if tasks_added_to_list_count == 0 and failed_tasks_in_list_count == 0 and len(getattr(cal, 'todos_from_caldav', [])) == 0 : # check if todos were attempted
                 logger.info(
                    f"  No tasks were found or loaded for list '{task_list_data.name}'."
                )


        total_tasks_loaded = sum(len(tl.tasks) for tl in self.task_lists)
        logger.info(
            f"Finished loading remote data. Total lists: {len(self.task_lists)}, Total tasks: {total_tasks_loaded}"
        )

    def get_task_list_by_uid(self, list_uid: str) -> TaskListData | None:
        """Retrieves a loaded task list by its UID."""
        logger.debug(f"Attempting to get task list by UID: {list_uid}")
        for tl in self.task_lists:
            if tl.uid == list_uid:
                logger.trace(f"Found task list: {tl.name} for UID {list_uid}")
                return tl
        logger.debug(f"Task list with UID {list_uid} not found.")
        return None

    def get_tasks_by_list_uid(self, list_uid: str) -> list[TaskData]:
        """Retrieves all loaded tasks belonging to a specific list UID."""
        logger.debug(f"Attempting to get tasks for list UID: {list_uid}")
        task_list = self.get_task_list_by_uid(list_uid)
        if task_list:
            logger.trace(f"Returning {len(task_list.tasks)} tasks for list UID {list_uid} ('{task_list.name}').")
            return task_list.tasks
        logger.debug(f"No tasks found for list UID {list_uid} as list itself was not found.")
        return []

    def add_task(self, task_data: TaskData, list_uid: str) -> TaskData:
        """
        Adds a new task to the specified task list on the server.
        """
        logger.info(f"Attempting to add task (UID: {task_data.uid if task_data.uid else 'new'}) to list UID: {list_uid}")
        if not self.raw_calendars:
            logger.debug("Raw calendars not loaded, fetching them before adding task.")
            self._fetch_raw_calendars()

        target_raw_calendar: Optional[Calendar] = None
        for cal in self.raw_calendars:
            if str(cal.id) == list_uid:
                target_raw_calendar = cal
                logger.debug(f"Found target calendar '{cal.name}' (ID: {cal.id}) for adding task.")
                break

        if not target_raw_calendar:
            logger.error(f"Task list (calendar) with UID '{list_uid}' not found for adding task.")
            raise ValueError(f"Task list (calendar) with UID '{list_uid}' not found.")

        vtodo_ical_string = task_data.to_ical()
        logger.debug(
            f"  Attempting to save new VTODO to calendar '{target_raw_calendar.name}':\n{vtodo_ical_string[:200]}..."
        )
        try:
            new_todo_obj: Todo = target_raw_calendar.add_todo(vtodo_ical_string)
            logger.info(
                f"    Successfully saved VTODO. Server URL: {new_todo_obj.url}, Server UID (href part): {new_todo_obj.id}"
            )
            
            # The UID from the server might be different or more complete (e.g. full href)
            # TaskData.from_ical should ideally parse the UID from the VTODO string itself.
            # After add_todo, new_todo_obj.data should contain the server's version of the VTODO.
            # We should re-parse it to get the authoritative UID and other server-set fields.
            if new_todo_obj.data:
                logger.debug("Re-parsing task data from server response to get authoritative UID and other fields.")
                updated_task_data = TaskData.from_ical(new_todo_obj.data, list_uid=list_uid)
                # updated_task_data.synced is True if from_ical parsed a UID, which is expected.
                
                # Update the original task_data instance with server-authoritative values
                task_data.uid = updated_task_data.uid # Most important
                task_data.changed_at = updated_task_data.changed_at # Server might update this
                # Potentially other fields if server modifies them could be copied here.
                task_data.synced = True # Mark the original task_data as synced
                
                logger.debug(f"  Task data updated with server UID: {task_data.uid}, changed_at: {task_data.changed_at}, synced: {task_data.synced}")

            else: # Fallback if new_todo_obj.data is not available
                task_data.uid = str(new_todo_obj.id) if new_todo_obj.id else task_data.uid
                task_data.synced = True # Mark the original task_data as synced
                logger.debug(f"  Task data updated with server href part as UID: {task_data.uid}, synced: {task_data.synced}. Full data not re-parsed.")

            return task_data

        except Exception as e:
            logger.error(
                f"    Error saving VTODO to calendar '{target_raw_calendar.name}': {e}", exc_info=True
            )
            task_data.synced = False # Ensure synced is false on error
            if self.debug:
                logger.error("Debug mode: Entering PDB for add_task error.")
                pdb.post_mortem()
            raise

    def delete_task(self, task_uid: str, list_uid: str) -> bool:
        """
        Deletes a task from the specified task list on the server.
        """
        logger.info(f"Attempting to delete task UID '{task_uid}' from list UID '{list_uid}'.")
        if not self.raw_calendars:
            logger.debug("Raw calendars not loaded, fetching them before deleting task.")
            self._fetch_raw_calendars()

        target_raw_calendar: Optional[Calendar] = None
        for cal in self.raw_calendars:
            if str(cal.id) == list_uid:
                target_raw_calendar = cal
                logger.debug(f"Found target calendar '{cal.name}' (ID: {cal.id}) for task deletion.")
                break

        if not target_raw_calendar:
            logger.error(
                f"Task list (calendar) with UID '{list_uid}' not found for task deletion."
            )
            raise ValueError(
                f"Task list (calendar) with UID '{list_uid}' not found for deletion."
            )

        try:
            task_to_delete: Todo = target_raw_calendar.todo_by_uid(task_uid)
            logger.debug(
                f"  Found VTODO by UID '{task_uid}' (URL: {task_to_delete.url}) in calendar '{target_raw_calendar.name}'. Attempting delete."
            )
            task_to_delete.delete()
            logger.info(f"    Successfully deleted VTODO UID '{task_uid}'.")
            return True
        except caldav.lib.error.NotFoundError:
            logger.error(
                f"    Task with UID '{task_uid}' not found in calendar '{target_raw_calendar.name}' for deletion using todo_by_uid."
            )
            raise ValueError(
                f"Task with UID '{task_uid}' not found in list '{list_uid}' for deletion."
            )
        except Exception as e:
            logger.error(
                f"    Error deleting VTODO UID '{task_uid}' from calendar '{target_raw_calendar.name}': {e}", exc_info=True
            )
            if self.debug:
                logger.error("Debug mode: Entering PDB for delete_task error.")
                pdb.post_mortem()
            raise
