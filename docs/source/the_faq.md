FAQ
===

## When does the library upload data to the CalDAV server? What triggers these uploads?

Data uploads (i.e., changes to your tasks on the server) occur only when specific methods of the `TasksAPI` class are called. These methods interact directly with the CalDAV server to perform the requested operations. There is no automatic background synchronization or queuing of changes.

The primary methods that trigger uploads are:

*   **`TasksAPI.add_task(task_data, list_uid)`**: When you call this method, the new task (represented by `task_data`) is immediately created on the CalDAV server in the specified task list.
*   **`TasksAPI.update_task(task_data)`**: Calling this method will take the provided `task_data` (which should represent an existing task with its UID and your desired modifications) and save these changes to the corresponding task on the server. The task's `LAST-MODIFIED` timestamp is typically updated by the server.
*   **`TasksAPI.delete_task(task_uid, list_uid)`**: This method immediately sends a request to the CalDAV server to delete the task identified by `task_uid` from the specified `list_uid`.

The `TasksAPI.load_remote_data()` method, on the other hand, is responsible for *downloading* task lists and tasks from the server to your local `TasksAPI` instance. It does not upload any local changes.

In summary, uploads are explicit operations you initiate by calling `add_task`, `update_task`, or `delete_task`.

## What is the read-only mode and when should I use it?

The read-only mode (`read_only=True` when initializing `TasksAPI`) prevents any modifications to the server. When enabled:

*   `add_task()`, `update_task()`, and `delete_task()` will raise a `PermissionError` if called.
*   All data retrieval methods function normally.
*   `load_remote_data()` works as usual to fetch tasks.

This mode is useful for:

*   Applications that need to display tasks but shouldn't modify them.
*   Preventing accidental modifications during development.
*   Creating monitoring or reporting tools that need task data but should never change it.

To enable read-only mode, simply add the parameter when initializing the API:

```python
api = TasksAPI(
    url="YOUR_CALDAV_URL",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD",
    read_only=True
)
```

## How are VTODO properties and X-Properties handled?

The library aims to parse standard VTODO (iCalendar task) properties into the fields of the `TaskData` dataclass (e.g., `summary`, `due`, `status`, `description`).

A key feature is the handling of non-standard properties, particularly those prefixed with `X-` (e.g., `X-APPLE-SORT-ORDER`, `X-TASKS-ORG-ORDER`, `X-NEXTCLOUD-SYSTEM-CALENDAR-ORDER`). These properties are often used by specific CalDAV clients or servers to store custom metadata.

*   **Preservation:** All `X-` properties encountered in a VTODO component are preserved.
*   **Storage:** They are stored in the `TaskData.x_properties` attribute. This attribute is an instance of the `XProperties` class.
*   **Access:** The `XProperties` class offers flexible access:
    *   **Dictionary-like access:** You can get/set properties using their original, raw keys (e.g., `task.x_properties['X-APPLE-SORT-ORDER']`).
    *   **Attribute-style access:** For convenience, `X-` properties can be accessed using normalized attribute names. The `X-` prefix is removed, and hyphens are converted to underscores (e.g., `task.x_properties.apple_sort_order`). This is case-insensitive on the query.
    *   **Containment checking:** The `in` operator is supported for case-insensitive key checking (e.g., `if 'X-APPLE-SORT-ORDER' in task.x_properties:`).
*   **Round-Tripping:** When a `TaskData` object is converted back to an iCalendar string (via `to_ical()`), all stored `X-` properties are included with their original keys. This aims to preserve custom data during iCal conversion. (Note: values containing certain iCalendar special characters like backslashes (`\`) or double quotes (`"`) may require additional escaping beyond the current implementation for perfect round-tripping with all CalDAV servers/clients, as per RFC 5545.)
*   **Dictionary conversion:** Both TaskData and TaskListData objects support conversion to dictionaries via the `to_dict()` method, which properly handles the conversion of X-properties.

This robust handling of `X-` properties is crucial for interoperability and for ensuring that application-specific metadata managed by clients like Tasks.org is not inadvertently discarded.

