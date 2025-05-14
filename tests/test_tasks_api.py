import pytest
from caldav_tasks_api import TasksAPI, TaskData, TaskListData # Assuming tasks_api is importable
import uuid
import subprocess
import sys # To get python executable

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


def test_create_and_rename_task(tasks_api_instance: TasksAPI, test_list_name: str):
    """
    Test creating a new task, renaming it, and verifying the change.
    The task is NOT deleted by this test.
    """
    api = tasks_api_instance

    # Find the target test list
    target_list: TaskListData | None = None
    # Ensure data is loaded before searching for the list
    api.load_remote_data()
    for tl in api.task_lists:
        if tl.name == test_list_name:
            target_list = tl
            break
    
    if not target_list:
        pytest.skip(f"Test list '{test_list_name}' not found on the server. Skipping create/rename test.")

    assert target_list.uid is not None, "Target list UID should not be None"
    
    # --- Create Task ---
    initial_task_text = f"Initial Name - {uuid.uuid4()}"
    task_to_create = TaskData(
        text=initial_task_text,
        list_uid=target_list.uid
    )
    
    print(f"Attempting to create task '{initial_task_text}' in list '{target_list.name}' (UID: {target_list.uid})")
    created_task_data = api.add_task(task_to_create, target_list.uid)
    assert created_task_data is not None, "add_task should return the created task data."
    assert created_task_data.uid, "Created task data should have a UID."
    assert created_task_data.text == initial_task_text, "Created task text mismatch."
    assert created_task_data.synced is True, "Created task should be marked as synced."
    print(f"Successfully created task '{created_task_data.text}' with UID '{created_task_data.uid}'")

    # Add delay to ensure the server has time to process the creation
    import time
    time.sleep(2)

    # --- Rename Task ---
    renamed_task_text = f"Renamed Task - {uuid.uuid4()}"
    task_to_update = created_task_data # Work with the instance returned by add_task
    task_to_update.text = renamed_task_text
    
    print(f"Attempting to rename task UID '{task_to_update.uid}' to '{renamed_task_text}'")
    updated_task_data = api.update_task(task_to_update)
    assert updated_task_data is not None, "update_task should return the updated task data."
    assert updated_task_data.uid == created_task_data.uid, "Updated task UID should match original."
    assert updated_task_data.text == renamed_task_text, "Updated task text mismatch after update call."
    assert updated_task_data.synced is True, "Updated task should be marked as synced."
    print(f"Successfully called update_task for task UID '{updated_task_data.uid}'")

    # --- Verify Rename on Server ---
    api.load_remote_data() # Reload all data to ensure we see the server state
    target_list_after_rename = api.get_task_list_by_uid(target_list.uid)
    assert target_list_after_rename is not None, "Target list not found after reloading for rename verification."

    renamed_task_on_server = None
    for task in target_list_after_rename.tasks:
        if task.uid == updated_task_data.uid:
            renamed_task_on_server = task
            break
    
    assert renamed_task_on_server is not None, f"Task UID '{updated_task_data.uid}' not found in list after rename."
    assert renamed_task_on_server.text == renamed_task_text, f"Task text on server ('{renamed_task_on_server.text}') does not match expected renamed text ('{renamed_task_text}')."
    print(f"Successfully verified renamed task '{renamed_task_on_server.text}' (UID: '{renamed_task_on_server.uid}') on server.")


def test_task_to_dict(tasks_api_instance: TasksAPI, test_list_name: str):
    """
    Test the to_dict() method of TaskData for tasks in the designated test list.
    """
    api = tasks_api_instance

    # Find the target test list
    target_list: TaskListData | None = None
    # Ensure data is loaded before searching for the list
    api.load_remote_data()
    for tl in api.task_lists:
        if tl.name == test_list_name:
            target_list = tl
            break
    
    if not target_list:
        pytest.skip(f"Test list '{test_list_name}' not found on the server. Skipping to_dict test.")

    if not target_list.tasks:
        print(f"Warning: No tasks found in the test list '{test_list_name}'. Test test_task_to_dict might not be comprehensive.")
        return # Nothing to test if there are no tasks

    print(f"Found {len(target_list.tasks)} tasks in list '{test_list_name}' for to_dict testing.")
    for task in target_list.tasks:
        assert isinstance(task, TaskData), "Task object is not of type TaskData."
        print(f"  Testing to_dict for task: {task.text[:50]}... (UID: {task.uid})")
        task_dict = task.to_dict()

        assert task_dict is not None, "to_dict() should return a dictionary, not None."
        assert isinstance(task_dict, dict), "to_dict() should return a type dict."
        
        # Check for essential keys
        assert "uid" in task_dict, "Task dictionary should contain 'uid'."
        assert task_dict["uid"] == task.uid, "Task dictionary 'uid' should match task.uid."
        
        assert "text" in task_dict, "Task dictionary should contain 'text'."
        assert task_dict["text"] == task.text, "Task dictionary 'text' should match task.text."

        assert "list_uid" in task_dict, "Task dictionary should contain 'list_uid'."
        assert task_dict["list_uid"] == task.list_uid, "Task dictionary 'list_uid' should match task.list_uid."

        assert "created_at" in task_dict, "Task dictionary should contain 'created_at'."
        assert "changed_at" in task_dict, "Task dictionary should contain 'changed_at'."
        assert "completed" in task_dict, "Task dictionary should contain 'completed'."
        
        # Check x_properties structure
        assert "x_properties" in task_dict, "Task dictionary should contain 'x_properties'."
        assert isinstance(task_dict["x_properties"], dict), "'x_properties' in task_dict should be a dict."
        
        print(f"    Task UID {task.uid} to_dict() successful.")


def test_cli_show_summary_json_runs_successfully(caldav_credentials):
    """
    Test that the CLI 'show-summary' command with '--json' runs successfully.
    This test relies on CALDAV_TASKS_API_TEST_URL, CALDAV_TASKS_API_TEST_USERNAME, CALDAV_TASKS_API_TEST_PASSWORD environment
    variables being set (handled by the caldav_credentials fixture).
    """
    # caldav_credentials fixture ensures env vars are set for the subprocess
    command = [
        sys.executable,  # Path to current python interpreter
        "-m",
        "caldav_tasks_api",
        "show-summary", # The command to run
        "--json" # Command-specific option for json output
    ]
    
    print(f"Running CLI command: {' '.join(command)}")
    
    try:
        # check=True will raise CalledProcessError if the command returns a non-zero exit code.
        # capture_output=True can be used if we need to inspect stdout/stderr, but not needed here.
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"CLI command stdout (first 200 chars): {result.stdout[:200]}...")
        print(f"CLI command stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"CLI command failed with exit code {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        pytest.fail(f"CLI command {' '.join(command)} failed with error: {e.stderr}")
    except FileNotFoundError:
        pytest.fail(f"CLI command failed: `python -m caldav_tasks_api` could not be found. Ensure the package is installed correctly, e.g., `pip install -e .`")


def test_add_task_in_read_only_mode(read_only_tasks_api_instance: TasksAPI, test_list_name: str):
    """Test that adding a task fails with PermissionError in read-only mode."""
    api = read_only_tasks_api_instance

    # Find the target test list UID (or any list UID, as the operation should fail before that)
    target_list_uid = None
    if api.task_lists:
        # Try to find the specific test list, fallback to any list if not found
        # The operation should fail regardless of whether the list exists or not in read-only mode
        for tl in api.task_lists:
            if tl.name == test_list_name:
                target_list_uid = tl.uid
                break
        if not target_list_uid: # Fallback to the first list if test_list_name not found
            target_list_uid = api.task_lists[0].uid

    if not target_list_uid and not api.task_lists:
         # If there are no lists at all, we can still test the read-only check
         # by providing a dummy list_uid. The PermissionError should be raised
         # before the API attempts to find the list on the server.
         target_list_uid = "dummy-list-uid-for-read-only-test"


    task_to_create = TaskData(
        text=f"Read-Only Test Task - {uuid.uuid4()}",
        list_uid=target_list_uid
    )
    
    with pytest.raises(PermissionError) as excinfo:
        api.add_task(task_to_create, target_list_uid) # type: ignore
    assert "API is in read-only mode" in str(excinfo.value)
    print(f"Successfully asserted PermissionError when adding task in read-only mode: {excinfo.value}")


def test_delete_task_in_read_only_mode(read_only_tasks_api_instance: TasksAPI, test_list_name: str):
    """Test that deleting a task fails with PermissionError in read-only mode."""
    api = read_only_tasks_api_instance

    # Similar to add_task, find a list UID or use a dummy one
    target_list_uid = None
    if api.task_lists:
        for tl in api.task_lists:
            if tl.name == test_list_name:
                target_list_uid = tl.uid
                break
        if not target_list_uid:
            target_list_uid = api.task_lists[0].uid
    
    if not target_list_uid and not api.task_lists:
        target_list_uid = "dummy-list-uid-for-read-only-test"

    dummy_task_uid = f"dummy-task-uid-for-delete-{uuid.uuid4()}"
    
    with pytest.raises(PermissionError) as excinfo:
        api.delete_task(dummy_task_uid, target_list_uid) # type: ignore
    assert "API is in read-only mode" in str(excinfo.value)
    print(f"Successfully asserted PermissionError when deleting task in read-only mode: {excinfo.value}")


def test_update_task_in_read_only_mode(read_only_tasks_api_instance: TasksAPI, test_list_name: str):
    """Test that updating a task fails with PermissionError in read-only mode."""
    api = read_only_tasks_api_instance

    target_list_uid = None
    existing_task_uid = None

    if api.task_lists:
        # Try to find the specific test list
        test_list_found = None
        for tl in api.task_lists:
            if tl.name == test_list_name:
                test_list_found = tl
                break
        
        if test_list_found and test_list_found.tasks:
            target_list_uid = test_list_found.uid
            existing_task_uid = test_list_found.tasks[0].uid # Use the first task from the test list
        elif api.task_lists[0].tasks: # Fallback to first task of first list
            target_list_uid = api.task_lists[0].uid
            existing_task_uid = api.task_lists[0].tasks[0].uid
    
    if not target_list_uid or not existing_task_uid:
        # If no suitable task is found, create dummy data.
        # The PermissionError should be raised before server interaction.
        target_list_uid = target_list_uid or "dummy-list-uid-for-read-only-test"
        existing_task_uid = existing_task_uid or f"dummy-task-uid-for-update-{uuid.uuid4()}"

    task_to_update = TaskData(
        uid=existing_task_uid,
        list_uid=target_list_uid, # type: ignore
        text=f"Attempted Update - {uuid.uuid4()}"
    )
    
    with pytest.raises(PermissionError) as excinfo:
        api.update_task(task_to_update)
    assert "API is in read-only mode" in str(excinfo.value)
    print(f"Successfully asserted PermissionError when updating task in read-only mode: {excinfo.value}")


def test_create_update_xprop_delete_task(tasks_api_instance: TasksAPI, test_list_name: str):
    """
    Test creating a task, adding an X property, then deleting the task.
    This test verifies that X properties can be properly stored and retrieved.
    """
    api = tasks_api_instance

    # Find the target test list
    target_list: TaskListData | None = None
    for tl in api.task_lists:
        if tl.name == test_list_name:
            target_list = tl
            break
    
    if not target_list:
        pytest.skip(f"Test list '{test_list_name}' not found on the server. Skipping test.")

    assert target_list.uid is not None, "Target list UID should not be None"
    
    # --- Create Task ---
    new_task_text = f"X-Prop Test Task - {uuid.uuid4()}"
    task_to_create = TaskData(
        text=new_task_text,
        list_uid=target_list.uid
    )
    
    print(f"Creating task '{new_task_text}' in list '{target_list.name}'")
    created_task = api.add_task(task_to_create, target_list.uid)
    assert created_task.uid, "Created task should have a UID"
    assert created_task.synced, "Created task should be marked as synced"
    
    # --- Add X Property ---
    x_prop_name = f"X-TEST-PROP-{uuid.uuid4()}"
    x_prop_value = f"test-value-{uuid.uuid4()}"
    
    print(f"Adding X property {x_prop_name}={x_prop_value} to task")
    created_task.x_properties[x_prop_name] = x_prop_value
    updated_task = api.update_task(created_task)
    
    assert updated_task.synced, "Updated task should be marked as synced"
    
    # --- Verify X Property ---
    # Reload data to ensure we get fresh data from server
    api.load_remote_data()
    
    # Find the task in the reloaded data
    task_list = api.get_task_list_by_uid(target_list.uid)
    assert task_list is not None, "Task list should be found after reload"
    
    found_task = None
    for task in task_list.tasks:
        if task.uid == created_task.uid:
            found_task = task
            break
    
    assert found_task is not None, f"Task '{new_task_text}' (UID: {created_task.uid}) should be found after reload"
    
    # Check that the X property exists
    x_props = found_task.x_properties.get_raw_properties()
    assert x_prop_name in found_task.x_properties, f"X property {x_prop_name} should exist in task. Available props: {list(x_props.keys())}"
    
    # Get the actual stored key that matches our x_prop_name (might differ in case)
    actual_key = None
    for k in x_props.keys():
        if k.lower() == x_prop_name.lower() or (
           # Handle case where UUID part differs in case
           k.split('-', 2)[0:2] == x_prop_name.split('-', 2)[0:2] and 
           k.split('-', 2)[2].lower() == x_prop_name.split('-', 2)[2].lower()):
            actual_key = k
            break
    
    assert actual_key is not None, f"Failed to find any key matching {x_prop_name} in {list(x_props.keys())}"
    assert x_props[actual_key] == x_prop_value, f"X property value should be {x_prop_value}, got {x_props.get(actual_key)}"
    
    print(f"Successfully verified X property {x_prop_name}={x_prop_value} on task")
    
    # --- Delete Task ---
    print(f"Deleting task UID {created_task.uid}")
    delete_successful = api.delete_task(created_task.uid, target_list.uid)
    assert delete_successful, "Task deletion should be successful"
    
    # Verify deletion
    api.load_remote_data()
    task_list = api.get_task_list_by_uid(target_list.uid)
    for task in task_list.tasks:
        assert task.uid != created_task.uid, f"Task UID {created_task.uid} should not exist after deletion"


def test_task_ical_roundtrip():
    """
    Test that the to_ical() → from_ical() roundtrip conversion works correctly,
    and that from_ical() → to_ical() produces the same output.
    This is a purely local test and should not interact with any server.
    """
    # Create a TaskData instance with various properties set
    original_task = TaskData(
        text="Test Task for iCal Roundtrip",
        notes="These are some notes\nWith multiple lines\nAnd some special chars: ü, é, ñ",
        due_date="20250101T120000Z",
        start_date="20240101",  # Date only format
        priority=1,
        tags=["test", "important", "ical-roundtrip"],
        percent_complete=50,
        list_uid="test-list-uid-for-roundtrip",  # Required for from_ical
    )
    
    # Add some X-properties
    original_task.x_properties["X-CUSTOM-PROP"] = "test-value"
    original_task.x_properties["X-ANOTHER-PROP"] = "another-value"
    
    # Get the iCal string
    ical_string = original_task.to_ical()
    print(f"Generated iCal string (first 200 chars):\n{ical_string[:200]}...")
    
    # Convert back to TaskData
    roundtrip_task = TaskData.from_ical(ical_string, list_uid=original_task.list_uid)
    
    # Verify that key properties were preserved
    assert roundtrip_task.uid == original_task.uid, "UID should be preserved"
    assert roundtrip_task.text == original_task.text, "Text (SUMMARY) should be preserved"
    assert roundtrip_task.notes == original_task.notes, "Notes (DESCRIPTION) should be preserved"
    assert roundtrip_task.due_date == original_task.due_date, "DUE date should be preserved"
    assert roundtrip_task.start_date == original_task.start_date, "DTSTART should be preserved"
    assert roundtrip_task.priority == original_task.priority, "PRIORITY should be preserved"
    assert set(roundtrip_task.tags) == set(original_task.tags), "CATEGORIES (tags) should be preserved"
    assert roundtrip_task.percent_complete == original_task.percent_complete, "PERCENT-COMPLETE should be preserved"
    
    # Check X-properties preservation
    for key, value in original_task.x_properties.items():
        assert key in roundtrip_task.x_properties.get_raw_properties(), f"X-property {key} should be preserved"
        assert roundtrip_task.x_properties[key] == value, f"X-property {key} value should be preserved"
    
    # Generate iCal string from the roundtrip task
    second_ical_string = roundtrip_task.to_ical()
    
    # Compare generated iCal strings
    # Note: Depending on implementation details, there might be minor formatting differences
    # that don't affect the semantic content. If exact string comparison fails, a more
    # sophisticated comparison might be needed.
    assert second_ical_string == ical_string, "Double conversion (to_ical→from_ical→to_ical) should produce the same output"
    
    print("Successfully verified TaskData.to_ical() → from_ical() → to_ical() roundtrip")


def test_task_parent_child_relationships(tasks_api_instance: TasksAPI, test_list_name: str):
    """
    Test that parent-child relationships between tasks are correctly established and retrievable.
    - Creates a parent task.
    - Creates a child task linked to the parent.
    - Verifies child.parent_task points to parent.
    - Verifies parent.child_tasks contains child.
    - Cleans up created tasks.
    """
    api = tasks_api_instance

    # Find the target test list
    target_list: TaskListData | None = None
    # Ensure data is loaded before searching for the list, as task_lists might be empty initially
    if not api.task_lists:
        api.load_remote_data()
        
    for tl in api.task_lists:
        if tl.name == test_list_name:
            target_list = tl
            break
    
    if not target_list:
        pytest.skip(f"Test list '{test_list_name}' not found on the server. Skipping parent-child relationship test.")

    assert target_list.uid is not None, "Target list UID should not be None"

    # --- Create Parent Task ---
    parent_task_text = f"Test Parent Task - {uuid.uuid4()}"
    parent_to_create = TaskData(text=parent_task_text, list_uid=target_list.uid)
    
    print(f"Attempting to create parent task '{parent_task_text}' in list '{target_list.name}' (UID: {target_list.uid})")
    created_parent_task = api.add_task(parent_to_create, target_list.uid)
    assert created_parent_task is not None, "add_task (parent) should return the created task data."
    assert created_parent_task.uid, "Created parent task data should have a UID."
    assert created_parent_task.text == parent_task_text, "Parent task text mismatch."
    assert created_parent_task.synced is True, "Created parent task should be marked as synced."
    print(f"Successfully created parent task '{created_parent_task.text}' with UID '{created_parent_task.uid}'")

    # --- Create Child Task ---
    child_task_text = f"Test Child Task - {uuid.uuid4()}"
    child_to_create = TaskData(
        text=child_task_text,
        list_uid=target_list.uid,
        parent=created_parent_task.uid  # Link to the parent's UID
    )

    print(f"Attempting to create child task '{child_task_text}' linked to parent UID '{created_parent_task.uid}'")
    created_child_task = api.add_task(child_to_create, target_list.uid)
    assert created_child_task is not None, "add_task (child) should return the created task data."
    assert created_child_task.uid, "Created child task data should have a UID."
    assert created_child_task.text == child_task_text, "Child task text mismatch."
    assert created_child_task.parent == created_parent_task.uid, "Child task parent UID mismatch."
    assert created_child_task.synced is True, "Created child task should be marked as synced."
    print(f"Successfully created child task '{created_child_task.text}' with UID '{created_child_task.uid}'")

    # --- Reload data: Crucial for populating _api_reference correctly for all tasks in api.task_lists ---
    print("Reloading all remote data to ensure API instance has fresh data and correct references.")
    api.load_remote_data()

    # --- Retrieve fresh tasks from API after reload ---
    # These instances will be from the refreshed api.task_lists and have their _api_reference correctly set.
    retrieved_parent = api.get_task_by_global_uid(created_parent_task.uid)
    retrieved_child = api.get_task_by_global_uid(created_child_task.uid)

    assert retrieved_parent is not None, f"Parent task (UID: {created_parent_task.uid}) should be found after reload."
    assert retrieved_child is not None, f"Child task (UID: {created_child_task.uid}) should be found after reload."

    # --- Test child's parent relationship ---
    print(f"Verifying child task (UID: {retrieved_child.uid}) parent relationship...")
    assert retrieved_child.parent_task is not None, "Child's parent_task property should resolve to a TaskData instance."
    assert retrieved_child.parent_task.uid == retrieved_parent.uid, \
        (f"Child's resolved parent UID ('{retrieved_child.parent_task.uid}') "
         f"should match original parent UID ('{retrieved_parent.uid}').")
    print("Child's parent relationship verified.")

    # --- Test parent's child relationship ---
    print(f"Verifying parent task (UID: {retrieved_parent.uid}) child relationship...")
    assert retrieved_parent.child_tasks, "Parent's child_tasks property should return a non-empty list."
    
    found_child_in_parent_list = next((t for t in retrieved_parent.child_tasks if t.uid == retrieved_child.uid), None)
    assert found_child_in_parent_list is not None, \
        (f"Child task (UID: {retrieved_child.uid}) was not found in parent's (UID: {retrieved_parent.uid}) "
         f"child_tasks list. Children found: {[c.uid for c in retrieved_parent.child_tasks]}.")
    assert found_child_in_parent_list.uid == retrieved_child.uid, \
        "The UID of the child found in parent's list does not match the expected child UID."
    print("Parent's child relationship verified.")

    # --- Clean up ---
    print(f"Attempting to delete child task UID '{created_child_task.uid}'")
    delete_child_successful = api.delete_task(created_child_task.uid, target_list.uid)
    assert delete_child_successful, "Child task deletion should return True."
    print(f"Successfully deleted child task UID '{created_child_task.uid}'.")

    print(f"Attempting to delete parent task UID '{created_parent_task.uid}'")
    delete_parent_successful = api.delete_task(created_parent_task.uid, target_list.uid)
    assert delete_parent_successful, "Parent task deletion should return True."
    print(f"Successfully deleted parent task UID '{created_parent_task.uid}'.")

    # Optional: Verify deletion by reloading data and checking counts or absence
    api.load_remote_data()
    target_list_after_cleanup = api.get_task_list_by_uid(target_list.uid)
    assert target_list_after_cleanup is not None, "Target list should still exist after cleanup."
    
    task_should_be_gone_child = api.get_task_by_global_uid(created_child_task.uid)
    assert task_should_be_gone_child is None, f"Child task UID '{created_child_task.uid}' should not be found after deletion."
    
    task_should_be_gone_parent = api.get_task_by_global_uid(created_parent_task.uid)
    assert task_should_be_gone_parent is None, f"Parent task UID '{created_parent_task.uid}' should not be found after deletion."
    print("Cleanup verified: Parent and child tasks are no longer present.")
