"""
Caldav Tasks API Package.

This package provides the TasksAPI client for interacting with CalDAV task servers,
and the data structures TaskListData and TaskData for representing task lists and tasks.
"""

# Initialize logging configuration as early as possible
from caldav_tasks_api.utils import logging_config  # This will run setup_logging()

from caldav_tasks_api.caldav_tasks_api import TasksAPI
from caldav_tasks_api.utils.data import TaskData, TaskListData
import caldav_tasks_api.__main__ as cli

VERSION = TasksAPI.VERSION

__all__ = [
    "TasksAPI",
    "TaskData",
    "TaskListData",
    "logging_config",  # Optionally expose logger or config
    "VERSION",
    "cli",
]
