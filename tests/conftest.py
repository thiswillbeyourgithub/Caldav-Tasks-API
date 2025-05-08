import pytest
import os
from dotenv import load_dotenv
from caldav_tasks_api import TasksAPI, TaskData # Assuming tasks_api is importable

# Load environment variables from .env file if it exists
load_dotenv()

@pytest.fixture(scope="session")
def caldav_credentials():
    """Fixture to provide CalDAV credentials from environment variables."""
    url = os.environ.get("CALDAV_URL")
    username = os.environ.get("CALDAV_USERNAME")
    password = os.environ.get("CALDAV_PASSWORD")

    if not all([url, username, password]):
        pytest.skip("CALDAV_URL, CALDAV_USERNAME, or CALDAV_PASSWORD environment variables not set.")
    
    return {"url": url, "username": username, "password": password}

@pytest.fixture(scope="session")
def tasks_api_instance(caldav_credentials):
    """Fixture to provide an initialized TasksAPI instance."""
    try:
        api = TasksAPI(
            url=caldav_credentials["url"],
            username=caldav_credentials["username"],
            password=caldav_credentials["password"],
            nextcloud_mode=True # Assuming Nextcloud mode for tests, adjust if needed
        )
        api.load_remote_data() # Initial load of data
        return api
    except ConnectionError as e:
        pytest.fail(f"Failed to connect to CalDAV server: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during TasksAPI initialization: {e}")


@pytest.fixture(scope="session")
def test_list_name():
    """Fixture to provide the name of the list designated for testing create/delete operations."""
    name = os.environ.get("CALDAV_TASKS_API_TEST_LIST_NAME")
    if not name:
        pytest.skip("CALDAV_TASKS_API_TEST_LIST_NAME environment variable not set. Skipping create/delete tests.")
    return name

@pytest.fixture(scope="session")
def read_only_tasks_api_instance(caldav_credentials):
    """Fixture to provide an initialized TasksAPI instance in read-only mode."""
    try:
        api = TasksAPI(
            url=caldav_credentials["url"],
            username=caldav_credentials["username"],
            password=caldav_credentials["password"],
            nextcloud_mode=True,  # Assuming Nextcloud mode for tests
            read_only=True  # Initialize in read-only mode
        )
        # Load data for read-only instance as well, so it has lists/tasks to "attempt" to modify
        api.load_remote_data() 
        return api
    except ConnectionError as e:
        pytest.fail(f"Failed to connect to CalDAV server for read_only_tasks_api_instance: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during read_only_tasks_api_instance initialization: {e}")
