

TODO
=====


Tests
=====

The test suite for `caldav-tasks-api` ensures the reliability and
correctness of its core functionalities. Tests are implemented using
`pytest` and interact with a live CalDAV server, requiring specific
environment variables for credentials and server details.

Key Tested Features
-------------------

The following features are covered by automated tests:

**Python API (`TasksAPI`):**

*   **Connection & Data Fetching:**
    *   Fetching and populating task lists (`test_fetch_task_lists`).
    *   Finding and validating tasks within fetched lists
(`test_find_tasks_in_lists`).

*   **Task CRUD Operations:**
    *   Creating a new task and subsequently deleting it
(`test_create_and_delete_task`).
    *   Creating a single task without immediate deletion
(`test_create_single_task`).
    *   Creating a task, renaming (updating) it, and verifying the change
(`test_create_and_rename_task`).
    *   Creating a task, adding/updating an X-property, and then deleting
the task (`test_create_update_xprop_delete_task`).

*   **Read-Only Mode:**
    *   Attempting to add a task in read-only mode correctly raises
`PermissionError` (`test_add_task_in_read_only_mode`).
    *   Attempting to delete a task in read-only mode correctly raises
`PermissionError` (`test_delete_task_in_read_only_mode`).
    *   Attempting to update a task in read-only mode correctly raises
`PermissionError` (`test_update_task_in_read_only_mode`).

*   **Data Handling & Conversion:**
    *   `TaskData.to_dict()` method correctly converts task objects to
dictionaries (`test_task_to_dict`).
    *   `TaskData.to_ical()` and `TaskData.from_ical()` methods ensure
correct iCalendar roundtrip conversion for task properties, including
X-properties (`test_task_ical_roundtrip`).

*   **Task Relationships:**
    *   Establishing and retrieving parent-child relationships between
tasks, including verification of `parent_task` and `child_tasks` properties
after server interaction and data reload
(`test_task_parent_child_relationships`).

**Command-Line Interface (CLI):**

*   The `show-summary --json` command runs successfully and produces output,
indicating basic CLI functionality and environment variable usage
(`test_cli_show_summary_json_runs_successfully`).

Setup and Fixtures
------------------

Tests rely on several `pytest` fixtures defined in `tests/conftest.py`:

*   `caldav_credentials`: Provides CalDAV server URL, username, and password
from environment variables.
*   `tasks_api_instance`: Provides an initialized `TasksAPI` instance
connected to the server with data pre-loaded.
*   `read_only_tasks_api_instance`: Provides an initialized `TasksAPI`
instance in read-only mode.
*   `test_list_name`: Provides the name of a specific CalDAV task list
designated for tests involving task creation, modification, and deletion.

Running Tests
-------------

To run the tests, ensure you have the necessary environment variables set
(see `tests/conftest.py` for details) and execute `pytest` from the root of
the project directory.

.. code-block:: bash

   pytest

This project uses `aider.chat` for development assistance.
