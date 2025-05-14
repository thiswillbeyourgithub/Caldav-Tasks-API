API
===

This document outlines the primary functionalities provided by the `caldav-tasks-api` package,
both through its Command-Line Interface (CLI) and its Python API.

Command-Line Interface (CLI)
----------------------------

The CLI offers quick access to common CalDAV task operations. It can be invoked using 
``caldav-tasks-api <command> [options]`` (if installed via pip) or 
``python -m caldav_tasks_api <command> [options]`` (if running from source).

.. note::
   Common CLI options for specifying CalDAV server URL, username, and password can be
   provided directly on the command line (e.g., ``--url``, ``--username``, ``--password``)
   or through environment variables (``CALDAV_TASKS_API_URL``, 
   ``CALDAV_TASKS_API_USERNAME``, ``CALDAV_TASKS_API_PASSWORD``).
   Most CLI commands that only read data default to operating in read-only mode. For operations
   that modify data, like ``add-task``, the ``--read-write`` flag must be used.
   Use ``caldav-tasks-api --help`` or ``caldav-tasks-api <command> --help`` for full details.

Available CLI Commands:

*   ``show_summary``
    *   **Description:** Connects to the CalDAV server, loads all (or specified) task lists 
        and their tasks, and prints a summary to the console.
    *   **Key Options:**
        *   ``--list TEXT, -l TEXT``: Specify task list name(s) or UID(s) to load. Can be used multiple times. If omitted, all accessible task lists are loaded.
        *   ``--json``: Output the summary information in JSON format instead of plain text.
        *   ``--read-only`` (default) / ``--read-write``: Control modification permissions.
    *   **Example:** ``caldav-tasks-api show_summary --url <your_url> --username <user> --password <pass> --list "Work List"``

*   ``list-lists``
    *   **Description:** Fetches and prints a JSON-formatted list of all available task lists 
        (calendars that support VTODOs). Each entry includes the list's name and UID.
    *   **Key Options:**
        *   ``--read-only`` (default): This command only reads data.
    *   **Example:** ``caldav-tasks-api list-lists --url <your_url> --username <user> --password <pass>``

*   ``add-task``
    *   **Description:** Adds a new task to a specified task list on the CalDAV server.
    *   **Key Options:**
        *   ``--list-uid TEXT``: The UID of the task list where the task will be added. This is mandatory if the ``CALDAV_TASKS_API_DEFAULT_LIST_UID`` environment variable is not set.
        *   ``--summary TEXT``: The summary or title text for the new task. This is required.
        *   ``--read-write``: Must be specified to allow this command to modify server data.
    *   **Example:** ``caldav-tasks-api add-task --url <your_url> --username <user> --password <pass> --list-uid "aabbccdd-eeff-1122-3344-556677889900" --summary "Buy groceries" --read-write``

*   ``list-latest-tasks``
    *   **Description:** Lists the most recently created, non-completed tasks from a specific task list 
        (or all lists if ``--list-uid`` is not specified and the default environment variable isn't set). 
        Tasks are sorted by their creation date, and the output is in JSON format.
    *   **Key Options:**
        *   ``--list-uid TEXT``: UID of the task list to filter tasks from. If not provided, uses the ``CALDAV_TASKS_API_DEFAULT_LIST_UID`` environment variable if set.
        *   ``--limit INTEGER``: The maximum number of tasks to return (default is 10).
        *   ``--read-only`` (default): This command only reads data.
    *   **Example:** ``caldav-tasks-api list-latest-tasks --url <your_url> --username <user> --password <pass> --list-uid "task-list-xyz" --limit 5``


Python API
----------

The Python API provides more granular control over CalDAV interactions and is primarily
accessed through the ``TasksAPI`` class.

Core Class: ``caldav_tasks_api.TasksAPI``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the main class for initializing a connection to a CalDAV server and managing tasks.

Key `TasksAPI` Methods:

*   **`__init__(url: str, username: str, password: str, nextcloud_mode: bool = True, debug: bool = False, target_lists: Optional[List[str]] = None, read_only: bool = False)`**
    *   **Description:** Initializes the API client. It attempts to connect to the CalDAV server using the provided credentials and settings.
    *   **Parameters:**
        *   `url` (str): The base URL of the CalDAV server (e.g., "https://example.com/dav").
        *   `username` (str): The username for CalDAV authentication.
        *   `password` (str): The password for CalDAV authentication.
        *   `nextcloud_mode` (bool, optional): If `True` (default), adjusts the URL for Nextcloud's specific CalDAV path (e.g., appending "/remote.php/dav/"). Set to `False` for other CalDAV servers if necessary.
        *   `debug` (bool, optional): If `True` (default: `False`), enables PDB post-mortem debugging on certain exceptions.
        *   `target_lists` (Optional[List[str]], optional): A list of task list names or UIDs. If provided, the API will only interact with these specified lists. If `None` (default), all accessible task lists are considered.
        *   `read_only` (bool, optional): If `True` (default: `False`), the API operates in read-only mode, preventing any modifications to the server (e.g., adding, updating, or deleting tasks).
    *   **Raises:** `ConnectionError` if the connection to the CalDAV server fails.

*   **`load_remote_data()`**
    *   **Description:** Fetches all relevant task lists (calendars supporting VTODOs that match `target_lists` if specified during initialization) and all their tasks from the CalDAV server. The fetched data populates the `api.task_lists` attribute, overwriting any previously loaded local data.
    *   **Raises:** `ConnectionError` if the API instance is not connected to the server.

*   **`get_task_list_by_uid(list_uid: str) -> Optional[TaskListData]`**
    *   **Description:** Retrieves a specific `TaskListData` object from the task lists currently loaded into the API instance (e.g., after a call to `load_remote_data()`).
    *   **Parameters:**
        *   `list_uid` (str): The UID of the task list to retrieve.
    *   **Returns:** A `TaskListData` object if a list with the given UID is found, otherwise `None`.

*   **`get_tasks_by_list_uid(list_uid: str) -> list[TaskData]`**
    *   **Description:** Retrieves all `TaskData` objects that belong to a specific task list, identified by its UID, from the currently loaded tasks.
    *   **Parameters:**
        *   `list_uid` (str): The UID of the task list whose tasks are to be retrieved.
    *   **Returns:** A list of `TaskData` objects. Returns an empty list if the task list is not found or contains no tasks.

*   **`get_task_by_global_uid(task_uid: str) -> Optional[TaskData]`**
    *   **Description:** Retrieves a specific `TaskData` object by its unique ID (UID), searching across all task lists currently loaded in the API instance.
    *   **Parameters:**
        *   `task_uid` (str): The UID of the task to retrieve.
    *   **Returns:** A `TaskData` object if a task with the given UID is found, otherwise `None`.

*   **`add_task(task_data: TaskData, list_uid: Optional[str] = None) -> TaskData`**
    *   **Description:** Adds a new task to the CalDAV server. The task's details should be pre-configured in the `task_data` object. The target list UID can be specified directly via the `list_uid` argument, fall back to `task_data.list_uid`, or finally use the `CALDAV_TASKS_API_DEFAULT_LIST_UID` environment variable.
    *   **Parameters:**
        *   `task_data` (`TaskData`): An instance of `TaskData` representing the new task to be created. Its attributes (e.g., `text`, `notes`, `due_date`) should be set as desired.
        *   `list_uid` (Optional[str], optional): The UID of the task list to add the task to. If `None`, the method attempts to determine the list UID as described above.
    *   **Returns:** The `TaskData` object representing the newly created task, updated with information from the server (such as the server-assigned UID if not initially provided, and timestamps).
    *   **Raises:**
        *   `PermissionError`: If the API is in read-only mode.
        *   `ValueError`: If the task list UID cannot be determined or if the specified task list is not found on the server.

*   **`update_task(task_data: TaskData) -> TaskData`**
    *   **Description:** Updates an existing task on the CalDAV server. The `task_data` object must have its `uid` and `list_uid` attributes correctly set to identify the task. Other attributes of `task_data` should reflect the desired changes. The `changed_at` timestamp is automatically updated.
    *   **Parameters:**
        *   `task_data` (`TaskData`): The `TaskData` instance containing the updated information for an existing task.
    *   **Returns:** The `TaskData` object, potentially updated with server responses (e.g., a new `LAST-MODIFIED` timestamp).
    *   **Raises:**
        *   `PermissionError`: If the API is in read-only mode.
        *   `ValueError`: If the `task_data.uid` or `task_data.list_uid` is missing, or if the task or list is not found on the server.

*   **`delete_task(task_uid: str, list_uid: str) -> bool`**
    *   **Description:** Deletes a task from the specified task list on the CalDAV server.
    *   **Parameters:**
        *   `task_uid` (str): The UID of the task to be deleted.
        *   `list_uid` (str): The UID of the task list from which the task should be deleted.
    *   **Returns:** `True` if the task was successfully deleted.
    *   **Raises:**
        *   `PermissionError`: If the API is in read-only mode.
        *   `ValueError`: If the task list or the task itself is not found on the server.

For more detailed information on the `TasksAPI` class, including all its methods and attributes, refer to its docstrings generated below by Sphinx:

.. automodule:: caldav_tasks_api.caldav_tasks_api
   :members: TasksAPI
   :undoc-members:
   :show-inheritance:

Data Structures
~~~~~~~~~~~~~~~

The Python API uses several dataclasses to represent CalDAV entities and their properties. The main ones are:

*   **`caldav_tasks_api.utils.data.TaskListData`**: Represents a task list (equivalent to a CalDAV calendar that supports VTODOs). Key attributes include `uid`, `name`, and `tasks` (a list of `TaskData` objects).
*   **`caldav_tasks_api.utils.data.TaskData`**: Represents an individual task (a VTODO component). Key attributes include `uid`, `text` (summary), `notes` (description), `completed`, `due_date`, `priority`, `x_properties`, etc. It also includes methods like `to_ical()` and `from_ical()` for VTODO string conversion.
*   **`caldav_tasks_api.utils.data.XProperties`**: A specialized class for handling custom `X-` properties within a `TaskData` object, allowing both dictionary-style and attribute-style access.

Detailed documentation for these data structures, including all their fields and methods, can be found in their docstrings, which are rendered below by Sphinx:

.. automodule:: caldav_tasks_api.utils.data
   :members: TaskListData, TaskData, XProperties
   :undoc-members:
   :show-inheritance:

Refer to the source code or the :doc:`examples` page for practical usage patterns.
