Here's the rewritten content in Markdown format:

```markdown
# Examples

## Python API Usage

Here's an example of how to use the `caldav-tasks-api` library in Python:

```python
from caldav_tasks_api import TasksAPI, TaskData
from caldav_tasks_api.utils.data import XProperties # For advanced X-Property handling
import os # For environment variables, if used

# Initialize the API
# Credentials can be passed directly or loaded from environment variables if not provided
try:
    api = TasksAPI(
        url=os.environ.get("CALDAV_TASKS_API_URL", "YOUR_CALDAV_URL"),
        username=os.environ.get("CALDAV_TASKS_API_USERNAME", "YOUR_USERNAME"),
        password=os.environ.get("CALDAV_TASKS_API_PASSWORD", "YOUR_PASSWORD"),
        # nextcloud_mode=True,  # Default, adjust if not using Nextcloud
        # target_lists=["Personal", "Work"], # Optional: load only specific lists by name or UID
        # debug=True, # Optional: enable PDB for certain exceptions
        # read_only=True, # Optional: prevent any modifications to the server
    )
except ConnectionError as e:
    print(f"Failed to connect: {e}")
    exit()

# Load all task lists and their tasks from the server
api.load_remote_data()

# Access task lists and tasks
print("--- Task Lists ---")
for task_list in api.task_lists:
    print(f"List: '{task_list.name}' (UID: {task_list.uid})")
    print(f"  Tasks: {len(task_list.tasks)}")
    for task in task_list:  # TaskListData is iterable over its tasks
        status = "Completed" if task.completed else "Pending"
        print(f"    - [{status}] {task.text} (UID: {task.uid})")
        if task.due_date:
            print(f"      Due: {task.due_date}")
        if task.notes:
            print(f"      Notes: {task.notes[:50]}...")
        if task.x_properties: # Check if there are any X-properties
            print(f"      X-Properties:")
            for key, value in task.x_properties.items(): # Iterate raw X-properties
                print(f"        {key}: {value}")
            # Example of accessing a specific X-property via normalized attribute:
            # if hasattr(task.x_properties, 'tasks_org_order'):
            #     print(f"        Tasks.org Order: {task.x_properties.tasks_org_order}")

# Example: Add a new task
if api.task_lists:
    # For this example, pick the first task list.
    # In a real application, you'd likely let the user choose or have a default.
    target_list_uid = api.task_lists[0].uid

    new_task_data = TaskData(
        text="My important new task from API",
        notes="This is a detailed description.",
        list_uid=target_list_uid, # Set the list_uid for the new task
        priority=5, # 1 (highest) to 9 (lowest), 0 (undefined)
        # x_properties={"X-CUSTOM-FIELD": "CustomValue"} # Can also pass a dict
    )
    # Or initialize XProperties directly and assign
    new_task_data.x_properties["X-ANOTHER-PROP"] = "AnotherValue"

    try:
        # Ensure the API is not in read-only mode if you want to add tasks.
        # If api was initialized with read_only=True, this will raise a PermissionError.
        # If you need to switch an existing API instance from read-only to read-write:
        # api.read_only = False # (and vice-versa) BEFORE calling modification methods.

        created_task = api.add_task(new_task_data, target_list_uid) # Pass target_list_uid explicitly
        print(f"\n--- Created Task ---")
        print(f"Successfully created task: '{created_task.text}' with UID: {created_task.uid} in list {target_list_uid}")
        print(f"Server assigned created_at: {created_task.created_at}, changed_at: {created_task.changed_at}")

        # Example: Update the task we just created
        print(f"\n--- Updating Task ---")
        created_task.text = "Updated task title"
        created_task.priority = 1  # Higher priority
        updated_task = api.update_task(created_task) # update_task uses task_data.list_uid
        print(f"Successfully updated task: '{updated_task.text}' with UID: {updated_task.uid}")
        print(f"Server updated changed_at: {updated_task.changed_at}")

        # Example: Delete the task
        # print(f"\n--- Deleting Task ---")
        # if api.delete_task(created_task.uid, target_list_uid): # delete_task requires list_uid
        #     print(f"Successfully deleted task UID: {created_task.uid}")
        # else:
        #     print(f"Failed to delete task UID: {created_task.uid}")

    except PermissionError as e:
        print(f"Permission error: {e} - Ensure API is not in read-only mode for modifications.")
    except ValueError as e:
        print(f"Error adding/updating/deleting task: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
else:
    print("No task lists found. Cannot add a new task.")
```

Key changes made:
1. Replaced rST headers with Markdown headers (# and ##)
2. Replaced `.. code-block:: python` with ```python
3. Maintained all the code structure and comments exactly as they were
4. Preserved all the functionality and examples
5. Kept the same formatting for the example code
```
