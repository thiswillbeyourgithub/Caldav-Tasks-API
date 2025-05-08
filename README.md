# CalDAV Tasks API

A Python library and command-line interface (CLI) for interacting with CalDAV task lists (VTODOs). This project provides tools to connect to a CalDAV server, fetch task lists and tasks, create new tasks, and delete existing ones.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE.md](LICENSE.md) file for details.

## Motivation and Purpose

This library was developed as a foundational component for integrating CalDAV task management with more advanced systems. The primary goal is to serve as a backbone for:

1.  Synchronizing tasks from applications like the excellent [Tasks.org Android app](https://f-droid.org/packages/org.tasks/).
2.  Enabling features such as smart task prioritization using ELO ranking, envisioned to work with a [Litoy-like setup](https://github.com/thiswillbeyourgithub/mini_LiTOY).

By providing a robust Python interface to CalDAV tasks, this project aims to bridge the gap between standard task management and custom, intelligent task processing workflows. The library is intentionally designed to be minimal, with few external dependencies, to ensure it is lightweight and easy to integrate.

## Compatibility

The API has been primarily tested with **Nextcloud Tasks**. However, it is designed to be compatible with any CalDAV server that supports VTODO components.

Testers and feedback for other CalDAV server implementations (e.g., Baïkal, Radicale, Synology Calendar) are highly welcome!

## Features

*   Connect to CalDAV servers with optional Nextcloud-specific URL adjustments.
*   Load task lists (calendars supporting VTODOs).
*   Load tasks from specified lists, parsing standard iCalendar properties.
*   Preserve and provide access to custom `X-` properties.
*   Create, update, and delete tasks (VTODOs) on the server.
*   Read-only mode for applications that need to prevent modifications.
*   Complete iCalendar (VTODO) roundtrip conversion.
*   CLI for basic task list inspection with JSON output support.
*   Debug mode for both CLI (interactive console) and API (PDB post-mortem).

## Installation

The CalDAV Tasks API can be installed directly from PyPI:

```bash
pip install caldav-tasks-api
```

Alternatively, you can install from source:

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd caldav-tasks-api
    ```
2.  Install dependencies (ensure you have `python>=3.8`):
    ```bash
    # Install the package and all dependencies:
    pip install .
    
    # For development with editable install:
    pip install -e .
    
    # For development with additional dev dependencies:
    pip install -e ".[dev]"
    ```


## Usage

Credentials for the CalDAV server can be provided as arguments to the CLI or `TasksAPI` constructor, or via the following environment variables:

*   `CALDAV_URL`: The full URL to your CalDAV server (e.g., `https://cloud.example.com/remote.php/dav`)
*   `CALDAV_USERNAME`: Your CalDAV username.
*   `CALDAV_PASSWORD`: Your CalDAV password.

### Command-Line Interface (CLI)

The CLI provides a simple way to interact with your CalDAV tasks. After installation, you can use the CLI in two ways:

1. **Using the installed command** (if installed via pip):
   ```bash
   caldav-tasks-api <command> [options]
   ```

2. **Using the module directly** (if running from source):
   ```bash
   python -m caldav_tasks_api <command> [options]
   ```

**Available Commands:**

*   `show_summary`: Connects to the server, loads task lists and tasks, and prints a summary.

**Examples:**

```bash
# Using command-line arguments for credentials (installed version)
caldav-tasks-api show_summary \
    --url "https://your.nextcloud.instance/remote.php/dav" \
    --username "your_user" \
    --password "your_password"

# Using environment variables (assuming they are set)
export CALDAV_URL="https://your.nextcloud.instance/remote.php/dav"
export CALDAV_USERNAME="your_user"
export CALDAV_PASSWORD="your_password"
caldav-tasks-api show_summary

# Show summary for specific task lists and enable debug console
caldav-tasks-api show_summary --list "Personal" --list "Work Project" --debug

# Output results in JSON format (useful for scripting)
caldav-tasks-api show_summary --json > tasks_data.json
```

**Common Options:**

*   `--url TEXT`: CalDAV server URL (or set CALDAV_URL env var)
*   `--username TEXT`: CalDAV username (or set CALDAV_USERNAME env var)
*   `--password TEXT`: CalDAV password (or set CALDAV_PASSWORD env var)
*   `--nextcloud-mode / --no-nextcloud-mode`: Adjust URL for Nextcloud (default: True)
*   `--list TEXT, -l TEXT`: Specify a task list name or UID to load (can use multiple times)
*   `--debug / --no-debug`: Enable interactive debugging console (default: False)
*   `--json / --no-json`: Output summary information in JSON format (default: False)

**Note:** All CLI operations are read-only by default. To modify tasks, use the Python API.

### Python API

The Python API offers more fine-grained control.

```python
from caldav_tasks_api import TasksAPI, TaskData
from caldav_tasks_api.utils.data import XProperties # For advanced X-Property handling

# Initialize the API
# Credentials can be passed directly or loaded from environment variables if not provided
try:
    api = TasksAPI(
        url="YOUR_CALDAV_URL", # or os.environ.get("CALDAV_URL")
        username="YOUR_USERNAME", # or os.environ.get("CALDAV_USERNAME")
        password="YOUR_PASSWORD", # or os.environ.get("CALDAV_PASSWORD")
        # nextcloud_mode=True,  # Default, adjust if not using Nextcloud
        # target_lists=["Personal", "Work"], # Optional: load only specific lists by name or UID
        # debug=True, # Optional: enable PDB for certain exceptions
        # read_only=True, # Optional: prevent any modifications to the server
    )
except ConnectionError as e:
    print(f"Failed to connect: {e}")
    exit()

# Load all task lists and their tasks from the server
api.load_remote_data()

# Access task lists and tasks
print("--- Task Lists ---")
for task_list in api.task_lists:
    print(f"List: '{task_list.name}' (UID: {task_list.uid})")
    print(f"  Tasks: {len(task_list.tasks)}")
    for task in task_list:  # TaskListData is iterable over its tasks
        status = "Completed" if task.completed else "Pending"
        print(f"    - [{status}] {task.text} (UID: {task.uid})")
        if task.due_date:
            print(f"      Due: {task.due_date}")
        if task.notes:
            print(f"      Notes: {task.notes[:50]}...")
        if task.x_properties: # Check if there are any X-properties
            print(f"      X-Properties:")
            for key, value in task.x_properties.items(): # Iterate raw X-properties
                print(f"        {key}: {value}")
            # Example of accessing a specific X-property via normalized attribute:
            # if hasattr(task.x_properties, 'tasks_org_order'):
            #     print(f"        Tasks.org Order: {task.x_properties.tasks_org_order}")


# Example: Add a new task
if api.task_lists:
    target_list_uid = api.task_lists[0].uid  # Get UID of the first list for this example
    
    new_task_data = TaskData(
        text="My important new task from API",
        notes="This is a detailed description.",
        list_uid=target_list_uid, # Good practice to set, though add_task uses its own list_uid param
        priority=5, # 1 (highest) to 9 (lowest), 0 (undefined)
        # x_properties={"X-CUSTOM-FIELD": "CustomValue"} # Can also pass a dict
    )
    # Or initialize XProperties directly
    new_task_data.x_properties["X-ANOTHER-PROP"] = "AnotherValue"


    try:
        created_task = api.add_task(new_task_data, target_list_uid)
        print(f"\n--- Created Task ---")
        print(f"Successfully created task: '{created_task.text}' with UID: {created_task.uid} in list {target_list_uid}")
        print(f"Server assigned created_at: {created_task.created_at}, changed_at: {created_task.changed_at}")

        # Example: Update the task we just created
        print(f"\n--- Updating Task ---")
        created_task.text = "Updated task title"
        created_task.priority = 1  # Higher priority
        updated_task = api.update_task(created_task)
        print(f"Successfully updated task: '{updated_task.text}' with UID: {updated_task.uid}")
        print(f"Server updated changed_at: {updated_task.changed_at}")

        # Example: Delete the task
        # print(f"\n--- Deleting Task ---")
        # if api.delete_task(created_task.uid, target_list_uid):
        #     print(f"Successfully deleted task UID: {created_task.uid}")
        # else:
        #     print(f"Failed to delete task UID: {created_task.uid}")

    except PermissionError as e:
        print(f"Permission error: {e}")  # Will occur in read-only mode
    except ValueError as e:
        print(f"Error adding/updating/deleting task: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
else:
    print("No task lists found to add a new task to.")

```

## Supported Operations & Testing Status

### Python API Features

| Feature                 | Status | Description                                                           |
| ----------------------- | ------ | --------------------------------------------------------------------- |
| Connect to Server       | ✅     | Connect using credentials via constructor or environment variables    |
| Fetch Task Lists        | ✅     | Load calendar lists that support tasks (VTODOs)                       |
| Fetch Tasks             | ✅     | Retrieve tasks with details (summary, due date, status, etc.)         |
| Create Task             | ✅     | Create new tasks on the server                                        |
| Update Task             | ✅     | Modify existing tasks                                                 |
| Delete Task             | ✅     | Remove tasks from the server                                          |
| Read-Only Mode          | ✅     | Prevent modifications to the server                                   |
| X-Property Handling     | ✅     | Support for custom task properties                                    |
| iCal Roundtrip          | ✅     | Consistent conversion to/from iCalendar format                        |
| Filter by Target Lists  | ✅     | Specify which lists to operate on                                     |
| Debug Mode              | ✅     | Enable PDB for certain exceptions                                     |

### Command-Line Interface Features

**Note: The CLI is always in read-only mode and cannot modify tasks on the server.**

| Feature                 | Status | Description                                                           |
| ----------------------- | ------ | --------------------------------------------------------------------- |
| Connect to Server       | ✅     | Connect using credentials via args or environment variables           |
| Fetch Task Lists        | ✅     | Load calendar lists that support tasks (VTODOs)                       |
| Fetch Tasks             | ✅     | Retrieve tasks with details (summary, due date, status, etc.)         |
| JSON Output             | ✅     | Format output as JSON for CLI commands                                |
| Filter by Target Lists  | ✅     | Specify which lists to operate on                                     |
| Debug Mode              | ✅     | Enable interactive console for troubleshooting                        |

## Handling of VTODO Properties (including X-Properties)

The library aims to parse standard VTODO (iCalendar task) properties into the fields of the `TaskData` dataclass (e.g., `summary`, `due`, `status`, `description`).

A key feature is the handling of non-standard properties, particularly those prefixed with `X-` (e.g., `X-APPLE-SORT-ORDER`, `X-TASKS-ORG-ORDER`, `X-NEXTCLOUD-SYSTEM-CALENDAR-ORDER`). These properties are often used by specific CalDAV clients or servers to store custom metadata.

*   **Preservation:** All `X-` properties encountered in a VTODO component are preserved.
*   **Storage:** They are stored in the `TaskData.x_properties` attribute. This attribute is an instance of the `XProperties` class.
*   **Access:** The `XProperties` class offers flexible access:
    *   **Dictionary-like access:** You can get/set properties using their original, raw keys (e.g., `task.x_properties['X-APPLE-SORT-ORDER']`).
    *   **Attribute-style access:** For convenience, `X-` properties can be accessed using normalized attribute names. The `X-` prefix is removed, and hyphens are converted to underscores (e.g., `task.x_properties.apple_sort_order`). This is case-insensitive on the query.
    *   **Containment checking:** The `in` operator is supported for case-insensitive key checking (e.g., `if 'X-APPLE-SORT-ORDER' in task.x_properties:`).
*   **Round-Tripping:** When a `TaskData` object is converted back to an iCalendar string (via `to_ical()`), all stored `X-` properties are included with their original keys. This ensures that custom data is not lost during iCal conversion.
*   **Dictionary conversion:** Both TaskData and TaskListData objects support conversion to dictionaries via the `to_dict()` method, which properly handles the conversion of X-properties.

This robust handling of `X-` properties is crucial for interoperability and for ensuring that application-specific metadata managed by clients like Tasks.org is not inadvertently discarded.

## Frequently Asked Questions (FAQ)

**Q: When does the library upload data to the CalDAV server? What triggers these uploads?**

A: Data uploads (i.e., changes to your tasks on the server) occur only when specific methods of the `TasksAPI` class are called. These methods interact directly with the CalDAV server to perform the requested operations. There is no automatic background synchronization or queuing of changes.

The primary methods that trigger uploads are:

*   **`TasksAPI.add_task(task_data, list_uid)`**: When you call this method, the new task (represented by `task_data`) is immediately created on the CalDAV server in the specified task list.
*   **`TasksAPI.update_task(task_data)`**: Calling this method will take the provided `task_data` (which should represent an existing task with its UID and your desired modifications) and save these changes to the corresponding task on the server. The task's `LAST-MODIFIED` timestamp is typically updated by the server.
*   **`TasksAPI.delete_task(task_uid, list_uid)`**: This method immediately sends a request to the CalDAV server to delete the task identified by `task_uid` from the specified `list_uid`.

The `TasksAPI.load_remote_data()` method, on the other hand, is responsible for *downloading* task lists and tasks from the server to your local `TasksAPI` instance. It does not upload any local changes.

In summary, uploads are explicit operations you initiate by calling `add_task`, `update_task`, or `delete_task`.

**Q: What is the read-only mode and when should I use it?**

A: The read-only mode (`read_only=True` when initializing `TasksAPI`) prevents any modifications to the server. When enabled:

* `add_task()`, `update_task()`, and `delete_task()` will raise a `PermissionError` if called
* All data retrieval methods function normally
* `load_remote_data()` works as usual to fetch tasks

This mode is useful for:

* Applications that need to display tasks but shouldn't modify them
* Preventing accidental modifications during development
* Creating monitoring or reporting tools that need task data but should never change it

To enable read-only mode, simply add the parameter when initializing the API:
```python
api = TasksAPI(
    url="YOUR_CALDAV_URL",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD",
    read_only=True
)
```

## Contributing

Contributions are welcome! If you'd like to contribute, please feel free to:

1.  Open an issue to discuss a bug, feature request, or an idea.
2.  Fork the repository and submit a pull request with your changes.

Please ensure your code follows the existing style and includes tests where appropriate.

## Acknowledgements

This project was developed with the assistance of [aider.chat](https://aider.chat), an AI pair programmer.
