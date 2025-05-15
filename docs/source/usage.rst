Usage
=====

Credentials for the CalDAV server can be provided as arguments to the CLI or ``TasksAPI`` constructor, or via the following environment variables:

*   ``CALDAV_TASKS_API_URL``: The full URL to your CalDAV server (e.g., ``https://cloud.example.com/remote.php/dav``)
*   ``CALDAV_TASKS_API_USERNAME``: Your CalDAV username.
*   ``CALDAV_TASKS_API_PASSWORD``: Your CalDAV password.

Command-Line Interface (CLI)
----------------------------

The CLI provides a simple way to interact with your CalDAV tasks. After installation, you can use the CLI in two ways:

1. **Using the installed command** (if installed via pip):

   .. code-block:: bash

      caldav-tasks-api <command> [options]

2. **Using the module directly** (if running from source):

   .. code-block:: bash

      python -m caldav_tasks_api <command> [options]

**Available Commands:**

*   ``show_summary``: Connects to the server, loads task lists and tasks, and prints a summary.
*   ``add-task``: Adds a new task to a specified task list.
*   ``list-latest-tasks``: Lists the most recently created, non-completed tasks.
*   ``list-lists``: Prints a JSON list of task lists (name and UID).

**Examples:**

.. code-block:: bash

   # Using command-line arguments for credentials (installed version)
   caldav-tasks-api show_summary \
       --url "https://your.nextcloud.instance/remote.php/dav" \
       --username "your_user" \
       --password "your_password"

   # Using environment variables (assuming they are set)
   export CALDAV_TASKS_API_URL="https://your.nextcloud.instance/remote.php/dav"
   export CALDAV_TASKS_API_USERNAME="your_user"
   export CALDAV_TASKS_API_PASSWORD="your_password"
   caldav-tasks-api show_summary

   # Show summary for specific task lists and enable debug console
   caldav-tasks-api show_summary --list "Personal" --list "Work Project" --debug

   # Output results in JSON format (useful for scripting)
   caldav-tasks-api show_summary --json > tasks_data.json

   # Add a new task (using environment variables for credentials)
   # Ensure CALDAV_TASKS_API_DEFAULT_LIST_UID is set or provide --list-uid
   caldav-tasks-api add-task --summary "My new task from CLI" --read-write

   # List the latest 5 tasks from a specific list (output is JSON)
   caldav-tasks-api list-latest-tasks --list-uid "your-list-uid-here" --limit 5 > latest_tasks.json

   # List all available task lists (output is JSON)
   caldav-tasks-api list-lists > all_lists.json

**Common Options:**

*   ``--url TEXT``: CalDAV server URL (or set ``CALDAV_TASKS_API_URL`` env var)
*   ``--username TEXT``: CalDAV username (or set ``CALDAV_TASKS_API_USERNAME`` env var)
*   ``--password TEXT``: CalDAV password (or set ``CALDAV_TASKS_API_PASSWORD`` env var)
*   ``--nextcloud-mode`` / ``--no-nextcloud-mode``: Adjust URL for Nextcloud (default: True)
*   ``--debug`` / ``--no-debug``: Enable interactive debugging console (default: False)
*   ``--read-only`` / ``--read-write``: Operate in read-only mode (default for ``show_summary``, ``list-latest-tasks``, ``list-lists``) or allow modifications (required for ``add-task``). This flag controls if the underlying API instance is initialized in read-only mode.

**Specific command options:**

*   ``show_summary``:
    *   ``--list TEXT, -l TEXT``: Specify a task list name or UID to load (can use multiple times)
    *   ``--json`` / ``--no-json``: Output summary information in JSON format (default: False)
*   ``add-task``:
    *   ``--list-uid TEXT``: UID of the task list (or ``CALDAV_TASKS_API_DEFAULT_LIST_UID`` env var). Mandatory if env var not set.
    *   ``--summary TEXT``: Summary/text of the task (required).
*   ``list-latest-tasks``:
    *   ``--list-uid TEXT``: UID of the task list to filter from (or ``CALDAV_TASKS_API_DEFAULT_LIST_UID`` env var).
    *   ``--limit INTEGER``: Maximum number of tasks to return (default: 10). Output is always JSON.
*   ``list-lists``: Output is always JSON.

.. note::

   Most CLI operations that only read data default to read-only mode. For operations that modify data, like ``add-task``, the ``--read-write`` flag must be explicitly used if you wish to make changes on the server (or ensure the API defaults to read-write if that behavior changes). The ``add-task`` command itself will implicitly use ``read_only=False`` when initializing its API instance, but the global ``--read-write`` or ``--read-only`` flag passed to the ``caldav-tasks-api`` group can influence this. It's best practice to be explicit with ``--read-write`` for modification commands if the global default is read-only.

Python API
----------

The Python API offers more fine-grained control. An example of its usage can be found in the documentation under :doc:`examples`.

.. note::
   For a detailed reference of the Python API classes and methods, please see the :doc:`api` documentation.
