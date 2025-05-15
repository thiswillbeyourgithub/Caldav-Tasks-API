FAQ
===

**Q: When does the library upload data to the CalDAV server? What triggers these uploads?**

A: Data uploads (i.e., changes to your tasks on the server) occur only when specific methods of the ``TasksAPI`` class are called. These methods interact directly with the CalDAV server to perform the requested operations. There is no automatic background synchronization or queuing of changes.

The primary methods that trigger uploads are:

*   **``TasksAPI.add_task(task_data, list_uid)``**: When you call this method, the new task (represented by ``task_data``) is immediately created on the CalDAV server in the specified task list.
*   **``TasksAPI.update_task(task_data)``**: Calling this method will take the provided ``task_data`` (which should represent an existing task with its UID and your desired modifications) and save these changes to the corresponding task on the server. The task's ``LAST-MODIFIED`` timestamp is typically updated by the server.
*   **``TasksAPI.delete_task(task_uid, list_uid)``**: This method immediately sends a request to the CalDAV server to delete the task identified by ``task_uid`` from the specified ``list_uid``.

The ``TasksAPI.load_remote_data()`` method, on the other hand, is responsible for *downloading* task lists and tasks from the server to your local ``TasksAPI`` instance. It does not upload any local changes.

In summary, uploads are explicit operations you initiate by calling ``add_task``, ``update_task``, or ``delete_task``.

**Q: What is the read-only mode and when should I use it?**

A: The read-only mode (``read_only=True`` when initializing ``TasksAPI``) prevents any modifications to the server. When enabled:

*   ``add_task()``, ``update_task()``, and ``delete_task()`` will raise a ``PermissionError`` if called.
*   All data retrieval methods function normally.
*   ``load_remote_data()`` works as usual to fetch tasks.

This mode is useful for:

*   Applications that need to display tasks but shouldn't modify them.
*   Preventing accidental modifications during development.
*   Creating monitoring or reporting tools that need task data but should never change it.

To enable read-only mode, simply add the parameter when initializing the API:

.. code-block:: python

   api = TasksAPI(
       url="YOUR_CALDAV_URL",
       username="YOUR_USERNAME",
       password="YOUR_PASSWORD",
       read_only=True
   )
