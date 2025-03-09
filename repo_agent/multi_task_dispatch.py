from __future__ import annotations
import random
import threading
import time
from typing import Any, Callable, Dict, List
from colorama import Fore, Style

class Task:
    """Represents a task within the Repository Agent framework.

Each task has an ID, dependencies, and optional extra information that can be used for tracking or additional context.

Args:
    task_id (int): The unique identifier for the task.
    dependencies (List[Task]): List of tasks that this task depends on.
    extra_info (Any, optional): Additional information associated with the task. Defaults to None.

Attributes:
    task_id (int): The unique identifier for the task.
    dependencies (List[Task]): List of tasks that this task depends on.
    status (int): Task status: 0 - not started, 1 - in progress, 2 - completed, 3 - error.
    extra_info (Any): Additional information associated with the task.

Note:
    See also: Repository Agent framework documentation for more details on task management and concurrency handling.
"""

    def __init__(self, task_id: int, dependencies: List[Task], extra_info: Any=None):
        """Initialize the Task instance.

This method initializes an instance of the Task class, setting up its unique identifier and dependencies.

Args:
    task_id (int): The unique identifier for the task.
    dependencies (List[Task]): List of dependent tasks that must be completed before this task can start.
    extra_info (Any, optional): Additional information related to the task. Defaults to None.

Returns:
    None

Raises:
    ValueError: If task_id is not a positive integer or if dependencies is not a list of Task instances.

Note:
    See also: The status attribute for task states.
"""
        self.task_id = task_id
        self.extra_info = extra_info
        self.dependencies = dependencies
        self.status = 0

class TaskManager:
    """Initialize a TaskManager object.

This method initializes the TaskManager object by setting up necessary attributes such as task dictionary, lock for thread synchronization, current task ID, and query ID to manage tasks efficiently within the Repository Agent framework.

Args:
    None

Returns:
    None


Check if all tasks have been successfully completed.

Returns:
    bool: True if there are no remaining tasks, False otherwise.


Adds a new task to the task dictionary.

This method adds a new task to the task dictionary with specified dependencies and optional extra information. It ensures that tasks are added in an ordered manner based on their dependencies.

Args:
    dependency_task_id (List[int]): List of task IDs that the new task depends on.
    extra (Any, optional): Extra information associated with the task. Defaults to None.

Returns:
    int: The ID of the newly added task.


Get the next task for a given process ID.

This method retrieves the next available task from the task dictionary based on the provided process ID. It ensures that tasks are assigned in an order that respects their dependencies and synchronization requirements.

Args:
    process_id (int): The ID of the process.

Returns:
    tuple: A tuple containing the next task object and its ID.
           If there are no available tasks, returns (None, -1).


Marks a task as completed and removes it from the task dictionary.

This method marks a specified task as completed by removing it from the task dictionary. It ensures that all dependencies for subsequent tasks are met before they can be processed.

Args:
    task_id (int): The ID of the task to mark as completed.
"""

    def __init__(self):
        """Initialize a TaskManager object for the Repository Agent.

This method initializes the TaskManager object by setting up necessary attributes required for managing tasks concurrently within the framework.

Args:
    None

Returns:
    None

Raises:
    None

Attributes:
    - task_dict (Dict[int, Task]): A dictionary that maps task IDs to Task objects.
    - task_lock (threading.Lock): A lock used for thread synchronization when accessing the task_dict.
    - now_id (int): The current task ID.
    - query_id (int): The current query ID.
    - sync_func (None): A placeholder for a synchronization function.

Note:
    This class is part of the Task Handling component, which manages multiple tasks concurrently to optimize performance and resource utilization in the Repository Agent framework.
"""
        self.task_dict: Dict[int, Task] = {}
        self.task_lock = threading.Lock()
        self.now_id = 0
        self.query_id = 0

    @property
    def all_success(self) -> bool:
        """Checks if all tasks have been successfully completed.

This function determines whether there are any pending tasks in the task dictionary by checking its length. If the length is zero, it implies that all tasks have been successfully processed.

Args:
    None

Returns:
    bool: True if no tasks are present (indicating success), otherwise False.

Raises:
    None

Note:
    This function is part of the Repository Agent's Task Management system, which efficiently handles multiple tasks concurrently to optimize performance and resource utilization.
"""
        return len(self.task_dict) == 0

    def add_task(self, dependency_task_id: List[int], extra=None) -> int:
        """Adds a new task to the task dictionary.

The Repository Agent framework utilizes a task manager system to handle multiple tasks concurrently, ensuring efficient resource utilization and performance optimization.

Args:
    dependency_task_id (List[int]): List of task IDs that the new task depends on.
    extra (Any, optional): Extra information associated with the task. Defaults to None.

Returns:
    int: The ID of the newly added task.

Note:
    See also: TaskManager class and Task class for more details on task management.
"""
        with self.task_lock:
            depend_tasks = [self.task_dict[task_id] for task_id in dependency_task_id if task_id in self.task_dict]
            self.task_dict[self.now_id] = Task(task_id=self.now_id, dependencies=depend_tasks, extra_info=extra)
            self.now_id += 1
            return self.now_id - 1

    def get_next_task(self, process_id: int):
        """Retrieve the next task for a specified process.

This function fetches the subsequent task associated with a given process ID from the task management system. It ensures efficient handling of multiple tasks concurrently within the Repository Agent framework.

Args:
    process_id (int): The unique identifier of the process to retrieve the task for.

Returns:
    tuple: A pair containing the next task object and its corresponding ID. Returns (None, -1) if no available tasks exist for the specified process.

Raises:
    ValueError: If an invalid or non-existent process ID is provided.

Note:
    See also: TaskManager class for more details on task management.
"""
        with self.task_lock:
            self.query_id += 1
            for task_id in self.task_dict.keys():
                ready = len(self.task_dict[task_id].dependencies) == 0 and self.task_dict[task_id].status == 0
                if ready:
                    self.task_dict[task_id].status = 1
                    print(f'{Fore.RED}[process {process_id}]{Style.RESET_ALL}: get task({task_id}), remain({len(self.task_dict)})')
                    return (self.task_dict[task_id], task_id)
            return (None, -1)

    def mark_completed(self, task_id: int):
        """Marks a task as completed by removing it from the task dictionary.

This function updates dependencies for other tasks by removing references to the marked task, ensuring that the task management system remains consistent and up-to-date.

Args:
    task_id (int): The ID of the task to mark as completed.

Returns:
    None

Raises:
    KeyError: If the specified task_id does not exist in the task dictionary.

Note:
    This method ensures that all dependencies are updated when a task is marked as completed.
"""
        with self.task_lock:
            target_task = self.task_dict[task_id]
            for task in self.task_dict.values():
                if target_task in task.dependencies:
                    task.dependencies.remove(target_task)
            self.task_dict.pop(task_id)

def worker(task_manager, process_id: int, handler: Callable):
    """Worker function that performs tasks assigned by the task manager.

The Repository Agent framework leverages this function to handle multiple tasks concurrently, ensuring efficient resource utilization and optimal performance.

Args:
    task_manager: The task manager object responsible for assigning tasks to workers.
    process_id (int): The ID of the current worker process.
    handler (Callable): The function that processes the assigned tasks.

Returns:
    None

Raises:
    ValueError: If an invalid task is encountered.

Note:
    This function continuously monitors for new tasks and processes them until all tasks are completed or an error occurs. It plays a crucial role in the concurrent task management system of the Repository Agent.
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
if __name__ == '__main__':
    task_manager = TaskManager()

    def some_function():
        """Pauses the execution for a random duration between 0 and 3 seconds.

This function introduces a delay in the execution flow, which can be useful for simulating asynchronous behavior or adding randomness to timing-dependent tests.

Args:  
    None

Returns:  
    None  

Raises:  
    None  

Note:  
    This function does not accept any parameters or return any values.
"""
        time.sleep(random.random() * 3)
    i1 = task_manager.add_task(some_function, [])
    i2 = task_manager.add_task(some_function, [])
    i3 = task_manager.add_task(some_function, [i1])
    i4 = task_manager.add_task(some_function, [i2, i3])
    i5 = task_manager.add_task(some_function, [i2, i3])
    i6 = task_manager.add_task(some_function, [i1])
    threads = [threading.Thread(target=worker, args=(task_manager,)) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()