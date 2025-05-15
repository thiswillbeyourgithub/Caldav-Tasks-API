"""
CLI entry point for the Tasks API.

This module uses the `click` library to expose functionalities of the TasksAPI
as command-line interface commands.

Can be run directly using:
    python -m caldav_tasks_api
"""

import os
import json
import code  # For interactive debugging
from typing import List, Optional
import os  # Added for environment variable access

import click
from loguru import logger

from caldav_tasks_api import TasksAPI
from caldav_tasks_api.utils.data import TaskData  # Import TaskData


def get_api(
    url: Optional[str],
    username: Optional[str],
    password: Optional[str],
    nextcloud_mode: bool,
    debug: bool,
    target_lists: Optional[List[str]],
    read_only: bool,
) -> TasksAPI:
    """
    Initializes and returns the TasksAPI instance.
    Validates credentials and raises appropriate errors.
    """
    # Get credentials from args or environment
    url = url or os.environ.get("CALDAV_TASKS_API_URL")
    username = username or os.environ.get("CALDAV_TASKS_API_USERNAME")
    password = password or os.environ.get("CALDAV_TASKS_API_PASSWORD")

    # Validate credentials
    if not url:
        logger.error("CalDAV server URL not provided.")
        raise click.UsageError(
            "CalDAV server URL must be provided via --url option or CALDAV_URL environment variable."
        )
    if not username:
        logger.error("CalDAV username not provided.")
        raise click.UsageError(
            "CalDAV username must be provided via --username option or CALDAV_USERNAME environment variable."
        )
    if not password:
        logger.error("CalDAV password not provided.")
        raise click.UsageError(
            "CalDAV password must be provided via --password option or CALDAV_PASSWORD environment variable."
        )

    logger.debug("Credentials validated successfully.")
    logger.info(f"Initializing TasksAPI for CalDAV server at: {url}")

    return TasksAPI(
        url=url,
        username=username,
        password=password,
        nextcloud_mode=nextcloud_mode,
        debug=debug,
        target_lists=target_lists,
        read_only=read_only,
    )


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli():
    """CalDAV Tasks API - Command-line interface for interacting with CalDAV task servers."""
    pass


@cli.command()
@click.option("--url", help="CalDAV server URL (or set CALDAV_URL env var)")
@click.option("--username", help="CalDAV username (or set CALDAV_USERNAME env var)")
@click.option("--password", help="CalDAV password (or set CALDAV_PASSWORD env var)")
@click.option(
    "--nextcloud-mode/--no-nextcloud-mode",
    default=True,
    help="Adjust URL for Nextcloud specific path [default: enabled]",
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable debug mode with interactive console [default: disabled]",
)
@click.option(
    "--list",
    "-l",
    multiple=True,
    help="Filter by task list name or UID (can use multiple times)",
)
@click.option(
    "--json/--no-json",
    "json_output",
    default=False,
    help="Output summary as JSON [default: disabled]",
)
@click.option(
    "--read-only/--read-write",
    "read_only_flag",
    default=True,
    help="Operate in read-only mode (default) or allow modifications [default: read-only]",
)
def show_summary(
    url, username, password, nextcloud_mode, debug, list, json_output, read_only_flag
):
    """Connect to CalDAV server and show a summary of all task lists and tasks."""
    target_lists = list if list else None
    logger.debug(
        f"CLI initialized with url: {'***' if url else 'from env'}, "
        f"user: {username or 'from env'}, nc_mode: {nextcloud_mode}, "
        f"debug: {debug}, lists: {target_lists}, json: {json_output}, read_only: {read_only_flag}"
    )

    try:
        api = get_api(
            url,
            username,
            password,
            nextcloud_mode,
            debug,
            target_lists,
            read_only=read_only_flag,
        )
        logger.info("Loading remote tasks...")
        api.load_remote_data()

        if json_output:
            # Prepare data for JSON output
            output_data = [tl.to_dict() for tl in api.task_lists]
            click.echo(json.dumps(output_data, ensure_ascii=False, indent=2))
            return  # Exit after printing JSON

        # Standard summary logging
        click.echo("--- Summary ---")
        click.echo(f"Total Task Lists loaded: {len(api.task_lists)}")
        total_tasks_count = 0

        for tl in api.task_lists:
            click.echo(
                f"  List: '{tl.name}' (UID: {tl.uid}, Color: {tl.color}) - Tasks: {len(tl.tasks)}"
            )
            total_tasks_count += len(tl.tasks)

        click.echo(f"Total Tasks loaded: {total_tasks_count}")

        if debug:
            click.echo(
                "Debug mode: Starting interactive console. API available as 'api'."
            )
            click.echo("Variables available: api, locals()")
            # Expose api to the interactive console
            _globals = globals().copy()
            _locals = locals().copy()
            _globals.update(_locals)  # Make local variables accessible
            code.interact(local=_globals)

    except click.UsageError as ue:
        click.echo(f"Configuration error: {ue}", err=True)
        raise click.Abort()
    except ConnectionError as ce:
        click.echo(f"Connection failed: {ce}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command(name="list-latest-tasks")
@click.option("--url", help="CalDAV server URL (or set CALDAV_URL env var)")
@click.option("--username", help="CalDAV username (or set CALDAV_USERNAME env var)")
@click.option("--password", help="CalDAV password (or set CALDAV_PASSWORD env var)")
@click.option(
    "--nextcloud-mode/--no-nextcloud-mode",
    default=True,
    help="Adjust URL for Nextcloud specific path [default: enabled]",
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable debug mode with interactive console [default: disabled]",
)
@click.option(
    "--list-uid",
    default=None,
    envvar="CALDAV_TASKS_API_DEFAULT_LIST_UID",
    help="UID of the task list to filter tasks from. Defaults to CALDAV_TASKS_API_DEFAULT_LIST_UID env var if set (optional).",
)
@click.option(
    "--limit",
    default=10,
    type=int,
    help="Maximum number of tasks to return [default: 10].",
)
def list_latest_tasks(url, username, password, nextcloud_mode, debug, list_uid, limit):
    """
    List the most recently created, non-completed tasks, sorted by creation_date.
    Output is in JSON format.
    """
    logger.debug(
        f"CLI list-latest-tasks initiated with url: {'***' if url else 'from env'}, "
        f"user: {username or 'from env'}, nc_mode: {nextcloud_mode}, "
        f"debug: {debug}, list_uid: {list_uid}, limit: {limit}"
    )

    try:
        # This command is inherently read-only.
        # target_lists can be set to [list_uid] if list_uid is provided,
        # or None to fetch all lists and then filter.
        # Fetching all might be simpler if TaskData doesn't always have list_uid readily after parsing.
        # However, TasksAPI constructor takes target_lists to filter calendars.
        target_lists_filter = [list_uid] if list_uid else None
        api = get_api(
            url,
            username,
            password,
            nextcloud_mode,
            debug,
            target_lists=target_lists_filter,
            read_only=True,
        )

        logger.info("Loading remote tasks...")
        api.load_remote_data()

        all_relevant_tasks: List[TaskData] = []
        for task_list in api.task_lists:
            # If list_uid was specified for filtering at API level, only that list will be here.
            # If list_uid was specified but not for API level (e.g. target_lists=None initially),
            # we'd filter here. Current setup filters at API level via target_lists_filter.
            # If no list_uid specified, all lists (respecting target_lists_filter) are processed.
            if (
                list_uid and task_list.uid != list_uid
            ):  # Defensive check if target_lists_filter wasn't perfect
                continue

            for task in task_list.tasks:
                if not task.completed:
                    all_relevant_tasks.append(task)

        logger.debug(f"Found {len(all_relevant_tasks)} non-completed tasks initially.")

        # Sort tasks by created_at (descending, most recent first)
        # Helper to parse created_at string to datetime for sorting
        def get_task_sort_key(t: TaskData):
            from datetime import datetime, timezone  # Import here if not at top level

            if t.created_at:
                try:
                    # Assuming created_at is in ISO 8601 format like 'YYYYMMDDTHHMMSSZ'
                    return datetime.strptime(t.created_at, "%Y%m%dT%H%M%SZ").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    logger.warning(
                        f"Invalid created_at format '{t.created_at}' for task UID {t.uid}. Treating as very old."
                    )
                    return datetime.min.replace(
                        tzinfo=timezone.utc
                    )  # Earliest possible datetime
            return datetime.min.replace(
                tzinfo=timezone.utc
            )  # Tasks without created_at are considered oldest

        sorted_tasks = sorted(all_relevant_tasks, key=get_task_sort_key, reverse=True)

        # Apply limit
        limited_tasks = sorted_tasks[:limit]
        logger.info(
            f"Returning {len(limited_tasks)} tasks after sorting and applying limit of {limit}."
        )

        # Reversing the list here, as requested.
        # This implies that the previous state of limited_tasks (derived from a sort with reverse=True)
        # was effectively oldest-first if the goal is to now see latest-first after this reversal.
        limited_tasks.reverse()

        # Prepare data for JSON output
        output_data = [task.to_dict() for task in limited_tasks]
        click.echo(json.dumps(output_data, ensure_ascii=False, indent=2))

        if debug:
            click.echo(
                "Debug mode: Starting interactive console. API, tasks available as 'api', 'output_data'."
            )
            _globals = globals().copy()
            _locals = locals().copy()
            _globals.update(_locals)
            code.interact(local=_globals)

    except click.UsageError as ue:
        click.echo(f"Configuration error: {ue}", err=True)
        raise click.Abort()
    except ConnectionError as ce:
        click.echo(f"Connection failed: {ce}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("--url", help="CalDAV server URL (or set CALDAV_URL env var)")
@click.option("--username", help="CalDAV username (or set CALDAV_USERNAME env var)")
@click.option("--password", help="CalDAV password (or set CALDAV_PASSWORD env var)")
@click.option(
    "--nextcloud-mode/--no-nextcloud-mode",
    default=True,
    help="Adjust URL for Nextcloud specific path [default: enabled]",
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable debug mode with interactive console [default: disabled]",
)
@click.option(
    "--list-uid",
    required=False,
    envvar="CALDAV_TASKS_API_DEFAULT_LIST_UID",
    help="UID of the task list to add the task to. Defaults to CALDAV_TASKS_API_DEFAULT_LIST_UID env var if set. Mandatory if env var not set.",
)
@click.option("--summary", required=True, help="Summary/text of the task.")
# Add more options for other TaskData fields as needed (e.g., --notes, --due-date)
def add_task(
    url, username, password, nextcloud_mode, debug, list_uid, summary
):  # list_uid is specific to this command
    """Add a new task to a specified task list."""
    logger.debug(
        f"CLI add-task initiated with url: {'***' if url else 'from env'}, "
        f"user: {username or 'from env'}, nc_mode: {nextcloud_mode}, "
        f"debug: {debug}, list_uid: {list_uid}, summary: {summary}"
    )

    try:
        # For adding tasks, read_only must be False.
        # target_lists is not strictly needed for adding a single task if list_uid is known,
        # but get_api expects it. We pass None as we are directly using list_uid.
        api = get_api(
            url,
            username,
            password,
            nextcloud_mode,
            debug,
            target_lists=None,
            read_only=False,
        )

        # Initialize TaskData.list_uid with an empty string if list_uid from CLI/env is None,
        # as TaskData.list_uid expects a string. The api.add_task method will handle final resolution.
        task_data_list_uid = list_uid if list_uid is not None else ""
        task_data = TaskData(
            text=summary,
            list_uid=task_data_list_uid,
            # Initialize other fields of TaskData as needed, e.g. notes, due_date
            # For example:
            # notes="Generated via CLI",
        )

        # Pass the original list_uid from CLI/env (which could be None) to api.add_task.
        # The api.add_task method will resolve the definitive list_uid using its precedence logic.
        logger.info(
            f"Attempting to add task '{summary}' (CLI list_uid: '{list_uid}')..."
        )
        created_task = api.add_task(task_data, list_uid)

        click.echo(f"Task '{created_task.text}' added successfully!")
        click.echo(f"  UID: {created_task.uid}")
        click.echo(f"  List UID: {created_task.list_uid}")
        if created_task.synced:
            click.echo("  Status: Synced with server.")
        else:
            click.echo(
                "  Status: Not synced (or sync status unknown) with server.", err=True
            )

        if debug:
            click.echo(
                "Debug mode: Starting interactive console. API and task available as 'api', 'created_task'."
            )
            _globals = globals().copy()
            _locals = locals().copy()
            _globals.update(_locals)
            code.interact(local=_globals)

    except click.UsageError as ue:
        click.echo(f"Configuration error: {ue}", err=True)
        raise click.Abort()
    except ConnectionError as ce:
        click.echo(f"Connection failed: {ce}", err=True)
        raise click.Abort()
    except PermissionError as pe:
        click.echo(f"Permission error: {pe}", err=True)
        raise click.Abort()
    except ValueError as ve:
        click.echo(f"Value error: {ve}", err=True)  # e.g. list not found
        raise click.Abort()
    except Exception as e:
        logger.exception(f"An unexpected error occurred while adding task: {e}")
        click.echo(f"Error adding task: {e}", err=True)
        raise click.Abort()


@cli.command(name="list-lists")
@click.option("--url", help="CalDAV server URL (or set CALDAV_URL env var)")
@click.option("--username", help="CalDAV username (or set CALDAV_USERNAME env var)")
@click.option("--password", help="CalDAV password (or set CALDAV_PASSWORD env var)")
@click.option(
    "--nextcloud-mode/--no-nextcloud-mode",
    default=True,
    help="Adjust URL for Nextcloud specific path [default: enabled]",
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable debug mode with interactive console [default: disabled]",
)
# target_lists is implicitly all lists for this command
def list_lists(url, username, password, nextcloud_mode, debug):
    """Connect to CalDAV server and print a JSON list of task lists (name and UID)."""
    logger.debug(
        f"CLI list-lists initiated with url: {'***' if url else 'from env'}, "
        f"user: {username or 'from env'}, nc_mode: {nextcloud_mode}, "
        f"debug: {debug}"
    )

    try:
        # This command is inherently read-only.
        # No specific target_lists, we want all lists.
        api = get_api(
            url,
            username,
            password,
            nextcloud_mode,
            debug,
            target_lists=None,
            read_only=True,
        )
        logger.info("Loading remote task lists...")
        api.load_remote_data()  # This loads all lists and their tasks

        # Prepare data for JSON output: a list of dicts with name and UID
        output_data = [{"name": tl.name, "uid": tl.uid} for tl in api.task_lists]
        click.echo(json.dumps(output_data, ensure_ascii=False, indent=2))

        if debug:
            click.echo(
                "Debug mode: Starting interactive console. API available as 'api'."
            )
            click.echo("Variables available: api, output_data, locals()")
            _globals = globals().copy()
            _locals = locals().copy()
            _globals.update(_locals)
            code.interact(local=_globals)

    except click.UsageError as ue:
        click.echo(f"Configuration error: {ue}", err=True)
        raise click.Abort()
    except ConnectionError as ce:
        click.echo(f"Connection failed: {ce}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
