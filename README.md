[![PyPI version](https://badge.fury.io/py/caldav-tasks-api.svg)](https://badge.fury.io/py/caldav-tasks-api)
*(Full documentation available at [caldavtasksapi.readthedocs.io](https://caldavtasksapi.readthedocs.io/en/latest/#))*

# CalDAV-Tasks-API

A Python library and command-line interface (CLI) for interacting with CalDAV task lists (VTODOs). This project provides tools to connect to a CalDAV server, fetch task lists and tasks, create new tasks, and delete existing ones.

## Table of Contents

- [Motivation and Purpose](#motivation-and-purpose)
- [Compatibility](#compatibility)
- [Features](#features)
- [Installation](#installation)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)


## Motivation and Purpose

This library was developed as a foundational component for integrating CalDAV task management with more advanced systems. The primary goal is to serve as a backbone for:

1. Synchronizing tasks from applications like the excellent [Tasks.org Android app](https://f-droid.org/packages/org.tasks/).
2. Enabling features such as smart task prioritization using ELO ranking, envisioned to work with a [Litoy-like setup](https://github.com/thiswillbeyourgithub/mini_LiTOY).
3. Making useful python objects with handy methods to manipulate caldav's tasks.
4. Making a CLI interface to manipulate tasks (secondary goal).

By providing a robust Python interface to CalDAV tasks, this project aims to bridge the gap between standard task management and custom, intelligent task processing workflows. The library is intentionally designed to be minimal, with few external dependencies, to ensure it is lightweight and easy to integrate.

## Compatibility

The API has been primarily tested with **Nextcloud Tasks**. However, it is designed to be compatible with any CalDAV server that supports VTODO components.

Testers and feedback for other CalDAV server implementations (e.g., Baïkal, Radicale, Synology Calendar) are highly welcome!

## Some of the features

*   Connect to CalDAV servers with optional Nextcloud-specific URL adjustments.
*   Load task lists (calendars supporting VTODOs).
*   Load tasks from specified lists, parsing standard iCalendar properties.
*   Preserve and provide access to custom `X-` properties.
*   Create, update, and delete tasks (VTODOs) on the server.
*   Access parent and child task relationships (`TaskData.parent_task` and `TaskData.child_tasks`).
*   Read-only mode for applications that need to prevent modifications.
*   CLI for basic task list inspection with JSON output support (secondary goal of the project).

## Installation

The CalDAV Tasks API can be installed directly from PyPI:

```bash
uv pip install caldav-tasks-api
```

Alternatively, you can install from source:

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd caldav-tasks-api
    ```
2.  Install dependencies (ensure you have `python>=3.8`):
    ```bash
    # Install the package and all dependencies:
    uv pip install .
    
    # For development with editable install:
    uv pip install -e .
    
    # For development with additional dev dependencies:
    uv pip install -e ".[dev]"
    ```

## Contributing

Contributions are welcome! If you'd like to contribute, please feel free to:

1.  Open an issue to discuss a bug, feature request, or an idea.
2.  Fork the repository and submit a pull request with your changes.

Please ensure your code follows the existing style and includes tests where appropriate.

## Acknowledgements

This project was developed with the assistance of [aider.chat](https://aider.chat), an AI pair programmer.
