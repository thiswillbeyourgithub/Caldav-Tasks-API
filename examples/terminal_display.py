from fire import Fire
from caldav_tasks_api import TasksAPI


def main(list_name: str, number: int = 10):
    api = TasksAPI(read_only=True)
    tasklist = [
        tl for tl in api.task_lists if (tl.name == list_name or tl.uid == list_name)
    ]
    assert len(tasklist) == 1, "Wrong list name"
    tasklist = tasklist[0]

    tasks = tasklist.tasks

    # filter some
    tasks = [t for t in tasks if not t.completed]
    tasks = [t for t in tasks if not t.trash]
    tasks = [t for t in tasks if not t.deleted]

    # sort
    # get lowest sort value
    min_sort_order = min(
        [
            (
                int(t.x_properties.apple_sort_order)
                if hasattr(t.x_properties, "apple_sort_order")
                else 0
            )
            for t in tasks
        ]
    )

    def sorter(task) -> int:
        if not hasattr(task.x_properties, "apple_sort_order"):
            return min_sort_order
        else:
            return int(task.x_properties.apple_sort_order)

    # regroup by parent
    def sort_hierarchical_tasks(tasks):
        # Build parent-to-children mapping
        children_map = {}
        task_map = {task.uid: task for task in tasks}

        for task in tasks:
            parent_uid = task.parent
            if parent_uid not in children_map:
                children_map[parent_uid] = []
            children_map[parent_uid].append(task)

        # Sort children by apple_sort_order within each parent group
        for parent_uid in children_map:
            children_map[parent_uid].sort(key=sorter)

        def traverse(parent_uid, depth=0):
            if parent_uid not in children_map:
                return

            for task in children_map[parent_uid]:
                yield task, depth
                yield from traverse(task.uid, depth + 1)

        # Start with root tasks (parent=None or parent not in task_map)
        roots = [t for t in tasks if t.parent is None or t.parent not in task_map]
        roots.sort(key=sorter)

        for root in roots:
            yield root, 0
            yield from traverse(root.uid, 1)

    # Usage
    for task, depth in sort_hierarchical_tasks(tasks):
        indent = "  " * depth
        aso = (
            task.x_properties.apple_sort_order
            if hasattr(task.x_properties, "apple_sort_order")
            else "?"
        )
        try:
            summary = task.summary
            if summary == "---":
                print(f"{indent}{summary}")
            elif aso == "?":
                print(f"{indent}{summary} {aso}")
            else:
                print(f"{indent}{summary}")

        except Exception as e:
            print(f"Error when display task: {task}")


if __name__ == "__main__":
    Fire(main)
