# Guide

This document outlines the primary functionalities provided by the `caldav-tasks-api` package, both through its Command-Line Interface (CLI) and its Python API.

## Command-Line Interface (CLI)

The CLI offers quick access to common CalDAV task operations. It can be invoked using:

```bash
caldav-tasks-api <command> [options]
```

or when running from source:

```bash
python -m caldav_tasks_api <command> [options]
```

> **Note:**
> Common CLI options for specifying CalDAV server URL, username, and password can be provided directly on the command line (e.g., `--url`, `--username`, `--password`) or through environment variables (`CALDAV_TASKS_API_URL`, `CALDAV_TASKS_API_USERNAME`, `CALDAV_TASKS_API_PASSWORD`).
>
> The `show_summary` command defaults to read-only but can be explicitly set to allow modifications using the `--read-write` flag. The `add-task` command inherently modifies data and operates in write mode by default (it does not use a `--read-write` flag). Other commands like `list-lists` and `list-latest-tasks` are strictly read-only.
>
> Use `caldav-tasks-api --help` or `caldav-tasks-api <command> --help` for full details.

### Available CLI Commands

#### `show_summary`

**Description:** Connects to the CalDAV server, loads all (or specified) task lists and their tasks, and prints a summary to the console.

**Key Options:**
- `--list TEXT, -l TEXT`: Specify task list name(s) or UID(s) to load. Can be used multiple times. If omitted, all accessible task lists are loaded.
- `--json`: Output the summary information in JSON format instead of plain text.
- `--read-only` (default) / `--read-write`: Control modification permissions.

**Example:**
```bash
caldav-tasks-api show_summary --url <your_url> --username <user> --password <pass> --list "Work List"
```

#### `list-lists`

**Description:** Fetches and prints a JSON-formatted list of all available task lists (calendars that support VTODOs). Each entry includes the list's name and UID. This command is inherently read-only.

**Key Options:**
_(This command has no specific key options beyond the common connection ones like `--url`, `--username`, etc.)_

**Example:**
```bash
caldav-tasks-api list-lists --url <your_url> --username <user> --password <pass>
```

#### `add-task`

**Description:** Adds a new task to a specified task list on the CalDAV server. This command inherently operates with write permissions to the server.

**Key Options:**
- `--list-uid TEXT`: The UID of the task list where the task will be added. This is mandatory if the `CALDAV_TASKS_API_DEFAULT_LIST_UID` environment variable is not set.
- `--summary TEXT`: The summary or title text for the new task. This is required.
- `--description TEXT`: Description for the task.
- `--priority INTEGER`: Priority of the task (0-9, where 0 means undefined) [default: 0].
- `--due-date TEXT`: Due date in format YYYYMMDD or YYYYMMDDTHHMMSSZ (e.g., 20240315 or 20240315T143000Z).
- `--start-date TEXT`: Start date in format YYYYMMDD or YYYYMMDDTHHMMSSZ (e.g., 20240315 or 20240315T143000Z).
- `--tag TEXT`: Add a tag/category to the task (can be used multiple times).
- `--parent TEXT`: UID of the parent task (for creating subtasks).
- `--x-property TEXT`: Add a custom X-property in format KEY=VALUE (can be used multiple times). Example: `--x-property X-CUSTOM-FIELD=myvalue`
- `--percent-complete INTEGER`: Completion percentage (0-100) [default: 0].

**Example:**
```bash
caldav-tasks-api add-task --url <your_url> --username <user> --password <pass> --list-uid "aabbccdd-eeff-1122-3344-556677889900" --summary "Buy groceries" --description "Don't forget milk" --priority 5 --due-date 20240315
```

#### `list-latest-tasks`

**Description:** Lists non-completed tasks from a specific task list (or all lists if `--list-uid` is not specified and the default environment variable isn't set). Tasks are selected by their creation date (most recent first), up to the specified limit. The final output in JSON then lists these selected tasks, ordered from oldest to newest among the selection. This command is inherently read-only.

**Key Options:**
- `--list-uid TEXT`: UID of the task list to filter tasks from. If not provided, uses the `CALDAV_TASKS_API_DEFAULT_LIST_UID` environment variable if set.
- `--limit INTEGER`: The maximum number of tasks to return (default is 10).

**Example:**
```bash
caldav-tasks-api list-latest-tasks --url <your_url> --username <user> --password <pass> --list-uid "task-list-xyz" --limit 5
```

## Python API

The Python API provides more granular control over CalDAV interactions and is primarily accessed through the `TasksAPI` class.

### Core Class: `caldav_tasks_api.TasksAPI`

This is the main class for initializing a connection to a CalDAV server and managing tasks.

#### `__init__(url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None, nextcloud_mode: bool = True, debug: bool = False, target_lists: Optional[List[str]] = None, read_only: bool = False, ssl_verify_cert: bool = True)`

**Description:** Initializes the API client. It attempts to connect to the CalDAV server using the provided credentials and settings. If credentials are not provided as arguments, they will be read from environment variables.

**Parameters:**
- `url` (Optional[str], optional): The base URL of the CalDAV server (e.g., "https://example.com/dav"). If `None`, reads from `CALDAV_TASKS_API_URL` environment variable.
- `username` (Optional[str], optional): The username for CalDAV authentication. If `None`, reads from `CALDAV_TASKS_API_USERNAME` environment variable.
- `password` (Optional[str], optional): The password for CalDAV authentication. If `None`, reads from `CALDAV_TASKS_API_PASSWORD` environment variable.
- `nextcloud_mode` (bool, optional): If `True` (default), adjusts the URL for Nextcloud's specific CalDAV path (e.g., appending "/remote.php/dav/"). Set to `False` for other CalDAV servers if necessary.
- `debug` (bool, optional): If `True` (default: `False`), enables PDB post-mortem debugging on certain exceptions.
- `target_lists` (Optional[List[str]], optional): A list of task list names or UIDs. If provided, the API will only interact with these specified lists. If `None` (default), all accessible task lists are considered.
- `read_only` (bool, optional): If `True` (default: `False`), the API operates in read-only mode, preventing any modifications to the server (e.g., adding, updating, or deleting tasks).
- `ssl_verify_cert` (bool, optional): If `True` (default), verifies SSL certificates. Set to `False` for self-signed certificates.

**Raises:** 
- `ValueError` if required credentials cannot be determined from arguments or environment variables.
- `ConnectionError` if the connection to the CalDAV server fails.

#### `load_remote_data()`

**Description:** Fetches all relevant task lists (calendars supporting VTODOs that match `target_lists` if specified during initialization) and all their tasks from the CalDAV server. The fetched data populates the `api.task_lists` attribute, overwriting any previously loaded local data.

**Raises:** `ConnectionError` if the API instance is not connected to the server.

#### `get_task_list_by_uid(list_uid: str) -> Optional[TaskListData]`

**Description:** Retrieves a specific `TaskListData` object from the task lists currently loaded into the API instance (e.g., after a call to `load_remote_data()`).

**Parameters:**
- `list_uid` (str): The UID of the task list to retrieve.

**Returns:** A `TaskListData` object if a list with the given UID is found, otherwise `None`.

#### `get_tasks_by_list_uid(list_uid: str) -> list[TaskData]`

**Description:** Retrieves all `TaskData` objects that belong to a specific task list, identified by its UID, from the currently loaded tasks.

**Parameters:**
- `list_uid` (str): The UID of the task list whose tasks are to be retrieved.

**Returns:** A list of `TaskData` objects. Returns an empty list if the task list is not found or contains no tasks.

#### `get_task_by_global_uid(task_uid: str) -> Optional[TaskData]`

**Description:** Retrieves a specific `TaskData` object by its unique ID (UID), searching across all task lists currently loaded in the API instance.

**Parameters:**
- `task_uid` (str): The UID of the task to retrieve.

**Returns:** A `TaskData` object if a task with the given UID is found, otherwise `None`.

#### `add_task(task_data: TaskData, list_uid: Optional[str] = None) -> TaskData`

**Description:** Adds a new task to the CalDAV server. The task's details should be pre-configured in the `task_data` object. The target list UID can be specified directly via the `list_uid` argument, fall back to `task_data.list_uid`, or finally use the `CALDAV_TASKS_API_DEFAULT_LIST_UID` environment variable.

**Parameters:**
- `task_data` (`TaskData`): An instance of `TaskData` representing the new task to be created. Its attributes (e.g., `summary`, `description`, `due_date`) should be set as desired.
- `list_uid` (Optional[str], optional): The UID of the task list to add the task to. If `None`, the method attempts to determine the list UID as described above.

**Returns:** The `TaskData` object representing the newly created task, updated with information from the server (such as the server-assigned UID if not initially provided, and timestamps).

**Raises:**
- `PermissionError`: If the API is in read-only mode.
- `ValueError`: If the task list UID cannot be determined or if the specified task list is not found on the server.

#### `update_task(task_data: TaskData) -> TaskData`

**Description:** Updates an existing task on the CalDAV server. The `task_data` object must have its `uid` and `list_uid` attributes correctly set to identify the task. Other attributes of `task_data` should reflect the desired changes. The `changed_at` timestamp is automatically updated.

**Parameters:**
- `task_data` (`TaskData`): The `TaskData` instance containing the updated information for an existing task.

**Returns:** The `TaskData` object, potentially updated with server responses (e.g., a new `LAST-MODIFIED` timestamp).

**Raises:**
- `PermissionError`: If the API is in read-only mode.
- `ValueError`: If the `task_data.uid` or `task_data.list_uid` is missing, or if the task or list is not found on the server.

#### `delete_task(task_uid: str, list_uid: str) -> bool`

**Description:** Deletes a task from the specified task list on the CalDAV server.

**Parameters:**
- `task_uid` (str): The UID of the task to be deleted.
- `list_uid` (str): The UID of the task list from which the task should be deleted.

**Returns:** `True` if the task was successfully deleted.

**Raises:**
- `PermissionError`: If the API is in read-only mode.
- `ValueError`: If the task list or the task itself is not found on the server.

For more detailed information on the `TasksAPI` class, including all its methods and attributes, refer to its docstrings.

### Data Structures

The Python API uses several dataclasses to represent CalDAV entities and their properties. The main ones are:

- **`caldav_tasks_api.utils.data.TaskListData`**: Represents a task list (equivalent to a CalDAV calendar that supports VTODOs). Key attributes include `uid`, `name`, and `tasks` (a list of `TaskData` objects).
- **`caldav_tasks_api.utils.data.TaskData`**: Represents an individual task (a VTODO component). Key attributes include `uid`, `summary` (summary), `description` (description), `completed`, `due_date`, `priority`, `x_properties`, etc. It also includes methods like `to_ical()` and `from_ical()` for VTODO string conversion.
- **`caldav_tasks_api.utils.data.XProperties`**: A specialized class for handling custom `X-` properties within a `TaskData` object, allowing both dictionary-style and attribute-style access.

Detailed documentation for these data structures, including all their fields and methods, can be found in their docstrings.

Refer to the source code or the [examples page](https://caldavtasksapi.readthedocs.io/en/stable/examples.html) for practical usage patterns.
