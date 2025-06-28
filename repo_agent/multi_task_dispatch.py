from __future__ import annotations
import random
import threading
import time
from typing import Any, Callable, Dict, List
from colorama import Fore, Style


class Task:
    """
    Represents a task with dependencies and extra information."""

    def __init__(self, task_id: int, dependencies: List[Task], extra_info: Any = None):
        self.task_id = task_id
        self.extra_info = extra_info
        self.dependencies = dependencies
        self.status = 0


class TaskManager:
    """
    Manages a collection of tasks with dependencies and tracks their completion status.
    """

    def __init__(self):
        """
        Initializes the task management system with an empty dictionary to store tasks, a lock for thread safety, and initializes unique IDs for new tasks and queries.

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
        Checks if no tasks remain in the manager.

            Args:
                None

            Returns:
                bool: True if all tasks are successful (task_dict is empty), False otherwise.
        """

        return len(self.task_dict) == 0

    def add_task(self, dependency_task_id: List[int], extra=None) -> int:
        """
        Registers a new task with its dependencies and associated data. Each task receives a unique ID for tracking purposes.

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
        Assigns a ready-to-process task to the requesting process, marking it as in progress and returning its details. If no tasks are currently available, returns None.

            This method checks for tasks that have no remaining dependencies and are not yet assigned to a worker.
            It updates the task's status to 'assigned' when a suitable task is found.

            Args:
                process_id: The ID of the process requesting a task.

            Returns:
                tuple: A tuple containing the next available task object and its ID.
                       If no tasks are available, returns (None, -1).
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
        Removes a completed task and updates the dependency relationships of other tasks.

            Removes the completed task from the task dictionary and removes it
            from the dependency lists of other tasks.

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
    Executes tasks from a task manager until all tasks are successful.

        Args:
            task_manager: The task manager object providing access to tasks and completion status.
            process_id:  The ID of the worker process.
            handler: A callable that processes the extra information associated with each task.

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
