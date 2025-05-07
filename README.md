# CalDAV Tasks API

A Python library and command-line interface (CLI) for interacting with CalDAV task lists (VTODOs). This project provides tools to connect to a CalDAV server, fetch task lists and tasks, create new tasks, and delete existing ones.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE.md](LICENSE.md) file for details.

## Motivation and Purpose

This library was developed as a foundational component for integrating CalDAV task management with more advanced systems. The primary goal is to serve as a backbone for:

1.  Synchronizing tasks from applications like the excellent [Tasks.org Android app](https://f-droid.org/packages/org.tasks/).
2.  Enabling features such as smart task prioritization using ELO ranking, envisioned to work with a [Litoy-like setup](https://github.com/thiswillbeyourgithub/mini_LiTOY) (Note: link is a placeholder for the user's intended project).

By providing a robust Python interface to CalDAV tasks, this project aims to bridge the gap between standard task management and custom, intelligent task processing workflows.

## Compatibility

The API has been primarily tested with **Nextcloud Tasks**. However, it is designed to be compatible with any CalDAV server that supports VTODO components.

Testers and feedback for other CalDAV server implementations (e.g., Baïkal, Radicale, Synology Calendar) are highly welcome!

## Features

*   Connect to CalDAV servers with optional Nextcloud-specific URL adjustments.
*   Load task lists (calendars supporting VTODOs).
*   Load tasks from specified lists, parsing standard iCalendar properties.
*   Preserve and provide access to custom `X-` properties.
*   Create new tasks (VTODOs) on the server.
*   Delete tasks from the server.
*   CLI for basic task list inspection.
*   Debug mode for both CLI (interactive console) and API (PDB post-mortem).

## Installation

Currently, the project is not yet packaged for PyPI. To use it:

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd caldav-tasks-api
    ```
2.  Install dependencies (ensure you have `python>=3.8`):
    ```bash
    pip install -r requirements.txt 
    # Or, for development:
    pip install -e .
    ```
    (Note: A `requirements.txt` might need to be generated or dependencies listed in `setup.py` should be sufficient for `pip install .`)


## Usage

Credentials for the CalDAV server can be provided as arguments to the CLI or `TasksAPI` constructor, or via the following environment variables:

*   `CALDAV_URL`: The full URL to your CalDAV server (e.g., `https://cloud.example.com/remote.php/dav`)
*   `CALDAV_USERNAME`: Your CalDAV username.
*   `CALDAV_PASSWORD`: Your CalDAV password.

### Command-Line Interface (CLI)

The CLI provides a simple way to interact with your CalDAV tasks. The main entry point is `caldav_tasks_api.__main__`.

**Basic Invocation:**

```bash
python -m caldav_tasks_api <command> [options]
```

**Available Commands:**

*   `show_summary`: Connects to the server, loads task lists and tasks, and prints a summary.

**Example:**

```bash
# Using command-line arguments for credentials
python -m caldav_tasks_api show_summary \
    --url "https://your.nextcloud.instance/remote.php/dav" \
    --username "your_user" \
    --password "your_password"

# Using environment variables (assuming they are set)
export CALDAV_URL="https://your.nextcloud.instance/remote.php/dav"
export CALDAV_USERNAME="your_user"
export CALDAV_PASSWORD="your_password"
python -m caldav_tasks_api show_summary

# Show summary for specific task lists and enable debug console
python -m caldav_tasks_api show_summary --list "Personal" "Work Project" --debug
```

**Common Options:**

*   `--url TEXT`: CalDAV server URL.
*   `--username TEXT`: CalDAV username.
*   `--password TEXT`: CalDAV password.
*   `--nextcloud-mode / --no-nextcloud-mode`: Adjust URL for Nextcloud (default: True).
*   `--list TEXT ...`: Specify one or more task list names or UIDs to load.
*   `--debug / --no-debug`: Enable PDB post-mortem debugging and interactive console (default: False).

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
        # debug=True # Optional: enable PDB for certain exceptions
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
    # new_task_data.x_properties = XProperties({"X-ANOTHER-PROP": "AnotherValue"})


    try:
        created_task = api.add_task(new_task_data, target_list_uid)
        print(f"\n--- Created Task ---")
        print(f"Successfully created task: '{created_task.text}' with UID: {created_task.uid} in list {target_list_uid}")
        print(f"Server assigned created_at: {created_task.created_at}, changed_at: {created_task.changed_at}")

        # Example: Delete the task just created
        # print(f"\n--- Deleting Task ---")
        # if api.delete_task(created_task.uid, target_list_uid):
        #     print(f"Successfully deleted task UID: {created_task.uid}")
        # else:
        #     print(f"Failed to delete task UID: {created_task.uid}")

    except ValueError as e:
        print(f"Error adding/deleting task: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
else:
    print("No task lists found to add a new task to.")

```

## Supported Operations & Testing Status

| Feature                 | CLI Support & Tested                      | Python API Support & Tested           | Remarks                                                                                                                               |
| ----------------------- | ----------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Connect to Server       | Yes (Implicit in `show_summary`)          | Yes (Tested via `conftest.py` fixtures)             | Credentials via args or env vars (`CALDAV_URL`, `CALDAV_USERNAME`, `CALDAV_PASSWORD`).                                                |
| Fetch Task Lists        | Yes (`show_summary` command)              | Yes (Tested in `test_tasks_api.py::test_fetch_task_lists`) | Loads names, UIDs, and associated tasks.                                                                                      |
| Fetch Tasks             | Yes (Displayed by `show_summary` command) | Yes (Tested in `test_tasks_api.py::test_find_tasks_in_lists`) | Tasks are loaded as part of `TaskListData.tasks`. Includes details like summary, due date, status, X-properties, etc.             |
| Create Task             | No (Planned for future CLI commands)      | Yes (Tested in `test_tasks_api.py::test_create_and_delete_task`, `test_create_single_task`) | `TasksAPI.add_task()` creates a new VTODO on the server.                                                              |
| Delete Task             | No (Planned for future CLI commands)      | Yes (Tested in `test_tasks_api.py::test_create_and_delete_task`) | `TasksAPI.delete_task()` removes a VTODO by its UID from a specified list.                                                          |
| Update Task             | No                                        | Partial (Not directly tested as a dedicated API method) | No high-level `update_task()` method. Updates require fetching a `caldav.Todo` object, modifying its `data` with `TaskData.to_ical()`, and calling `save()`. This is an advanced operation. |
| Filter by Target Lists  | Yes (`--list` option for `show_summary`)  | Yes (Constructor argument `target_lists`) | Allows specifying list names or UIDs to operate on during initialization.                                                                                   |
| Debug Mode              | Yes (`--debug` option for `show_summary`) | Yes (Constructor argument `debug`)      | CLI: Enables PDB post-mortem and interactive console. API: Enables PDB for certain exceptions during development.                                        |

## Handling of VTODO Properties (including X-Properties)

The library aims to parse standard VTODO (iCalendar task) properties into the fields of the `TaskData` dataclass (e.g., `summary`, `due`, `status`, `description`).

A key feature is the handling of non-standard properties, particularly those prefixed with `X-` (e.g., `X-APPLE-SORT-ORDER`, `X-TASKS-ORG-ORDER`, `X-NEXTCLOUD-SYSTEM-CALENDAR-ORDER`). These properties are often used by specific CalDAV clients or servers to store custom metadata.

*   **Preservation:** All `X-` properties encountered in a VTODO component are preserved.
*   **Storage:** They are stored in the `TaskData.x_properties` attribute. This attribute is an instance of the `XProperties` class.
*   **Access:** The `XProperties` class offers flexible access:
    *   **Dictionary-like access:** You can get/set properties using their original, raw keys (e.g., `task.x_properties['X-APPLE-SORT-ORDER']`).
    *   **Attribute-style access:** For convenience, `X-` properties can be accessed using normalized attribute names. The `X-` prefix is removed, and hyphens are converted to underscores (e.g., `task.x_properties.apple_sort_order`). This is case-insensitive on the query.
*   **Round-Tripping:** When a `TaskData` object is converted back to an iCalendar string (via `to_ical()`), all stored `X-` properties are included with their original keys. This ensures that custom data is not lost if a task is read, potentially modified (though full update logic is advanced), and then intended to be saved back.

This robust handling of `X-` properties is crucial for interoperability and for ensuring that application-specific metadata managed by clients like Tasks.org is not inadvertently discarded.

## Contributing

Contributions are welcome! If you'd like to contribute, please feel free to:

1.  Open an issue to discuss a bug, feature request, or an idea.
2.  Fork the repository and submit a pull request with your changes.

Please ensure your code follows the existing style and includes tests where appropriate.

## Acknowledgements

This project was developed with the assistance of [aider.chat](https://aider.chat), an AI pair programmer.
