#!/usr/bin/env python3
"""
Autodelete script for completed tasks older than specified days.
This script uses the caldav-tasks-api to automatically delete completed tasks
that have been last modified more than X days ago from a specified task list.

This script was created with assistance from aider.chat.
"""

import click
import datetime
from typing import List, Optional
from loguru import logger

from caldav_tasks_api.caldav_tasks_api import TasksAPI
from caldav_tasks_api.utils.data import TaskData


def parse_ical_datetime(dt_str: str) -> datetime.datetime:
    """
    Parse iCal datetime string to datetime object.

    Handles formats like:
    - "20250101T120000Z" (UTC datetime)
    - "20250101T120000" (local datetime)
    - "20250101" (date only)

    Args:
        dt_str: The datetime string from iCal format

    Returns:
        Parsed datetime object, or datetime.min if parsing fails
    """
    if not dt_str:
        logger.warning("Empty datetime string provided")
        return datetime.datetime.min

    # Handle UTC timezone indicator
    is_utc = dt_str.endswith("Z")
    clean_str = dt_str.rstrip("Z")

    try:
        # Try parsing as datetime with time component
        if "T" in clean_str:
            parsed_dt = datetime.datetime.strptime(clean_str, "%Y%m%dT%H%M%S")
        else:
            # Parse as date only and set to start of day
            parsed_dt = datetime.datetime.strptime(clean_str, "%Y%m%d")

        # If it was UTC, make it timezone-aware, otherwise assume local
        if is_utc:
            parsed_dt = parsed_dt.replace(tzinfo=datetime.timezone.utc)

        return parsed_dt

    except ValueError as e:
        logger.warning(f"Could not parse datetime string '{dt_str}': {e}")
        return datetime.datetime.min


def get_tasks_to_delete(tasks: List[TaskData], days_threshold: int) -> List[TaskData]:
    """
    Filter completed tasks that are older than the specified threshold.

    Args:
        tasks: List of TaskData objects to filter
        days_threshold: Number of days threshold for deletion

    Returns:
        List of TaskData objects that should be deleted
    """
    # Calculate cutoff date (make timezone-aware for comparison)
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=days_threshold
    )
    logger.info(
        f"Cutoff date for deletion: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    # Filter for completed tasks that are old enough
    tasks_to_delete: List[TaskData] = []

    for task in tasks:
        if not task.completed:
            continue

        task_modified_date = parse_ical_datetime(task.changed_at)

        # Make comparison timezone-aware if needed
        if task_modified_date.tzinfo is None:
            task_modified_date = task_modified_date.replace(
                tzinfo=datetime.timezone.utc
            )

        if task_modified_date < cutoff_date:
            days_old = (cutoff_date - task_modified_date).days
            logger.debug(
                f"Task '{task.summary}' qualifies for deletion (modified {days_old} days ago)"
            )
            tasks_to_delete.append(task)

    # Sort tasks by modification date, oldest first
    def get_task_sort_key(task: TaskData) -> datetime.datetime:
        """Helper function to extract sortable datetime from task."""
        task_date = parse_ical_datetime(task.changed_at)
        if task_date.tzinfo is None:
            task_date = task_date.replace(tzinfo=datetime.timezone.utc)
        return task_date

    tasks_to_delete.sort(key=get_task_sort_key)
    logger.debug(
        f"Sorted {len(tasks_to_delete)} tasks by modification date (oldest first)"
    )

    return tasks_to_delete


@click.command()
@click.option(
    "--list-uid", type=str, required=True, help="The UID of the task list to process"
)
@click.option(
    "--days-threshold",
    type=int,
    required=True,
    help="Number of days - completed tasks older than this will be deleted",
)
@click.option("--url", help="CalDAV server URL (or set CALDAV_TASKS_API_URL env var)")
@click.option(
    "--username", help="CalDAV username (or set CALDAV_TASKS_API_USERNAME env var)"
)
@click.option(
    "--password", help="CalDAV password (or set CALDAV_TASKS_API_PASSWORD env var)"
)
@click.option(
    "--nextcloud-mode/--no-nextcloud-mode",
    default=True,
    help="Enable Nextcloud CalDAV path adjustment (default: enabled)",
)
@click.option(
    "--debug/--no-debug", default=False, help="Enable debug mode with detailed logging"
)
@click.option(
    "--ssl-verify/--no-ssl-verify",
    default=True,
    help="Verify SSL certificates (default: enabled)",
)
@click.option(
    "--dry",
    is_flag=True,
    default=False,
    help="Show what would be deleted without actually deleting",
)
def main(
    list_uid: str,
    days_threshold: int,
    url: Optional[str],
    username: Optional[str],
    password: Optional[str],
    nextcloud_mode: bool,
    debug: bool,
    ssl_verify: bool,
    dry: bool,
):
    """
    Delete completed tasks that have been last modified more than the specified days threshold.

    This script will connect to your CalDAV server, load tasks from the specified list,
    and delete completed tasks that haven't been modified within the threshold period.

    Examples:

        # Dry run (safe - shows what would be deleted)
        python autodelete.py --list-uid my-list-uid --days-threshold 30 --dry

        # Actually delete tasks (removes completed tasks older than 30 days)
        python autodelete.py --list-uid my-list-uid --days-threshold 30

        # Use with custom server settings
        python autodelete.py --list-uid my-list-uid --days-threshold 7 --url https://my-server.com --username myuser
    """
    # Setup logging - use basic configuration since no logging_config module referenced
    if debug:
        logger.add(lambda msg: None, level="TRACE")  # Enable trace level for debug mode

    logger.info(f"=== CalDAV Tasks Autodelete ===")
    logger.info(f"List UID: {list_uid}")
    logger.info(f"Days threshold: {days_threshold}")
    logger.info(
        f"Mode: {'DRY RUN (safe preview)' if dry else 'EXECUTE (will delete tasks)'}"
    )

    if days_threshold <= 0:
        logger.error("Days threshold must be a positive number")
        raise click.BadParameter("Days threshold must be greater than 0")

    try:
        # Initialize the TasksAPI - target only the specified list for efficiency
        logger.info("Connecting to CalDAV server...")
        api = TasksAPI(
            url=url,
            username=username,
            password=password,
            nextcloud_mode=nextcloud_mode,
            debug=debug,
            target_lists=[list_uid],  # Only load the specified list
            read_only=dry,  # Use read-only mode for dry runs to prevent accidental changes
            ssl_verify_cert=ssl_verify,
        )

        logger.info("Successfully connected to CalDAV server")

        # Get the task list info
        task_list = api.get_task_list_by_uid(list_uid)
        if not task_list:
            logger.error(f"Task list with UID '{list_uid}' not found")
            logger.info("Available task lists:")
            for tl in api.task_lists:
                logger.info(f"  - {tl.name} (UID: {tl.uid})")
            return

        logger.info(f"Processing task list: '{task_list.name}'")

        # Get all tasks for the specified list
        tasks = api.get_tasks_by_list_uid(list_uid)
        if not tasks:
            logger.warning(f"No tasks found in list '{task_list.name}'")
            return

        logger.info(f"Found {len(tasks)} total tasks in list")

        # Filter for completed tasks
        completed_tasks = [task for task in tasks if task.completed]
        logger.info(f"Found {len(completed_tasks)} completed tasks")

        if not completed_tasks:
            logger.info("No completed tasks found - nothing to delete")
            return

        # Find tasks that meet deletion criteria
        tasks_to_delete = get_tasks_to_delete(completed_tasks, days_threshold)

        logger.info(
            f"Found {len(tasks_to_delete)} completed tasks older than {days_threshold} days"
        )

        if not tasks_to_delete:
            logger.info("No tasks meet the deletion criteria")
            return

        # Display what will be deleted
        logger.info(f"\n{'=' * 50}")
        logger.info(f"Tasks to be {'deleted' if not dry else 'deleted (DRY RUN)'}:")
        logger.info(f"{'=' * 50}")

        for i, task in enumerate(tasks_to_delete, 1):
            modified_date = parse_ical_datetime(task.changed_at)
            if modified_date.tzinfo is None:
                modified_date = modified_date.replace(tzinfo=datetime.timezone.utc)
            days_old = (
                datetime.datetime.now(datetime.timezone.utc) - modified_date
            ).days

            logger.info(
                f"{i:3}. '{task.summary[:60]}{'...' if len(task.summary) > 60 else ''}'"
            )
            logger.info(
                f"     Last modified: {modified_date.strftime('%Y-%m-%d %H:%M:%S UTC')} ({days_old} days ago)"
            )
            logger.info(f"     UID: {task.uid}")
            logger.info("")

        if dry:
            logger.info("=" * 50)
            logger.info(f"DRY RUN COMPLETE: Would delete {len(tasks_to_delete)} tasks")
            logger.info("Run without --dry flag to actually delete these tasks")
            logger.info("=" * 50)
        else:
            # Actually delete the tasks
            logger.info("=" * 50)
            logger.info(f"EXECUTING DELETION of {len(tasks_to_delete)} tasks...")
            logger.info("=" * 50)

            deleted_count = 0
            failed_count = 0

            for i, task in enumerate(tasks_to_delete, 1):
                try:
                    logger.info(
                        f"Deleting {i}/{len(tasks_to_delete)}: '{task.summary}'"
                    )
                    task.delete()
                    deleted_count += 1
                    logger.info(f"  ✓ Successfully deleted")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"  ✗ Failed to delete: {e}")

            logger.info("=" * 50)
            logger.info(f"DELETION COMPLETE")
            logger.info(f"Successfully deleted: {deleted_count}")
            logger.info(f"Failed to delete: {failed_count}")
            logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Error during autodelete operation: {e}")
        if debug:
            import traceback

            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise
        else:
            logger.error("Use --debug flag for detailed error information")


if __name__ == "__main__":
    main()
