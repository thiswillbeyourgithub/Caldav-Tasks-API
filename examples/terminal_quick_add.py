#!/usr/bin/python
"""
Quick task addition script for CalDAV task lists.

This script provides a smart command-line interface for quickly adding tasks to CalDAV
task lists with minimal typing. It supports:
- Automatic list detection from first word using fuzzy matching
- Creating child tasks using '>' prefix
- Creating multiple tasks at once using '|' separator
- Desktop notifications on task creation

The script uses environment variable CALDAV_TASKS_API_DEFAULT_LIST_UID for default list.
This script was created with assistance from aider.chat.
"""

import os
from fire import Fire
from caldav_tasks_api.caldav_tasks_api import TasksAPI, TaskData
from plyer import notification
from rapidfuzz.distance.Levenshtein import normalized_distance as lev_dist
from rapidfuzz.fuzz import ratio as lev_ratio


def main(
    task_text: str,
    notif: bool = True,
    target_lists: list = None,
):
    """
    Create one or more CalDAV tasks with smart list detection and hierarchy support.

    This function implements intelligent task creation with several features:
    - Fuzzy matching of list names from the first word of task_text
    - Parent-child task relationships using '>' prefix
    - Batch task creation using '|' separator
    - Desktop notifications for user feedback

    The function first attempts to match the first word against task list UIDs using
    fuzzy string matching (Levenshtein distance). If a match is found with sufficient
    confidence (ratio > 0.6 and distance <= 0.5), that list is used and the first
    word is removed from the task text. Otherwise, it falls back to the default list
    specified in CALDAV_TASKS_API_DEFAULT_LIST_UID environment variable.

    Parameters
    ----------
    task_text : str
        The task summary text. Can include special prefixes:
        - Start with '>' to create as child of most recent task
        - Use '|' to separate multiple tasks to create
        - First word may be fuzzy-matched to a list UID
    notif : bool, optional
        Whether to show desktop notification after task creation, by default True
    target_lists : list, optional
        List of task list UIDs to limit operations to. Can be comma-separated string
        or list of strings, by default None (uses all lists except test list)

    Raises
    ------
    AssertionError
        If task_text is empty after stripping
        If default_list_id is set but not found in available lists

    Notes
    -----
    - Excludes the 'tests_do_not_delete' list from all operations
    - Sets X-CREATOR property to 'terminal_quick_add.py' for tracking
    - Uses SSL verification disabled for CalDAV connection
    - Only considers non-completed, non-deleted tasks when finding parent tasks

    Examples
    --------
    Create a simple task in default list:
        main("Buy groceries")

    Create task in specific list (fuzzy matched):
        main("work Review PR #123")

    Create child task of most recent task:
        main("> Follow up tomorrow")

    Create multiple tasks at once:
        main("Task 1 | Task 2 | Task 3")

    Can be combined:
        main("my project")
        main("> Task 1 | Task 2 | Task 3")
    """
    if isinstance(target_lists, str) and "," in target_lists:
        target_lists = target_lists.split(",")
    elif isinstance(target_lists, str):
        target_lists = [target_lists]

    api = TasksAPI(
        ssl_verify_cert=False,
        debug=True,
        read_only=False,
        target_lists=target_lists,
        include_completed=False,
    )
    api.load_remote_data()

    task_lists = api.task_lists

    # exclude the list used for pytest of the caldav client
    task_lists = [tl for tl in task_lists if tl.uid != "tests_do_not_delete"]

    # we can use env var to specify a default list uid
    default_list_id = os.environ.get("CALDAV_TASKS_API_DEFAULT_LIST_UID", None)
    if default_list_id:
        assert default_list_id in [tl.uid for tl in task_lists], task_lists

    task_text = task_text.strip()
    assert task_text, "Received empty text"

    # notification to show the user
    user_notif = ""

    # if the first word is similar to a list name, we use that list and drop that first word
    list_uid = ""
    task_list = None
    first_word = task_text.split(" ")[0]
    if len(first_word) >= 4:
        tl_ratios = [
            (tl, lev_ratio(first_word, tl.uid) / 100, lev_dist(first_word, tl.uid))
            for tl in task_lists
        ]
        tl_ratios = [
            tlr
            for tlr in tl_ratios
            if (tlr[1] > 0.6 and tlr[2] <= 0.5)
            or tlr[0].uid.lower().startswith(first_word.lower())
        ]
        if tl_ratios:
            tl_ratios = sorted(tl_ratios, key=lambda x: x[1] - x[2], reverse=True)
            task_list = tl_ratios[0][0]
            list_uid = task_list.uid
            task_text = " ".join(task_text.split(" ")[1:]).strip()

            user_notif += f"List: {list_uid} ({tl_ratios[0][1]}, {tl_ratios[0][2]})"
            print(f"List: {list_uid} ({tl_ratios[0][1]}, {tl_ratios[0][2]})")
    if not list_uid:
        user_notif += f"List: {default_list_id} (default)"
        print(f"List: {default_list_id} (default)")

    # if contain > near the start we create the task(s) as children of the last created task
    create_as_child = False
    if task_text.startswith(">") or first_word.startswith(">"):
        task_text = task_text.replace(" > ", "")
        task_text = task_text.replace(" >", "")
        task_text = task_text.replace("> ", "")
        task_text = task_text.replace(">", "")
        create_as_child = True

    # if contain | we create multiple tasks
    create_multiple = False
    if "|" in task_text:
        create_multiple = True
        task_texts = [tt.strip() for tt in task_text.split("|")]

    if create_as_child:
        # find the most recent task
        if task_list is None:  # we have not matched a task list
            if default_list_id:
                tasks = [tl.tasks for tl in task_lists if tl.uid == default_list_id][0]
            else:  # search across all tasks
                tasks = []
                [tasks.extend(tl.tasks) for tl in task_lists]
        else:  # search in the matched task list
            tasks = task_list.tasks
        recent_task = sorted(
            [t for t in tasks if not t.deleted and not t.completed],
            key=lambda x: x.created_at,
        )

        most_recent = recent_task[-1]
        parent_id = most_recent.uid
        user_notif += f"\nParent: '{most_recent.summary[:10]}...'"
        print(f"Parent: '{most_recent.summary[:10]}...'")

    if not create_multiple:
        task_data = TaskData(
            summary=task_text,
            list_uid=list_uid,
            parent=parent_id if create_as_child else "",
            x_properties={"CREATOR": "terminal_quick_add.py"},
        )
        api.add_task(task_data)
        user_notif += f"\nCreated: '{task_text}'"
        print(f"Created: '{task_text}'")

    else:
        user_notif += "\nCreated: "
        print("Created:")
        for itt, tt in enumerate(task_texts):
            task_data = TaskData(
                summary=tt,
                list_uid=list_uid,
                parent=parent_id if create_as_child else "",
                x_properties={
                    "CREATOR": "terminal_quick_add.py",
                    "apple-sort-order": str(itt),
                },
            )
            api.add_task(task_data)
            if itt != len(task_texts):
                user_notif += f"'{tt}' ; "
            else:
                user_notif += f"'{tt}'"
            print(f"  - {tt}")

    if user_notif:
        notification.notify(
            title="add_task.py",
            message=user_notif,
            timeout=5,
        )
    print("Done")


if __name__ == "__main__":
    Fire(main)
