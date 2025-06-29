from __future__ import annotations
import random
import threading
import time
from typing import Any, Callable, Dict, List
from colorama import Fore, Style


class Task:
    """
    Represents a task with dependencies and extra information.

    Attributes:
        task_id: The unique identifier for the task.
        dependencies: A list of task IDs that must complete before this task can start.
        extra_info: Any additional information associated with the task.
    """

    def __init__(self, task_id: int, dependencies: List[Task], extra_info: Any = None):
        self.task_id = task_id
        self.extra_info = extra_info
        self.dependencies = dependencies
        self.status = 0


class TaskManager:
    """
    Manages a queue of tasks with dependencies and thread safety.

    Attributes:
        task_dict: Stores tasks, keyed by their IDs.
        lock: A lock for thread-safe access to the task dictionary.
        next_id: Generates unique IDs for new tasks.
        next_query_id: Generates unique IDs for queries.
    """

    def __init__(self):
        """
        Initializes the internal data structures for managing tasks and assigning unique identifiers.


        This constructor initializes the internal data structures for managing tasks,
        including a dictionary to store tasks, a lock for thread safety, and IDs for
        new tasks and queries.

        Args:
            None

        Returns:
            None

        """

        self.task_dict: Dict[int, Task] = {}
        self.task_lock = threading.Lock()
        self.now_id = 0
        self.query_id = 0

    @property
    def all_success(self) -> bool:
        """
        Checks if all tasks have finished. Returns True if no tasks remain, False otherwise.

                    Returns:
                        bool: True if the task dictionary is empty (all tasks successful), False otherwise.

        """

        return len(self.task_dict) == 0

    def add_task(self, dependency_task_id: List[int], extra=None) -> int:
        """
        Registers a new task, specifying its dependencies and optional additional information.

        Args:
            dependency_task_id: A list of IDs representing tasks that this task depends on.
            extra: Optional additional information associated with the task.

        Returns:
            int: The ID of the newly added task.


        """

        with self.task_lock:
            depend_tasks = [
                self.task_dict[task_id]
                for task_id in dependency_task_id
                if task_id in self.task_dict
            ]
            self.task_dict[self.now_id] = Task(
                task_id=self.now_id, dependencies=depend_tasks, extra_info=extra
            )
            self.now_id += 1
            return self.now_id - 1

    def get_next_task(self, process_id: int):
        """
        Retrieves a ready-to-execute task for a specified process, considering dependencies and current status. Returns the task and its ID, or (None, -1) if no suitable task is found.

        Args:
            process_id: The ID of the process requesting a task.

        Returns:
            tuple: A tuple containing the task object and its ID. Returns (None, -1) if no task is available.


        """

        with self.task_lock:
            self.query_id += 1
            for task_id in self.task_dict.keys():
                ready = (
                    len(self.task_dict[task_id].dependencies) == 0
                    and self.task_dict[task_id].status == 0
                )
                if ready:
                    self.task_dict[task_id].status = 1
                    print(
                        f"{Fore.RED}[process {process_id}]{Style.RESET_ALL}: get task({task_id}), remain({len(self.task_dict)})"
                    )
                    return (self.task_dict[task_id], task_id)
            return (None, -1)

    def mark_completed(self, task_id: int):
        """
        Removes a task and updates any dependent tasks by removing it from their dependency lists.

        Args:
            task_id: The ID of the task to mark as completed.

        Returns:
            None


        """

        with self.task_lock:
            target_task = self.task_dict[task_id]
            for task in self.task_dict.values():
                if target_task in task.dependencies:
                    task.dependencies.remove(target_task)
            self.task_dict.pop(task_id)


def worker(task_manager, process_id: int, handler: Callable):
    """
    Process that repeatedly fetches tasks and executes a provided handler on their associated data, until all tasks are successfully completed.

    Args:
        task_manager: The task manager object providing access to tasks.
        process_id: The ID of the current worker process.
        handler: A callable that processes the extra information from a task.

    Returns:
        None


    """

    while True:
        if task_manager.all_success:
            return
        task, task_id = task_manager.get_next_task(process_id)
        if task is None:
            time.sleep(0.5)
            continue
        handler(task.extra_info)
        task_manager.mark_completed(task.task_id)
