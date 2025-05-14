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

import click
from loguru import logger

from .caldav_tasks_api import TasksAPI
from .utils.data import TaskData # Import TaskData


def get_api(url: Optional[str], username: Optional[str], password: Optional[str],
            nextcloud_mode: bool, debug: bool, target_lists: Optional[List[str]],
            read_only: bool) -> TasksAPI:
    """
    Initializes and returns the TasksAPI instance.
    Validates credentials and raises appropriate errors.
    """
    # Get credentials from args or environment
    url = url or os.environ.get("CALDAV_URL")
    username = username or os.environ.get("CALDAV_USERNAME")
    password = password or os.environ.get("CALDAV_PASSWORD")
    
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
@click.option('--url', help='CalDAV server URL (or set CALDAV_URL env var)')
@click.option('--username', help='CalDAV username (or set CALDAV_USERNAME env var)')
@click.option('--password', help='CalDAV password (or set CALDAV_PASSWORD env var)')
@click.option('--nextcloud-mode/--no-nextcloud-mode', default=True, 
              help='Adjust URL for Nextcloud specific path [default: enabled]')
@click.option('--debug/--no-debug', default=False, 
              help='Enable debug mode with interactive console [default: disabled]')
@click.option('--list', '-l', multiple=True, help='Filter by task list name or UID (can use multiple times)')
@click.option('--json/--no-json', 'json_output', default=False,
              help='Output summary as JSON [default: disabled]')
@click.option('--read-only/--read-write', 'read_only_flag', default=True,
              help='Operate in read-only mode (default) or allow modifications [default: read-only]')
def show_summary(url, username, password, nextcloud_mode, debug, list, json_output, read_only_flag):
    """Connect to CalDAV server and show a summary of all task lists and tasks."""
    target_lists = list if list else None
    logger.debug(f"CLI initialized with url: {'***' if url else 'from env'}, "
                f"user: {username or 'from env'}, nc_mode: {nextcloud_mode}, "
                f"debug: {debug}, lists: {target_lists}, json: {json_output}, read_only: {read_only_flag}")

    try:
        api = get_api(url, username, password, nextcloud_mode, debug, target_lists, read_only=read_only_flag)
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
            click.echo("Debug mode: Starting interactive console. API available as 'api'.")
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


@cli.command()
@click.option('--url', help='CalDAV server URL (or set CALDAV_URL env var)')
@click.option('--username', help='CalDAV username (or set CALDAV_USERNAME env var)')
@click.option('--password', help='CalDAV password (or set CALDAV_PASSWORD env var)')
@click.option('--nextcloud-mode/--no-nextcloud-mode', default=True,
              help='Adjust URL for Nextcloud specific path [default: enabled]')
@click.option('--debug/--no-debug', default=False,
              help='Enable debug mode with interactive console [default: disabled]')
@click.option('--list-uid', required=True, help='UID of the task list to add the task to.')
@click.option('--summary', required=True, help='Summary/text of the task.')
# Add more options for other TaskData fields as needed (e.g., --notes, --due-date)
def add_task(url, username, password, nextcloud_mode, debug, list_uid, summary):
    """Add a new task to a specified task list."""
    logger.debug(f"CLI add-task initiated with url: {'***' if url else 'from env'}, "
                f"user: {username or 'from env'}, nc_mode: {nextcloud_mode}, "
                f"debug: {debug}, list_uid: {list_uid}, summary: {summary}")

    try:
        # For adding tasks, read_only must be False.
        # target_lists is not strictly needed for adding a single task if list_uid is known,
        # but get_api expects it. We pass None as we are directly using list_uid.
        api = get_api(url, username, password, nextcloud_mode, debug, target_lists=None, read_only=False)
        
        task_data = TaskData(
            text=summary,
            list_uid=list_uid
            # Initialize other fields of TaskData as needed, e.g. notes, due_date
            # For example:
            # notes="Generated via CLI",
        )
        
        logger.info(f"Attempting to add task '{summary}' to list '{list_uid}'...")
        created_task = api.add_task(task_data, list_uid)
        
        click.echo(f"Task '{created_task.text}' added successfully!")
        click.echo(f"  UID: {created_task.uid}")
        click.echo(f"  List UID: {created_task.list_uid}")
        if created_task.synced:
            click.echo("  Status: Synced with server.")
        else:
            click.echo("  Status: Not synced (or sync status unknown) with server.", err=True)

        if debug:
            click.echo("Debug mode: Starting interactive console. API and task available as 'api', 'created_task'.")
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
        click.echo(f"Value error: {ve}", err=True) # e.g. list not found
        raise click.Abort()
    except Exception as e:
        logger.exception(f"An unexpected error occurred while adding task: {e}")
        click.echo(f"Error adding task: {e}", err=True)
        raise click.Abort()


@cli.command(name="list-lists")
@click.option('--url', help='CalDAV server URL (or set CALDAV_URL env var)')
@click.option('--username', help='CalDAV username (or set CALDAV_USERNAME env var)')
@click.option('--password', help='CalDAV password (or set CALDAV_PASSWORD env var)')
@click.option('--nextcloud-mode/--no-nextcloud-mode', default=True,
              help='Adjust URL for Nextcloud specific path [default: enabled]')
@click.option('--debug/--no-debug', default=False,
              help='Enable debug mode with interactive console [default: disabled]')
# target_lists is implicitly all lists for this command
def list_lists(url, username, password, nextcloud_mode, debug):
    """Connect to CalDAV server and print a JSON list of task lists (name and UID)."""
    logger.debug(f"CLI list-lists initiated with url: {'***' if url else 'from env'}, "
                f"user: {username or 'from env'}, nc_mode: {nextcloud_mode}, "
                f"debug: {debug}")

    try:
        # This command is inherently read-only.
        # No specific target_lists, we want all lists.
        api = get_api(url, username, password, nextcloud_mode, debug, target_lists=None, read_only=True)
        logger.info("Loading remote task lists...")
        api.load_remote_data() # This loads all lists and their tasks

        # Prepare data for JSON output: a list of dicts with name and UID
        output_data = [
            {"name": tl.name, "uid": tl.uid} for tl in api.task_lists
        ]
        click.echo(json.dumps(output_data, ensure_ascii=False, indent=2))

        if debug:
            click.echo("Debug mode: Starting interactive console. API available as 'api'.")
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
