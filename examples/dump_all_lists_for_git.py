#!/usr/bin/env python3
"""
Dump all CalDAV task lists to individual files for git versioning.

This script connects to a CalDAV server, retrieves all task lists,
and for each list dumps all tasks in VTODO format to a file named
after the list. Tasks are sorted by modification date with most
recent changes at the bottom.

This allows for easy git versioning of todo lists.
"""

import click
import os
from pathlib import Path
from typing import Optional, List
from caldav_tasks_api import TasksAPI, TaskData, TaskListData


def sanitize_filename(name: str) -> str:
    """
    Sanitize a list name to be safe for use as a filename.

    Args:
        name: The original list name

    Returns:
        A sanitized filename safe for most filesystems
    """
    # Replace problematic characters with underscores
    invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, "_")

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(" .")

    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed_list"

    return sanitized


def sort_tasks_by_modification_date(tasks: List[TaskData]) -> List[TaskData]:
    """
    Sort tasks by modification date, with most recent changes at the bottom.

    Args:
        tasks: List of TaskData objects to sort

    Returns:
        Sorted list of TaskData objects
    """

    def get_sort_key(task: TaskData) -> str:
        # Use changed_at if available, otherwise use created_at, otherwise use empty string
        if task.changed_at:
            return task.changed_at
        elif task.created_at:
            return task.created_at
        else:
            return ""

    return sorted(tasks, key=get_sort_key)


@click.command()
@click.option(
    "--url",
    envvar="CALDAV_TASKS_API_URL",
    help="CalDAV server URL. Can be set via CALDAV_TASKS_API_URL environment variable.",
)
@click.option(
    "--username",
    envvar="CALDAV_TASKS_API_USERNAME",
    help="Username for CalDAV authentication. Can be set via CALDAV_TASKS_API_USERNAME environment variable.",
)
@click.option(
    "--password",
    envvar="CALDAV_TASKS_API_PASSWORD",
    help="Password for CalDAV authentication. Can be set via CALDAV_TASKS_API_PASSWORD environment variable.",
)
@click.option(
    "--nextcloud-mode/--no-nextcloud-mode",
    default=True,
    help="Enable Nextcloud-specific optimizations (default: enabled).",
)
@click.option(
    "--debug/--no-debug", default=False, help="Enable debug mode (default: disabled)."
)
@click.option(
    "--ssl-verify/--no-ssl-verify",
    default=True,
    help="Verify SSL certificates (default: enabled).",
)
@click.option(
    "--output-dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("."),
    help="Directory to save dump files (default: current directory).",
)
def main(
    url: Optional[str],
    username: Optional[str],
    password: Optional[str],
    nextcloud_mode: bool,
    debug: bool,
    ssl_verify: bool,
    output_dir: Path,
) -> None:
    """
    Dump all CalDAV task lists to individual files for git versioning.

    For each task list found on the server, this script creates a file
    named "{list_name}.dump" containing all tasks in that list in VTODO
    format. Tasks are sorted by modification date with most recent
    changes at the bottom.

    This allows for easy git versioning and tracking of changes to
    your todo lists over time.
    """
    try:
        # Create API instance
        api = TasksAPI(
            url=url,
            username=username,
            password=password,
            nextcloud_mode=nextcloud_mode,
            debug=debug,
            ssl_verify_cert=ssl_verify,
            read_only=True,  # We're only reading data
        )

        # Load data from server
        click.echo("Loading data from CalDAV server...")
        api.load_remote_data()

        if not api.task_lists:
            click.echo("No task lists found on the server.")
            return

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        click.echo(f"Found {len(api.task_lists)} task lists. Processing...")

        # Process each task list
        for task_list in api.task_lists:
            process_task_list(api, task_list, output_dir)

        click.echo(f"Successfully dumped all task lists to {output_dir}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


def process_task_list(api: TasksAPI, task_list: TaskListData, output_dir: Path) -> None:
    """
    Process a single task list and dump its tasks to a file.

    Args:
        api: The TasksAPI instance
        task_list: The task list to process
        output_dir: Directory to save the dump file
    """
    list_name = task_list.name or f"list_{task_list.uid}"
    click.echo(f"Processing list: {list_name} ({len(task_list.tasks)} tasks)")

    # Get tasks for this list
    tasks = task_list.tasks

    if not tasks:
        click.echo(f"  No tasks found in list '{list_name}'")
        # Still create an empty file to track the list existence
        output_content = (
            f"# Task list: {list_name}\n# UID: {task_list.uid}\n# No tasks found\n"
        )
    else:
        # Sort tasks by modification date
        sorted_tasks = sort_tasks_by_modification_date(tasks)

        # Generate VTODO content for all tasks
        vtodo_blocks = []
        for task in sorted_tasks:
            try:
                vtodo_content = task.to_ical()
                vtodo_blocks.append(vtodo_content)
            except Exception as e:
                click.echo(
                    f"  Warning: Failed to convert task '{task.summary}' to iCal: {e}"
                )
                continue

        # Combine all VTODO blocks with metadata header
        output_content = f"# Task list: {list_name}\n# UID: {task_list.uid}\n# Tasks: {len(vtodo_blocks)}\n\n"
        output_content += "\n\n".join(vtodo_blocks)
        output_content += "\n"  # Final newline

    # Save to file
    filename = f"{sanitize_filename(list_name)}.dump"
    output_path = output_dir / filename

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_content)
        click.echo(f"  Saved to: {output_path}")
    except Exception as e:
        click.echo(f"  Error saving to {output_path}: {e}", err=True)


if __name__ == "__main__":
    main()
