import pytest
from caldav_tasks_api import TasksAPI, TaskData, TaskListData # Assuming tasks_api is importable
import uuid

def test_fetch_task_lists(tasks_api_instance: TasksAPI):
    """Test that task lists can be fetched and are populated."""
    api = tasks_api_instance
    # Data should already be loaded by the fixture, but an explicit call can be made if desired
    # api.load_remote_data() 
    
    assert api.task_lists is not None, "Task lists object should exist."
    assert isinstance(api.task_lists, list), "Task lists should be a list."
    
    if not api.task_lists:
        print("Warning: No task lists found on the server. Test might not be comprehensive.")
    
    for task_list in api.task_lists:
        assert isinstance(task_list, TaskListData), "Each item in task_lists should be TaskListData."
        assert task_list.uid, f"Task list '{task_list.name}' should have a UID."
        assert task_list.name is not None, f"Task list UID '{task_list.uid}' should have a name."
        print(f"Found task list: {task_list.name} (UID: {task_list.uid})")

def test_find_tasks_in_lists(tasks_api_instance: TasksAPI):
    """Test that tasks can be found within fetched task lists."""
    api = tasks_api_instance
    
    if not api.task_lists:
        pytest.skip("No task lists found, skipping task finding test.")

    found_any_task = False
    for task_list in api.task_lists:
        print(f"Checking tasks in list: {task_list.name} (UID: {task_list.uid})")
        assert isinstance(task_list.tasks, list), f"Tasks attribute for list '{task_list.name}' should be a list."
        if task_list.tasks:
            found_any_task = True
            for task in task_list.tasks:
                assert isinstance(task, TaskData), f"Each task in list '{task_list.name}' should be TaskData."
                assert task.uid, f"Task in list '{task_list.name}' should have a UID."
                assert task.text is not None, f"Task UID '{task.uid}' in list '{task_list.name}' should have text."
                print(f"  Found task: {task.text[:50]}... (UID: {task.uid})")
    
    if not found_any_task:
        print("Warning: No tasks found in any list. Test might not be comprehensive.")


def test_create_and_delete_task(tasks_api_instance: TasksAPI, test_list_name: str):
    """
    Test creating a new task in the designated test list and then deleting it.
    Requires CALDAV_TASKS_API_TEST_LIST_NAME environment variable to be set.
    """
    api = tasks_api_instance

    # Find the target test list
    target_list: TaskListData | None = None
    for tl in api.task_lists:
        if tl.name == test_list_name:
            target_list = tl
            break
    
    if not target_list:
        pytest.skip(f"Test list '{test_list_name}' not found on the server. Skipping create/delete test.")

    assert target_list.uid is not None, "Target list UID should not be None"
    
    # --- Create Task ---
    original_task_count = len(target_list.tasks)
    new_task_text = f"Test Task - {uuid.uuid4()}"
    task_to_create = TaskData(
        text=new_task_text,
        list_uid=target_list.uid
    )
    
    print(f"Attempting to create task '{new_task_text}' in list '{target_list.name}' (UID: {target_list.uid})")
    
    created_task_data = api.add_task(task_to_create, target_list.uid)
    assert created_task_data is not None, "add_task should return the created task data."
    assert created_task_data.uid, "Created task data should have a UID."
    assert created_task_data.text == new_task_text, "Created task text mismatch."
    assert created_task_data.synced is True, "Created task should be marked as synced."
    
    # Verify task is in the list by re-fetching or checking local state if add_task updates it
    # For robustness, let's reload data for that specific list or all lists
    api.load_remote_data() # Reload all data to ensure we see the server state
    target_list_after_add = api.get_task_list_by_uid(target_list.uid)
    assert target_list_after_add is not None, "Target list not found after reloading for add."

    assert len(target_list_after_add.tasks) == original_task_count + 1, "Task count should increase by 1 after adding."

    created_task_on_server = None
    for task in target_list_after_add.tasks:
        if task.text == new_task_text: # Or match by UID if add_task returns the server-assigned UID
            created_task_on_server = task
            break
    
    assert created_task_on_server is not None, f"Created task '{new_task_text}' not found in list after add."
    assert created_task_on_server.uid, "Task created on server must have a UID."
    print(f"Successfully created task '{created_task_on_server.text}' with UID '{created_task_on_server.uid}'")

    # --- Delete Task ---
    task_uid_to_delete = created_task_on_server.uid
    print(f"Attempting to delete task UID '{task_uid_to_delete}' from list '{target_list.name}'")
    
    delete_successful = api.delete_task(task_uid_to_delete, target_list.uid)
    assert delete_successful, "delete_task should return True on success."

    # Verify task is removed
    api.load_remote_data() # Reload all data
    target_list_after_delete = api.get_task_list_by_uid(target_list.uid)
    assert target_list_after_delete is not None, "Target list not found after reloading for delete."
    
    assert len(target_list_after_delete.tasks) == original_task_count, "Task count should revert to original after deleting."

    task_should_be_gone = None
    for task in target_list_after_delete.tasks:
        if task.uid == task_uid_to_delete:
            task_should_be_gone = task
            break
    assert task_should_be_gone is None, f"Deleted task UID '{task_uid_to_delete}' still found in list."
    print(f"Successfully deleted task UID '{task_uid_to_delete}'")


def test_create_single_task(tasks_api_instance: TasksAPI, test_list_name: str):
    """
    Test creating a single new task in the designated test list.
    Requires CALDAV_TASKS_API_TEST_LIST_NAME environment variable to be set.
    The created task is NOT deleted by this test.
    """
    api = tasks_api_instance

    # Find the target test list
    target_list: TaskListData | None = None
    for tl in api.task_lists:
        if tl.name == test_list_name:
            target_list = tl
            break
    
    if not target_list:
        pytest.skip(f"Test list '{test_list_name}' not found on the server. Skipping create task test.")

    assert target_list.uid is not None, "Target list UID should not be None"
    
    # --- Create Task ---
    # Reload data to get the current state before adding a new task
    api.load_remote_data() 
    target_list_before_add = api.get_task_list_by_uid(target_list.uid)
    assert target_list_before_add is not None, "Target list not found after reloading before add."
    original_task_count = len(target_list_before_add.tasks)

    new_task_text = f"Single Test Task - {uuid.uuid4()}"
    task_to_create = TaskData(
        text=new_task_text,
        list_uid=target_list_before_add.uid # Use UID from the reloaded list
    )
    
    print(f"Attempting to create task '{new_task_text}' in list '{target_list_before_add.name}' (UID: {target_list_before_add.uid})")
    
    created_task_data = api.add_task(task_to_create, target_list_before_add.uid)
    assert created_task_data is not None, "add_task should return the created task data."
    assert created_task_data.uid, "Created task data should have a UID."
    assert created_task_data.text == new_task_text, "Created task text mismatch."
    assert created_task_data.synced is True, "Created task should be marked as synced."
    
    # Verify task is in the list by re-fetching
    api.load_remote_data() # Reload all data to ensure we see the server state
    target_list_after_add = api.get_task_list_by_uid(target_list_before_add.uid) # Use original UID
    assert target_list_after_add is not None, "Target list not found after reloading for add."

    assert len(target_list_after_add.tasks) == original_task_count + 1, "Task count should increase by 1 after adding."

    created_task_on_server = None
    # Match by the UID returned by add_task, which is more reliable than text
    for task in target_list_after_add.tasks:
        if task.uid == created_task_data.uid: 
            created_task_on_server = task
            break
    
    assert created_task_on_server is not None, f"Created task '{new_task_text}' (UID: {created_task_data.uid}) not found in list after add."
    assert created_task_on_server.text == new_task_text, "Text of task on server does not match."
    print(f"Successfully created task '{created_task_on_server.text}' with UID '{created_task_on_server.uid}'")
