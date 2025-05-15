Tests
=====

The test suite for `caldav-tasks-api` ensures the reliability and
correctness of its core functionalities. Tests are implemented using
`pytest` and interact with a live CalDAV server, requiring specific
environment variables for credentials and server details.

The table below provides a summary of the features covered by the automated tests. A ✅ indicates that the feature is covered by one or more tests.

Test Coverage Summary
---------------------

| Area     | Feature Tested                                      | Test Function(s)                                 | Status |
|----------|-----------------------------------------------------|--------------------------------------------------|--------|
| TasksAPI | Fetching & populating task lists                    | `test_fetch_task_lists`                          |   ✅   |
| TasksAPI | Finding tasks in lists                              | `test_find_tasks_in_lists`                       |   ✅   |
| TasksAPI | Create and delete task                              | `test_create_and_delete_task`                    |   ✅   |
| TasksAPI | Create single task                                  | `test_create_single_task`                        |   ✅   |
| TasksAPI | Create and rename/update task                       | `test_create_and_rename_task`                    |   ✅   |
| TasksAPI | Create, update X-property, delete task              | `test_create_update_xprop_delete_task`           |   ✅   |
| TasksAPI | Add task attempt fails (read-only mode)             | `test_add_task_in_read_only_mode`                |   ✅   |
| TasksAPI | Delete task attempt fails (read-only mode)          | `test_delete_task_in_read_only_mode`             |   ✅   |
| TasksAPI | Update task attempt fails (read-only mode)          | `test_update_task_in_read_only_mode`             |   ✅   |
| TasksAPI | `TaskData.to_dict()` conversion                     | `test_task_to_dict`                              |   ✅   |
| TasksAPI | `TaskData` iCal roundtrip (to_ical/from_ical)       | `test_task_ical_roundtrip`                       |   ✅   |
| TasksAPI | Parent-child task relationships                     | `test_task_parent_child_relationships`           |   ✅   |
| CLI      | `show-summary --json` command runs successfully     | `test_cli_show_summary_json_runs_successfully`   |   ✅   |

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

```bash
pytest
```

