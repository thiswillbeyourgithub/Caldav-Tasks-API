from __future__ import annotations

import datetime
import random
from dataclasses import dataclass, field, fields  # Added fields
from typing import Optional, Dict
from uuid import uuid4


@dataclass
class TaskListData:
    color: str = ""
    # 'deleted' might be used by TasksAPI to mark for server-side deletion
    deleted: bool = False
    name: str = ""
    # 'synced' indicates if this local representation matches the server
    synced: bool = False
    uid: str = ""
    tasks: list[TaskData] = field(default_factory=list)  # Holds tasks for this list

    def __post_init__(self):
        if not self.uid:
            self.uid = str(uuid4())

    def __str__(self) -> str:
        """Returns a user-friendly string representation of the task list."""
        return (
            f"<TaskListData Name: '{self.name}', UID: {self.uid}, "
            f"Tasks: {len(self.tasks)}>"
        )

    def __repr__(self) -> str:
        """Returns a developer-friendly string representation of the task list."""
        # Similar to __str__ but more explicit about the class and attributes
        return (
            f"{self.__class__.__name__}("
            f"uid='{self.uid}', name='{self.name}', "
            f"deleted={self.deleted}, synced={self.synced}, "
            f"tasks_count={len(self.tasks)})"  # Represent tasks by their count
        )

    def __iter__(self):
        """Allows iteration over the tasks in the task list."""
        return iter(self.tasks)

    def to_dict(self) -> Dict:
        """Converts the TaskListData instance to a dictionary."""
        return {
            "uid": self.uid,
            "name": self.name,
            "color": self.color,
            "deleted": self.deleted,
            "synced": self.synced,
            "tasks": [task.to_dict() for task in self.tasks],
        }


class XProperties:
    """
    A wrapper for X-properties dictionary to allow attribute-style access
    with normalized names, while preserving original keys.
    """

    def __init__(self, initial_data: Optional[Dict[str, str]] = None):
        self._raw_properties: Dict[str, str] = (
            initial_data if initial_data is not None else {}
        )

    def __getattr__(self, name: str) -> str:
        """
        Allows attribute-style access to X-properties.
        Example: if raw key is "X-APPLE-SORT-ORDER", it can be accessed via xprops.apple_sort_order.
        """
        normalized_name_query = name.lower()

        for raw_key, raw_value in self._raw_properties.items():
            # Normalize raw_key: e.g., "X-APPLE-SORT-ORDER;FOO=BAR" -> "apple_sort_order"
            key_for_comparison = raw_key.split(";")[
                0
            ].lower()  # Isolate key part, lowercase

            if key_for_comparison.startswith("x-"):
                key_for_comparison = key_for_comparison[2:]  # Remove "x-" prefix
            key_for_comparison = key_for_comparison.replace(
                "-", "_"
            )  # Convert hyphens to underscores

            if key_for_comparison == normalized_name_query:
                return raw_value

        raise AttributeError(
            f"'{type(self).__name__}' object has no X-property corresponding to attribute '{name}'. "
            f"Searched for normalized form '{normalized_name_query}'. "
            f"Available raw X-property keys: {list(self._raw_properties.keys())}"
        )

    def __setitem__(self, key: str, value: str) -> None:
        """Stores the property with its original key. For dict-like assignment."""
        self._raw_properties[key] = value

    def __getitem__(self, key: str) -> str:
        """Retrieves the property using its original key. For dict-like access."""
        try:
            return self._raw_properties[key]
        except KeyError:
            # Case-insensitive lookup as fallback
            key_lower = key.lower()
            for raw_key, value in self._raw_properties.items():
                if raw_key.lower() == key_lower:
                    return value
            # If we get here, the key really doesn't exist
            raise KeyError(key)

    def get_raw_properties(self) -> Dict[str, str]:
        """Returns the underlying dictionary of raw X-properties."""
        return self._raw_properties

    def items(self):
        """Allows iteration like a dictionary (e.g., for key, value in x_props.items())."""
        return self._raw_properties.items()

    def __contains__(self, key: str) -> bool:
        """
        Case-insensitive check if a key exists in the X-properties.
        This is used for expressions like `key in x_properties`.
        """
        if key in self._raw_properties:
            return True

        # Case-insensitive lookup
        key_lower = key.lower()
        for raw_key in self._raw_properties:
            if raw_key.lower() == key_lower:
                return True

        # Handle the case where the prefix (X-...) is the same but the UUID part differs in case
        # Many servers might normalize the UUID part to all uppercase or all lowercase
        parts = key.split("-", 2)  # Split on first two hyphens (e.g., X-TEST-PROP-uuid)
        if len(parts) >= 3:
            prefix = "-".join(parts[0:2])  # X-TEST
            uuid_part = parts[2]  # PROP-uuid

            for raw_key in self._raw_properties:
                raw_parts = raw_key.split("-", 2)
                if len(raw_parts) >= 3:
                    raw_prefix = "-".join(raw_parts[0:2])
                    raw_uuid_part = raw_parts[2]

                    if (
                        prefix.lower() == raw_prefix.lower()
                        and uuid_part.lower() == raw_uuid_part.lower()
                    ):
                        return True

        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._raw_properties!r})"

    def __bool__(self) -> bool:
        """Defines truthiness based on whether any X-properties are stored."""
        return bool(self._raw_properties)


@dataclass
class TaskData:
    attachments: list[str] = field(default_factory=lambda: [])
    completed: bool = False  # STATUS:COMPLETED or NEEDS-ACTION
    changed_at: str = ""  # LAST-MODIFIED
    created_at: str = ""  # DTSTAMP
    deleted: bool = False  # Internal flag, might map to VTODO status or deletion
    due_date: str = ""  # DUE
    list_uid: str = ""  # Belongs to which TaskList/Calendar
    notes: str = ""  # DESCRIPTION
    notified: bool = False  # UI specific, not in standard VTODO
    parent: str = ""  # RELATED-TO (for subtasks)
    percent_complete: int = 0  # PERCENT-COMPLETE
    priority: int = 0  # PRIORITY
    rrule: str = ""  # RRULE for recurrence
    start_date: str = ""  # DTSTART
    synced: bool = False  # Internal flag
    tags: list[str] = field(default_factory=lambda: [])  # CATEGORIES
    text: str = ""  # SUMMARY
    trash: bool = False  # UI specific, might relate to 'deleted'
    uid: str = ""  # UID
    x_properties: XProperties = field(
        default_factory=XProperties
    )  # For any other X- properties
    _api_reference: Optional["TasksAPI"] = field(
        default=None, repr=False, compare=False
    )  # Reference to the TasksAPI instance, set by TasksAPI

    def __post_init__(self):
        """Set default values that need to be calculated and ensure types."""
        now_utc = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        )
        if not self.uid:  # Ensure UID is always present
            self.uid = str(uuid4())
        if not self.created_at:
            self.created_at = now_utc
        if not self.changed_at:
            self.changed_at = now_utc

        # Ensure x_properties is an XProperties instance, even if a dict was passed during init
        if isinstance(self.x_properties, dict):
            self.x_properties = XProperties(self.x_properties)

    def __str__(self) -> str:
        """Returns a pretty-printed string representation of the task."""
        lines = [f"<TaskData UID: {self.uid}>"]
        for f in fields(self.__class__):  # Iterate over dataclass fields
            if f.name == "uid":  # Already in the header
                continue
            value = getattr(self, f.name)
            # For potentially long string fields like 'notes' or 'text', truncate if too long for summary
            if isinstance(value, str) and len(value) > 70:
                value_repr = f"'{value[:67]}...'"
            elif (
                isinstance(value, list) and not value
            ):  # Don't print empty lists unless specifically desired
                continue
            # Check XProperties instance using its __bool__ method for emptiness
            elif isinstance(value, XProperties) and not value:
                continue
            elif (
                isinstance(value, dict) and not value
            ):  # Handles other potential dicts if any
                continue
            else:
                value_repr = repr(value)

            # Only print fields that have a non-default or interesting value for a summary string
            # This logic can be adjusted based on what's considered "interesting"
            if value or isinstance(
                value, (bool, int, float)
            ):  # Print booleans, numbers even if 0/False
                lines.append(f"  {f.name}: {value_repr}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        """Returns a detailed, developer-friendly representation of the task."""
        # For dataclasses, a common repr is one that could reconstruct the object
        # Here, we'll make it similar to __str__ but explicitly state the class name
        # and ensure all fields are represented.
        field_strings = []
        for f in fields(self.__class__):
            value = getattr(self, f.name)
            field_strings.append(f"{f.name}={value!r}")  # Use repr for each value
        return f"{self.__class__.__name__}(\n  " + ",\n  ".join(field_strings) + "\n)"

    @property
    def parent_task(self) -> Optional["TaskData"]:
        """
        Returns the parent TaskData object, if this task has a parent UID
        and an API reference to search for it.
        """
        if self.parent and self._api_reference:
            # get_task_by_global_uid will search across all lists managed by the API instance
            return self._api_reference.get_task_by_global_uid(self.parent)
        return None

    @property
    def child_tasks(self) -> list["TaskData"]:
        """
        Returns a list of child TaskData objects, if this task has children
        and an API reference to search for them.
        Searches for tasks whose 'parent' field matches this task's UID.
        """
        children: list[TaskData] = []
        if self._api_reference and self.uid:  # self.uid must exist to be a parent
            for task_list in self._api_reference.task_lists:
                for (
                    task_item
                ) in (
                    task_list.tasks
                ):  # Renamed 'task' to 'task_item' to avoid conflict with `TaskData` type hint in some contexts
                    if task_item.parent == self.uid:
                        children.append(task_item)
        return children

    def to_ical(self) -> str:
        """Build VTODO iCal component string from TaskData properties."""
        ical: str = ""
        ical += "BEGIN:VTODO\n"
        ical += f"UID:{self.uid}\n"
        ical += f"SUMMARY:{self.text}\n"
        if self.notes:
            # Escape newlines and commas as per iCal spec
            escaped_notes = self.notes.replace("\n", "\\n").replace(",", "\\,")
            ical += f"DESCRIPTION:{escaped_notes}\n"  # Ensure DESCRIPTION is not empty

        ical += f"DTSTAMP:{self.created_at}\n"  # Typically creation or last data stamp
        ical += f"LAST-MODIFIED:{self.changed_at}\n"

        ical += f"STATUS:{'COMPLETED' if self.completed else 'NEEDS-ACTION'}\n"
        if self.completed and self.percent_complete < 100:
            self.percent_complete = 100  # Ensure consistency
        ical += f"PERCENT-COMPLETE:{self.percent_complete}\n"

        if self.due_date:
            # Check if due_date is datetime or date
            is_date = "T" not in self.due_date
            ical += f"DUE{';VALUE=DATE' if is_date else ''}:{self.due_date}\n"
        if self.start_date:
            is_date = "T" not in self.start_date
            ical += f"DTSTART{';VALUE=DATE' if is_date else ''}:{self.start_date}\n"

        if self.priority != 0:  # Standard allows 0-9, 0 means undefined.
            ical += f"PRIORITY:{self.priority}\n"
        if self.parent:
            ical += f"RELATED-TO:{self.parent}\n"
        if self.tags:
            ical += f"CATEGORIES:{','.join(self.tags)}\n"
        if self.rrule:
            ical += f"RRULE:{self.rrule}\n"

        # Add any other X-properties
        for key, value in self.x_properties.items():
            # Escape special characters that might interfere with iCal parsing
            escaped_value = (
                value.replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")
            )
            ical += f"{key}:{escaped_value}\n"

        # attachments are not standard in VTODO, would need X-PROP or ATTACH property

        ical += "END:VTODO\n"
        return ical

    def to_dict(self) -> Dict:
        """Converts the TaskData instance to a dictionary."""
        data = {
            "uid": self.uid,
            "text": self.text,
            "notes": self.notes,
            "created_at": self.created_at,
            "changed_at": self.changed_at,
            "completed": self.completed,
            "percent_complete": self.percent_complete,
            "due_date": self.due_date,
            "start_date": self.start_date,
            "priority": self.priority,
            "parent": self.parent,
            "tags": self.tags,
            "rrule": self.rrule,
            "attachments": self.attachments,
            "deleted": self.deleted,
            "list_uid": self.list_uid,
            "notified": self.notified,
            "synced": self.synced,
            "trash": self.trash,
            "x_properties": self.x_properties.get_raw_properties(),
        }
        return data

    @staticmethod
    def from_ical(ical: str | bytes, list_uid: str) -> TaskData:
        """Build TaskData from a VTODO iCal string."""
        task: TaskData = TaskData(list_uid=list_uid)
        ical_str = str(ical)

        # Ensure we are parsing only the VTODO part
        vtodo_content = ical_str
        if "BEGIN:VTODO" in ical_str:
            start_idx = ical_str.find("BEGIN:VTODO")
            end_idx = ical_str.find("END:VTODO")
            if start_idx != -1 and end_idx != -1:
                vtodo_content = ical_str[start_idx:end_idx]

        # First, unfold the iCal content (RFC 5545 section 3.1)
        # Lines that start with whitespace are a continuation of the previous line
        unfolded_lines = []
        for line in vtodo_content.splitlines():
            if line.startswith(" ") or line.startswith("\t"):
                if unfolded_lines:  # Make sure there's a previous line to append to
                    unfolded_lines[-1] += line[1:]  # Skip the leading whitespace
            else:
                unfolded_lines.append(line)

        # Helper to parse property values, handling potential parameters (e.g., DUE;VALUE=DATE:...)
        def get_value(line: str) -> str:
            return line.split(":", 1)[-1]

        for line in unfolded_lines:
            if ":" not in line:  # Skip lines without a colon (like BEGIN:VTODO itself)
                continue

            prop_part = line.split(":", 1)[0]
            prop_name = prop_part.split(";")[
                0
            ].upper()  # Property name, uppercase, ignore params for matching
            value = get_value(line)

            if "UID" == prop_name:
                task.uid = value
            elif "SUMMARY" == prop_name:
                task.text = value
            elif "DESCRIPTION" == prop_name:
                task.notes = value.replace("\\n", "\n").replace(
                    "\\,", ","
                )  # Unescape common characters
            elif "DTSTAMP" == prop_name:
                task.created_at = value
            elif "LAST-MODIFIED" == prop_name:
                task.changed_at = value
            elif "STATUS" == prop_name:
                task.completed = value == "COMPLETED"
            elif "PERCENT-COMPLETE" == prop_name:
                try:
                    task.percent_complete = int(float(value))
                except ValueError:
                    task.percent_complete = 0  # Default if invalid
            elif "DUE" == prop_name:
                task.due_date = value
            elif "DTSTART" == prop_name:
                task.start_date = value
            elif "PRIORITY" == prop_name:
                try:
                    task.priority = int(value)
                except ValueError:
                    task.priority = 0  # Default if invalid
            elif "RELATED-TO" == prop_name:
                task.parent = value
            elif "CATEGORIES" == prop_name:
                task.tags = (
                    [tag.strip() for tag in value.split(",") if tag.strip()]
                    if value
                    else []
                )
            elif "RRULE" == prop_name:
                task.rrule = value
            # Capture any other X- properties
            elif prop_name.startswith("X-"):
                # Unescape special characters in the value
                unescaped_value = (
                    value.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";")
                )
                # task.x_properties is an XProperties instance, so this uses XProperties.__setitem__
                task.x_properties[prop_part] = (
                    unescaped_value  # Store with original casing and params
                )

        # If UID was somehow not in the VTODO, ensure it's set (should not happen for valid VTODO)
        if not task.uid:
            task.uid = str(uuid4())
            # Mark as not synced if UID had to be generated, as it's a new local interpretation
            task.synced = False
        else:
            # If UID was present, assume it's from server or a known item
            task.synced = True

        # Ensure changed_at is set, defaulting to created_at if not present
        if not task.changed_at and task.created_at:
            task.changed_at = task.created_at

        return task
