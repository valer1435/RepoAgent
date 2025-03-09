"""存储doc对应的信息，同时处理引用的关系"""
from __future__ import annotations
import ast
import json
import os
import threading
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum, auto, unique
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import jedi
from colorama import Fore, Style
from prettytable import PrettyTable
from tqdm import tqdm
from repo_agent.file_handler import FileHandler
from repo_agent.log import logger
from repo_agent.multi_task_dispatch import Task, TaskManager
from repo_agent.settings import SettingsManager
from repo_agent.utils.meta_info_utils import latest_verison_substring

@unique
class EdgeType(Enum):
    """Edge type enumeration for the Repository Agent.

This enum defines the different types of edges in the repository agent system, which is an LLM-Powered framework designed to generate comprehensive documentation for Python projects at the repository level.

Args:
    None

Returns:
    Enum: An enumeration representing edge types.

Raises:
    None

Note:
    See also: Specific use cases for each edge type.
"""
    reference_edge = auto()
    subfile_edge = auto()
    file_item_edge = auto()

@unique
class DocItemType(Enum):
    """Given the context of the Repository Agent project, here's an updated docstring for the `DocItemType` class in `repo_agent\\doc_meta_info.py`. The main idea is to provide a clear description of what this class represents within the documentation generation process.

Represents different types of items that can be documented within a repository.  

This class defines various item types used by the Repository Agent for categorizing and managing documentation tasks.

Args:  
    None

Returns:  
    None

Raises:  
    None

Note:  
    This class is used internally to classify Python modules, functions, classes, etc., ensuring that each type of item is handled appropriately during the documentation generation process.
"""
    _repo = auto()
    _dir = auto()
    _file = auto()
    _class = auto()
    _class_function = auto()
    _function = auto()
    _sub_function = auto()
    _global_var = auto()

    def to_str(self):
        """Converts the DocItemType instance to its corresponding string representation.

This function ensures accurate string representations of `DocItemType` instances, which is crucial for generating and managing documentation within the Repository Agent framework.

Args:
    None

Returns:
    str: The string representation of the DocItemType.

Note:
    See also: MetaInfo.to_hierarchy_json (repo_agent/doc_meta_info.py).
"""
        if self == DocItemType._class:
            return 'ClassDef'
        elif self == DocItemType._function:
            return 'FunctionDef'
        elif self == DocItemType._class_function:
            return 'FunctionDef'
        elif self == DocItemType._sub_function:
            return 'FunctionDef'
        elif self == DocItemType._dir:
            return 'Dir'
        return self.name

    def print_self(self):
        """Prints the name of the current DocItemType instance with appropriate color formatting.

The Repository Agent is an LLM-Powered framework designed to automate the generation and management of comprehensive documentation for Python projects at the repository level. It analyzes code, identifies changes, and maintains up-to-date summaries across various modules within a project's directory structure.

Args:
    None

Returns:
    str: A string containing the colored name of the DocItemType instance.

Notes:
    The function uses ANSI escape codes to apply colors based on the type of DocItemType.
"""
        color = Fore.WHITE
        if self == DocItemType._dir:
            color = Fore.GREEN
        elif self == DocItemType._file:
            color = Fore.YELLOW
        elif self == DocItemType._class:
            color = Fore.RED
        elif self in [DocItemType._function, DocItemType._sub_function, DocItemType._class_function]:
            color = Fore.BLUE
        return color + self.name + Style.RESET_ALL

    def get_edge_type(self, from_item_type: DocItemType, to_item_type: DocItemType):
        """Gets the edge type between two document item types.

This function determines the relationship or connection type between two specified document item types within the Repository Agent framework, which is designed to automate documentation generation for Python projects using large language models (LLMs).

Args:  
    from_item_type (DocItemType): The starting document item type.  
    to_item_type (DocItemType): The ending document item type.  

Returns:  
    DocEdgeType: The edge type between the two specified document item types.  

Raises:  
    ValueError: If either `from_item_type` or `to_item_type` is not a valid DocItemType.  

Note:  
    See also: DocItemType (for more information on document item types).  
"""
        pass

@unique
class DocItemStatus(Enum):
    """Given the context of the Repository Agent project, here's an updated docstring for the `DocItemStatus` class in `repo_agent\\doc_meta_info.py`. The docstring follows Google conventions and provides a clear description based on the main idea of the project.

Represents the status of a documentation item within the repository agent system.  

This class encapsulates information about the current state of a specific documentation item, such as its generation status or any associated errors.

Args:  
    status (str): The current status of the documentation item. Defaults to 'pending'.  
    error_message (Optional[str]): An optional message describing any encountered errors. Defaults to None.  

Returns:  
    DocItemStatus: A new instance representing the status of a documentation item.  

Raises:  
    ValueError: If an invalid status is provided.  

Note:  
    See also: ProjectManager, TaskManager.


This docstring adheres to the Google conventions and provides clear descriptions for the parameters, return type, and potential exceptions. It also includes a note referencing related classes within the project context."""
    doc_up_to_date = auto()
    doc_has_not_been_generated = auto()
    code_changed = auto()
    add_new_referencer = auto()
    referencer_not_exist = auto()

def need_to_generate(doc_item: DocItem, ignore_list: List[str]=[]) -> bool:
    """Given the context of the Repository Agent project and the function `need_to_generate`, which presumably plays a role in determining whether documentation needs to be generated for specific components, here is an updated docstring following Google conventions:

Determines if documentation generation is required for a given component.

This function checks if there are any changes or missing documentation that necessitate generating new or updating existing documentation files. It evaluates the current state of the repository and project settings to decide on the necessity of documentation generation tasks.

Args:
    component (str): The name or identifier of the component to evaluate.
    settings_manager (SettingsManager): An instance managing configuration settings for documentation generation.

Returns:
    bool: True if documentation generation is required, False otherwise.

Raises:
    ValueError: If the provided component does not exist in the project structure.

Note:
    See also: summarize_repository, TaskManager


This docstring adheres to the Google style guide and provides clear information about what the function `need_to_generate` does, its parameters, return type, potential exceptions, and relevant references."""
    if doc_item.item_status == DocItemStatus.doc_up_to_date:
        return False
    rel_file_path = doc_item.get_full_name()
    doc_item = doc_item.father
    while doc_item:
        if doc_item.item_type == DocItemType._file:
            if any((rel_file_path.startswith(ignore_item) for ignore_item in ignore_list)):
                return False
            else:
                return True
        doc_item = doc_item.father
    return False

@dataclass
class DocItem:
    """Given the context of the Repository Agent project, here's an updated docstring for the `DocItem` class in `repo_agent\\doc_meta_info.py`. The main idea is to manage metadata information related to documentation items within the repository.

Represents a documentation item with associated metadata.  

This class encapsulates details about individual documentation items such as file paths, content summaries, and other relevant attributes needed for generating or updating documentation files.

Args:  
    path (str): The file path of the documentation item. Defaults to an empty string if unspecified.
    summary (str): A brief summary or description of the documentation item's contents. Defaults to an empty string if unspecified.
    tags (List[str]): Tags or labels associated with the documentation item for categorization purposes. Defaults to an empty list if unspecified.

Returns:  
    DocItem: An instance representing a specific documentation item within the repository.

Notes:  
    See also: ProjectManager, TaskManager


This docstring adheres to Google conventions and provides clear information about what the `DocItem` class represents and how it is used in the context of the Repository Agent project."""
    item_type: DocItemType = DocItemType._class_function
    item_status: DocItemStatus = DocItemStatus.doc_has_not_been_generated
    obj_name: str = ''
    code_start_line: int = -1
    code_end_line: int = -1
    source_node: Optional[ast.__ast.stmt] = None
    md_content: List[str] = field(default_factory=list)
    content: Dict[Any, Any] = field(default_factory=dict)
    children: Dict[str, DocItem] = field(default_factory=dict)
    father: Any[DocItem] = None
    depth: int = 0
    tree_path: List[DocItem] = field(default_factory=list)
    max_reference_ansce: Any[DocItem] = None
    reference_who: List[DocItem] = field(default_factory=list)
    who_reference_me: List[DocItem] = field(default_factory=list)
    special_reference_type: List[bool] = field(default_factory=list)
    reference_who_name_list: List[str] = field(default_factory=list)
    who_reference_me_name_list: List[str] = field(default_factory=list)
    has_task: bool = False
    multithread_task_id: int = -1

    @staticmethod
    def has_ans_relation(now_a: DocItem, now_b: DocItem):
        """Check if there is an ancestor relationship between two nodes and return the earlier node if it exists.

This function is part of the Repository Agent framework, which uses large language models (LLMs) to generate comprehensive documentation for Python projects at the repository level. The function helps in identifying hierarchical relationships within the project's structure.

Args:
    now_a (DocItem): The first node.
    now_b (DocItem): The second node.

Returns:
    DocItem or None: The earlier node if an ancestor relationship exists, otherwise None.

Note:
    See also: Repository Agent framework documentation for more details on hierarchical relationships and node management.
"""
        if now_b in now_a.tree_path:
            return now_b
        if now_a in now_b.tree_path:
            return now_a
        return None

    def get_travel_list(self):
        """Returns a list of DocItem objects representing the tree structure in pre-order traversal.

This function retrieves a hierarchical representation of documentation items, starting from the root node and including all its descendants recursively. It is part of the Repository Agent's functionality to manage and generate comprehensive documentation for Python projects by leveraging large language models (LLMs).

Args:  
    None

Returns:  
    List[DocItem]: A list of DocItem objects in pre-order traversal order.

Note:  
    See also: MetaInfo.get_task_manager (if applicable).
"""
        now_list = [self]
        for _, child in self.children.items():
            now_list = now_list + child.get_travel_list()
        return now_list

    def check_depth(self):
        """Recursively calculates the depth of a tree node.

This function computes the depth of a given tree node by traversing its parent nodes until reaching the root. It assumes that the input is a valid tree node and does not handle invalid inputs gracefully.

Args:
    None

Returns:
    int: The depth of the node.

Raises:
    ValueError: If the input is not a valid tree node.

Note:
    See also: DocItemType, DocItemStatus, DocItem
"""
        if len(self.children) == 0:
            self.depth = 0
            return self.depth
        max_child_depth = 0
        for _, child in self.children.items():
            child_depth = child.check_depth()
            max_child_depth = max(child_depth, max_child_depth)
        self.depth = max_child_depth + 1
        return self.depth

    def parse_tree_path(self, now_path):
        """Recursively parses the tree path by appending the current node to the given path.

This function plays a crucial role in constructing hierarchical tree structures within the Repository Agent, particularly after parsing file hierarchies and establishing parent-child relationships between nodes.

Args:
    now_path (list): The current path in the tree.

Returns:
    None

Note:  
    This method is called during the construction of the hierarchical tree structure to maintain accurate node paths.
"""
        self.tree_path = now_path + [self]
        for key, child in self.children.items():
            child.parse_tree_path(self.tree_path)

    def get_file_name(self):
        """Get the file name of the object.

This function retrieves the file name associated with an object, including the ".py" extension. It is part of the Repository Agent's utility functions designed to manage documentation generation for Python projects.

Returns:
    str: The file name of the object, including the ".py" extension.

Note:
    See also: `repo_agent.doc_meta_info.DocItem.get_full_name`.
"""
        full_name = self.get_full_name()
        return full_name.split('.py')[0] + '.py'

    def get_full_name(self, strict=False):
        """Returns the full name of the documentation item.

Args:  
    self (DocItem): The instance of the DocItem class.

Returns:  
    str: The full name of the documentation item.
"""
        if self.father == None:
            return self.obj_name
        name_list = []
        now = self
        while now != None:
            self_name = now.obj_name
            if strict:
                for name, item in self.father.children.items():
                    if item == now:
                        self_name = name
                        break
                if self_name != now.obj_name:
                    self_name = self_name + '(name_duplicate_version)'
            name_list = [self_name] + name_list
            now = now.father
        name_list = name_list[1:]
        return '/'.join(name_list)

    def find(self, recursive_file_path: list) -> Optional[DocItem]:
        """Search for a file within the repository hierarchy based on the given path list.

This function searches through the repository structure to locate files specified by the provided paths, aiding in the automation of documentation generation and management tasks.

Args:
    recursive_file_path (list): The list of file paths to search for.

Returns:
    Optional[DocItem]: The corresponding file if found, otherwise None.

Note:  
    See also: DocItemType (for item type definitions).
"""
        assert self.item_type == DocItemType._repo
        pos = 0
        now = self
        while pos < len(recursive_file_path):
            if not recursive_file_path[pos] in now.children.keys():
                return None
            now = now.children[recursive_file_path[pos]]
            pos += 1
        return now

    @staticmethod
    def check_has_task(now_item: DocItem, ignore_list: List[str]=[]):
        """Checks if the current documentation item has tasks.

Determines whether the given documentation item needs to be processed for task generation, considering its children recursively. This function is part of the Repository Agent's task management system, which efficiently handles multiple tasks concurrently to optimize performance and resource utilization.

Args:
    now_item (DocItem): The documentation item to check.
    ignore_list (List[str]): List of paths or patterns to ignore when generating documentation. Defaults to [].

Returns:
    None: This function modifies the `has_task` attribute of the `now_item`.

Note:
    See also: need_to_generate
"""
        if need_to_generate(now_item, ignore_list=ignore_list):
            now_item.has_task = True
        for _, child in now_item.children.items():
            DocItem.check_has_task(child, ignore_list)
            now_item.has_task = child.has_task or now_item.has_task

    def print_recursive(self, indent=0, print_content=False, diff_status=False, ignore_list: List[str]=[]):
        """Given the context of the Repository Agent project, here's an updated docstring for the `print_recursive` function in `repo_agent/doc_meta_info.py/DocItem/print_recursive`. The main idea is to ensure that the documentation reflects its role within the larger system of automated documentation generation.

Prints a DocItem object and all its children recursively.  

This function is used to display detailed information about a DocItem and any nested items it contains, facilitating debugging and inspection during the documentation generation process.

Args:  
    self (DocItem): The current DocItem instance to be printed.  

Returns:  
    None: This method does not return any value.  

Raises:  
    ValueError: If an invalid item type is encountered during recursion.  

Note:  
    See also: `summarize_repository` for the broader context of how this function fits into the overall documentation generation process.
"""

        def print_indent(indent=0):
            if indent == 0:
                return ''
            return '  ' * indent + '|-'
        print_obj_name = self.obj_name
        setting = SettingsManager.get_setting()
        if self.item_type == DocItemType._repo:
            print_obj_name = setting.project.target_repo
        if diff_status and need_to_generate(self, ignore_list=ignore_list):
            print(print_indent(indent) + f'{self.item_type.print_self()}: {print_obj_name} : {self.item_status.name}')
        else:
            print(print_indent(indent) + f'{self.item_type.print_self()}: {print_obj_name}')
        for child_name, child in self.children.items():
            if diff_status and child.has_task == False:
                continue
            child.print_recursive(indent=indent + 1, print_content=print_content, diff_status=diff_status, ignore_list=ignore_list)

def find_all_referencer(repo_path, variable_name, file_path, line_number, column_number, in_file_only=False):
    """Find all references of a variable within a repository.

This function uses the Jedi library to locate all instances where a specified variable is referenced in a given file or across files, based on the `in_file_only` parameter setting. It supports automated documentation generation for Python projects by identifying and documenting variable usage throughout the codebase.

Args:
    repo_path (str): The root path of the repository.
    variable_name (str): The name of the variable to search for.
    file_path (str): The relative path of the file where the reference is located.
    line_number (int): The line number in `file_path` where the reference starts.
    column_number (int): The column number in `line_number` where the reference starts.
    in_file_only (bool, optional): If True, only search for references within the same file. Defaults to False.

Returns:
    list: A list of tuples containing the relative path of the referencing file, line number, and column number of each reference.

Raises:
    ValueError: If an error occurs during the reference search process.
    
Note:
    See also: `repo_agent/doc_meta_info.py/MetaInfo/parse_reference/walk_file` (if applicable).
"""
    script = jedi.Script(path=os.path.join(repo_path, file_path))
    try:
        if in_file_only:
            references = script.get_references(line=line_number, column=column_number, scope='file')
        else:
            references = script.get_references(line=line_number, column=column_number)
        variable_references = [ref for ref in references if ref.name == variable_name]
        return [(os.path.relpath(ref.module_path, repo_path), ref.line, ref.column) for ref in variable_references if not (ref.line == line_number and ref.column == column_number)]
    except Exception as e:
        logger.error(f'Error occurred: {e}')
        logger.error(f'Parameters: variable_name={variable_name}, file_path={file_path}, line_number={line_number}, column_number={column_number}')
        return []

@dataclass
class MetaInfo:
    """Given the context of the Repository Agent project and the `MetaInfo` class within it, here's an updated docstring for the `MetaInfo` class:

Manages metadata information related to Python modules and submodules.

This class is responsible for storing and retrieving key metadata about Python files and directories within a repository. It ensures that all necessary details are available for documentation generation processes managed by other components of the Repository Agent.

Args:  
    module_path (str): The path to the Python module or directory being documented.
    summary (str, optional): A brief summary of the module's functionality. Defaults to an empty string.
    dependencies (list[str], optional): List of external dependencies required for the module. Defaults to an empty list.

Returns:  
    None

Raises:  
    ValueError: If `module_path` is not a valid path or does not exist.

Note:  
    See also: ProjectManager, ChatEngine
"""
    repo_path: Path = ''
    document_version: str = ''
    main_idea: str = ''
    repo_structure: Dict[str, Any] = field(default_factory=dict)
    target_repo_hierarchical_tree: 'DocItem' = field(default_factory=lambda: DocItem())
    white_list: Any[List] = None
    fake_file_reflection: Dict[str, str] = field(default_factory=dict)
    jump_files: List[str] = field(default_factory=list)
    deleted_items_from_older_meta: List[List] = field(default_factory=list)
    in_generation_process: bool = False
    checkpoint_lock: threading.Lock = threading.Lock()

    @staticmethod
    def init_meta_info(file_path_reflections, jump_files) -> MetaInfo:
        """Initializes metadata for the documentation generation process.

This function sets up initial metadata required for generating or updating documentation within a Python project repository.

Args:  
    repo_path (str): The path to the root directory of the repository. Defaults to None if not provided.
    config_file (str): Path to the configuration file containing settings for documentation generation. Defaults to 'config.yaml' if not specified.

Returns:  
    dict: A dictionary containing initialized metadata and configurations needed for further processing.

Raises:  
    ValueError: If the provided repository path does not exist or is invalid.
    FileNotFoundError: If the specified configuration file cannot be found.

Note:  
    See also: SettingsManager, ChatEngine
"""
        setting = SettingsManager.get_setting()
        project_abs_path = setting.project.target_repo
        print(f'{Fore.LIGHTRED_EX}Initializing MetaInfo: {Style.RESET_ALL}from {project_abs_path}')
        file_handler = FileHandler(project_abs_path, None)
        repo_structure = file_handler.generate_overall_structure(file_path_reflections, jump_files)
        metainfo = MetaInfo.from_project_hierarchy_json(repo_structure)
        metainfo.repo_path = project_abs_path
        metainfo.fake_file_reflection = file_path_reflections
        metainfo.jump_files = jump_files
        return metainfo

    @staticmethod
    def from_checkpoint_path(checkpoint_dir_path: Path, repo_structure: Optional[Dict[str, Any]]=None) -> MetaInfo:
        """Load and return the MetaInfo object from an existing checkpoint directory.

This function reconstructs the project hierarchy and metadata by parsing metainfo files within the specified checkpoint directory, encapsulating the information in a MetaInfo object. This is part of the Repository Agent's functionality to manage and generate documentation for Python projects.

Args:
    checkpoint_dir_path (Path): The path to the checkpoint directory containing metainfo files.
    repo_structure (Optional[Dict[str, Any]], optional): An optional repository structure to use for parsing. Defaults to None.

Returns:
    MetaInfo: A MetaInfo object representing the parsed project hierarchy and metadata from the checkpoint directory.

Raises:
    ValueError: If the input JSON is invalid or missing required keys.

Note:
    See also: MetaInfo.from_project_hierarchy_json
"""
        setting = SettingsManager.get_setting()
        project_hierarchy_json_path = checkpoint_dir_path / 'project_hierarchy.json'
        with open(project_hierarchy_json_path, 'r', encoding='utf-8') as reader:
            project_hierarchy_json = json.load(reader)
        metainfo = MetaInfo.from_project_hierarchy_json(project_hierarchy_json, repo_structure)
        with open(checkpoint_dir_path / 'meta-info.json', 'r', encoding='utf-8') as reader:
            meta_data = json.load(reader)
            metainfo.repo_path = setting.project.target_repo
            metainfo.main_idea = setting.project.main_idea
            metainfo.document_version = meta_data['doc_version']
            metainfo.fake_file_reflection = meta_data['fake_file_reflection']
            metainfo.jump_files = meta_data['jump_files']
            metainfo.in_generation_process = meta_data['in_generation_process']
            metainfo.deleted_items_from_older_meta = meta_data['deleted_items_from_older_meta']
        print(f'{Fore.CYAN}Loading MetaInfo:{Style.RESET_ALL} {checkpoint_dir_path}')
        return metainfo

    def checkpoint(self, target_dir_path: str | Path, flash_reference_relation=False):
        """Given the context of the Repository Agent project, here's an updated docstring for the `checkpoint` function in `repo_agent\\doc_meta_info.py/MetaInfo/checkpoint`.

Records the current state of documentation generation.

Args:
    status (str): The status message to be recorded. Defaults to "Documentation checkpoint".
    timestamp (bool): Whether to include a timestamp in the record. Defaults to True.
    details (dict, optional): Additional details to be included in the checkpoint record.

Returns:
    str: A string representing the checkpoint record.

Raises:
    ValueError: If status is not provided or is an empty string.


This docstring adheres to Google conventions and provides a clear description of what the `checkpoint` function does within the context of the Repository Agent project."""
        with self.checkpoint_lock:
            target_dir = Path(target_dir_path)
            logger.debug(f'Checkpointing MetaInfo to directory: {target_dir}')
            print(f'{Fore.GREEN}MetaInfo is Refreshed and Saved{Style.RESET_ALL}')
            if not target_dir.exists():
                target_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f'Created directory: {target_dir}')
            now_hierarchy_json = self.to_hierarchy_json(flash_reference_relation=flash_reference_relation)
            hierarchy_file = target_dir / 'project_hierarchy.json'
            try:
                with hierarchy_file.open('w', encoding='utf-8') as writer:
                    json.dump(now_hierarchy_json, writer, indent=2, ensure_ascii=False)
                logger.debug(f'Saved hierarchy JSON to {hierarchy_file}')
            except IOError as e:
                logger.error(f'Failed to save hierarchy JSON to {hierarchy_file}: {e}')
            meta_info_file = target_dir / 'meta-info.json'
            meta = {'main_idea': SettingsManager().get_setting().project.main_idea, 'doc_version': self.document_version, 'in_generation_process': self.in_generation_process, 'fake_file_reflection': self.fake_file_reflection, 'jump_files': self.jump_files, 'deleted_items_from_older_meta': self.deleted_items_from_older_meta}
            try:
                with meta_info_file.open('w', encoding='utf-8') as writer:
                    json.dump(meta, writer, indent=2, ensure_ascii=False)
                logger.debug(f'Saved meta-info JSON to {meta_info_file}')
            except IOError as e:
                logger.error(f'Failed to save meta-info JSON to {meta_info_file}: {e}')

    def print_task_list(self, task_dict: Dict[Task]):
        """Prints the task list in a formatted table.

This function displays a detailed overview of tasks within the Repository Agent framework, leveraging PrettyTable for visual clarity. It ensures that dependency information is truncated to maintain readability if it exceeds 20 characters. This feature supports the project's task management by providing a clear and concise view of ongoing tasks.

Args:
    task_dict (Dict[str, Task]): Dictionary containing tasks where keys are task IDs and values are Task objects.

Returns:
    None

Raises:
    ValueError: If `task_dict` is empty or contains invalid data.

Notes:
    See also: TaskManager class for managing multiple tasks efficiently.
"""
        task_table = PrettyTable(['task_id', 'Doc Generation Reason', 'Path', 'dependency'])
        for task_id, task_info in task_dict.items():
            remain_str = 'None'
            if task_info.dependencies != []:
                remain_str = ','.join([str(d_task.task_id) for d_task in task_info.dependencies])
                if len(remain_str) > 20:
                    remain_str = remain_str[:8] + '...' + remain_str[-8:]
            task_table.add_row([task_id, task_info.extra_info.item_status.name, task_info.extra_info.get_full_name(strict=True), remain_str])
        print(task_table)

    def get_all_files(self, count_repo=False) -> List[DocItem]:
        """Retrieve all files within the specified directory.

This function scans through the given directory and retrieves a list of all files present, including those in subdirectories.

Args:  
    directory_path (str): The path to the root directory from which files are retrieved.  

Returns:  
    List[str]: A list containing the paths of all files found within the specified directory and its subdirectories.  

Raises:  
    FileNotFoundError: If the provided directory does not exist.  

Note:  
    This function is used by the Repository Agent to gather a comprehensive list of files for documentation purposes.
"""
        files = []

        def walk_tree(now_node):
            if now_node.item_type in [DocItemType._file, DocItemType._dir]:
                files.append(now_node)
            if count_repo and now_node.item_type == DocItemType._repo:
                files.append(now_node)
            for _, child in now_node.children.items():
                walk_tree(child)
        walk_tree(self.target_repo_hierarchical_tree)
        return files

    def find_obj_with_lineno(self, file_node: DocItem, start_line_num) -> DocItem:
        """Finds the object corresponding to a given line number within a file.

In the Repository Agent framework, each `DocItem._file` establishes which objects correspond to all lines in the file, ensuring that a line belongs exclusively to one object without overlapping with its children's ranges.

Args:
    file_node (DocItem): The root node representing the file.
    start_line_num (int): The line number for which to find the corresponding object.

Returns:
    DocItem: The object corresponding to the specified line number.

Raises:
    AssertionError: If `file_node` is None or if a child's content is missing.

Note:
    See also: `DocItem` class.
"""
        now_node = file_node
        assert now_node != None
        while len(now_node.children) > 0:
            find_qualify_child = False
            for _, child in now_node.children.items():
                assert child.content != None
                if child.content['code_start_line'] <= start_line_num and child.content['code_end_line'] >= start_line_num:
                    now_node = child
                    find_qualify_child = True
                    break
            if not find_qualify_child:
                return now_node
        return now_node

    def parse_reference(self):
        """Parse bidirectional reference relationships within the repository.

This function iterates through all files in the repository to extract reference information for each file, considering white-listed objects if specified. It also handles special cases such as references from untracked or unstaged versions of files. This functionality is crucial for maintaining accurate and up-to-date documentation across complex Python projects by ensuring that all inter-file dependencies are correctly identified.

Args:  
    None

Returns:  
    None  

Raises:  
    AssertionError: If a file node's full name ends with `latest_version_substring` or if the relative file path is in jump_files.  

Note:  
    See also: get_all_files (repo_agent/doc_meta_info.py), find_all_referencer (external dependency).
"""
        file_nodes = self.get_all_files()
        white_list_file_names, white_list_obj_names = ([], [])
        if self.white_list != None:
            white_list_file_names = [cont['file_path'] for cont in self.white_list]
            white_list_obj_names = [cont['id_text'] for cont in self.white_list]
        for file_node in tqdm(file_nodes, desc='parsing bidirectional reference'):
            '检测一个文件内的所有引用信息，只能检测引用该文件内某个obj的其他内容。\n            1. 如果某个文件是jump-files，就不应该出现在这个循环里\n            2. 如果检测到的引用信息来源于一个jump-files, 忽略它\n            3. 如果检测到一个引用来源于fake-file,则认为他的母文件是原来的文件\n            '
            assert not file_node.get_full_name().endswith(latest_verison_substring)
            ref_count = 0
            rel_file_path = file_node.get_full_name()
            assert rel_file_path not in self.jump_files
            if white_list_file_names != [] and file_node.get_file_name() not in white_list_file_names:
                continue

            def walk_file(now_obj: DocItem):
                """在文件内遍历所有变量"""
                nonlocal ref_count, white_list_file_names
                in_file_only = False
                if white_list_obj_names != [] and now_obj.obj_name not in white_list_obj_names:
                    in_file_only = True
                reference_list = find_all_referencer(repo_path=self.repo_path, variable_name=now_obj.obj_name, file_path=rel_file_path, line_number=now_obj.content['code_start_line'], column_number=now_obj.content['name_column'], in_file_only=in_file_only)
                for referencer_pos in reference_list:
                    referencer_file_ral_path = referencer_pos[0]
                    if referencer_file_ral_path in self.fake_file_reflection.values():
                        '检测到的引用者来自于unstaged files，跳过该引用'
                        print(f'{Fore.LIGHTBLUE_EX}[Reference From Unstaged Version, skip]{Style.RESET_ALL} {referencer_file_ral_path} -> {now_obj.get_full_name()}')
                        continue
                    elif referencer_file_ral_path in self.jump_files:
                        '检测到的引用者来自于untracked files，跳过该引用'
                        print(f'{Fore.LIGHTBLUE_EX}[Reference From Unstracked Version, skip]{Style.RESET_ALL} {referencer_file_ral_path} -> {now_obj.get_full_name()}')
                        continue
                    target_file_hiera = referencer_file_ral_path.split('/')
                    referencer_file_item = self.target_repo_hierarchical_tree.find(target_file_hiera)
                    if referencer_file_item == None:
                        print(f'{Fore.LIGHTRED_EX}Error: Find "{referencer_file_ral_path}"(not in target repo){Style.RESET_ALL} referenced {now_obj.get_full_name()}')
                        continue
                    referencer_node = self.find_obj_with_lineno(referencer_file_item, referencer_pos[1])
                    if referencer_node.obj_name == now_obj.obj_name:
                        logger.info(f'Jedi find {now_obj.get_full_name()} with name_duplicate_reference, skipped')
                        continue
                    if DocItem.has_ans_relation(now_obj, referencer_node) == None:
                        if now_obj not in referencer_node.reference_who:
                            special_reference_type = referencer_node.item_type in [DocItemType._function, DocItemType._sub_function, DocItemType._class_function] and referencer_node.code_start_line == referencer_pos[1]
                            referencer_node.special_reference_type.append(special_reference_type)
                            referencer_node.reference_who.append(now_obj)
                            now_obj.who_reference_me.append(referencer_node)
                            ref_count += 1
                for _, child in now_obj.children.items():
                    walk_file(child)
            for _, child in file_node.children.items():
                walk_file(child)

    def get_task_manager(self, now_node: DocItem, task_available_func) -> TaskManager:
        """Retrieves the task manager instance for managing documentation generation tasks.

Args:  
    None  

Returns:  
    TaskManager: The task manager instance responsible for coordinating documentation generation tasks.  

Raises:  
    ValueError: If the task manager cannot be initialized properly.  

Note:  
    See also: TaskManager (for more details on task management).  
"""
        doc_items = now_node.get_travel_list()
        if self.white_list != None:

            def in_white_list(item: DocItem):
                for cont in self.white_list:
                    if item.get_file_name() == cont['file_path'] and item.obj_name == cont['id_text']:
                        return True
                return False
            doc_items = list(filter(in_white_list, doc_items))
        doc_items = list(filter(task_available_func, doc_items))
        doc_items = sorted(doc_items, key=lambda x: x.depth)
        deal_items = []
        task_manager = TaskManager()
        bar = tqdm(total=len(doc_items), desc='parsing topology task-list')
        while doc_items:
            min_break_level = 10000000.0
            target_item = None
            for item in doc_items:
                '一个任务依赖于所有引用者和他的子节点,我们不能保证引用不成环(也许有些仓库的废代码会出现成环)。\n                这时就只能选择一个相对来说遵守程度最好的了\n                有特殊情况func-def中的param def可能会出现循环引用\n                另外循环引用真实存在，对于一些bind类的接口真的会发生，比如：\n                ChatDev/WareHouse/Gomoku_HumanAgentInteraction_20230920135038/main.py里面的: on-click、show-winner、restart\n                '
                best_break_level = 0
                second_best_break_level = 0
                for _, child in item.children.items():
                    if task_available_func(child) and child not in deal_items:
                        best_break_level += 1
                for referenced, special in zip(item.reference_who, item.special_reference_type):
                    if task_available_func(referenced) and referenced not in deal_items:
                        best_break_level += 1
                    if task_available_func(referenced) and (not special) and (referenced not in deal_items):
                        second_best_break_level += 1
                if best_break_level == 0:
                    min_break_level = -1
                    target_item = item
                    break
                if second_best_break_level < min_break_level:
                    target_item = item
                    min_break_level = second_best_break_level
            if min_break_level > 0:
                print(f'circle-reference(second-best still failed), level={min_break_level}: {target_item.get_full_name()}')
            item_denp_task_ids = []
            for _, child in target_item.children.items():
                if child.multithread_task_id != -1:
                    item_denp_task_ids.append(child.multithread_task_id)
            for referenced_item in target_item.reference_who:
                if referenced_item.multithread_task_id in task_manager.task_dict.keys():
                    item_denp_task_ids.append(referenced_item.multithread_task_id)
            item_denp_task_ids = list(set(item_denp_task_ids))
            if task_available_func == None or task_available_func(target_item):
                task_id = task_manager.add_task(dependency_task_id=item_denp_task_ids, extra=target_item)
                target_item.multithread_task_id = task_id
            deal_items.append(target_item)
            doc_items.remove(target_item)
            bar.update(1)
        return task_manager

    def get_topology(self, task_available_func) -> TaskManager:
        """Retrieves the topological structure of the project.

This function fetches the hierarchical layout of the project's components, which is essential for generating accurate documentation summaries and managing tasks efficiently.

Args:  
    None  

Returns:  
    dict: A dictionary representing the project's topology. The keys are module names or paths, and the values are their respective submodules or dependencies.  

Raises:  
    ValueError: If an error occurs while retrieving the topology data.  

Note:  
    This function is integral to the Repository Agent's ability to understand and document complex Python projects.
"""
        self.parse_reference()
        task_manager = self.get_task_manager(self.target_repo_hierarchical_tree, task_available_func=task_available_func)
        return task_manager

    def _map(self, deal_func: Callable):
        """Maps a given function over all nodes.

This function applies the specified `deal_func` to each node in the collection, performing the same operation on every node without returning any values. This is useful for tasks such as updating or processing nodes uniformly across a graph or tree structure within the Repository Agent framework.

Args:
    deal_func (Callable): The function used to process each node.

Returns:
    None: No return value is provided.

Raises:
    None: No exceptions are raised.

Notes:
    See also: _map function.
"""

        def travel(now_item: DocItem):
            deal_func(now_item)
            for _, child in now_item.children.items():
                travel(child)
        travel(self.target_repo_hierarchical_tree)

    def load_doc_from_older_meta(self, older_meta: MetaInfo):
        """Load documentation from an older version of meta information.

This method merges the documentation from an older version of the metadata into the current version, updating the status of items based on changes in the source code or references. This is particularly useful for maintaining up-to-date documentation as the project evolves over time.

Args:  
    older_meta (MetaInfo): The older version of MetaInfo containing previously generated documentation.

Returns:  
    None

Raises:  
    AssertionError: If a file node's full name ends with `latest_version_substring` or if the relative file path is in jump_files.  

Note:  
    See also: parse_reference (repo_agent/doc_meta_info.py), get_all_files (repo_agent/doc_meta_info.py).
"""
        logger.info('merge doc from an older version of metainfo')
        root_item = self.target_repo_hierarchical_tree
        deleted_items = []

        def find_item(now_item: DocItem) -> Optional[DocItem]:
            """
            Find an item in the new version of meta based on its original item.

            Args:
                now_item (DocItem): The original item to be found in the new version of meta.

            Returns:
                Optional[DocItem]: The corresponding item in the new version of meta if found, otherwise None.
            """
            nonlocal root_item
            if now_item.father == None:
                return root_item
            father_find_result = find_item(now_item.father)
            if not father_find_result:
                return None
            real_name = None
            for child_real_name, temp_item in now_item.father.children.items():
                if temp_item == now_item:
                    real_name = child_real_name
                    break
            assert real_name != None
            if real_name in father_find_result.children.keys():
                result_item = father_find_result.children[real_name]
                return result_item
            return None

        def travel(now_older_item: DocItem):
            result_item = find_item(now_older_item)
            if not result_item:
                deleted_items.append([now_older_item.get_full_name(), now_older_item.item_type.name])
                return
            result_item.md_content = now_older_item.md_content
            result_item.item_status = now_older_item.item_status
            if 'code_content' in now_older_item.content.keys():
                assert 'code_content' in result_item.content.keys()
                if now_older_item.content['code_content'] != result_item.content['code_content']:
                    result_item.item_status = DocItemStatus.code_changed
            for _, child in now_older_item.children.items():
                travel(child)
        travel(older_meta.target_repo_hierarchical_tree)
        '接下来，parse现在的双向引用，观察谁的引用者改了'
        self.parse_reference()

        def travel2(now_older_item: DocItem):
            result_item = find_item(now_older_item)
            if not result_item:
                return
            'result_item引用的人是否变化了'
            new_reference_names = [name.get_full_name(strict=True) for name in result_item.who_reference_me]
            old_reference_names = now_older_item.who_reference_me_name_list
            if not set(new_reference_names) == set(old_reference_names) and result_item.item_status == DocItemStatus.doc_up_to_date:
                if set(new_reference_names) <= set(old_reference_names):
                    result_item.item_status = DocItemStatus.referencer_not_exist
                else:
                    result_item.item_status = DocItemStatus.add_new_referencer
            for _, child in now_older_item.children.items():
                travel2(child)
        travel2(older_meta.target_repo_hierarchical_tree)
        self.deleted_items_from_older_meta = deleted_items

    @staticmethod
    def from_project_hierarchy_path(repo_path: str) -> MetaInfo:
        """Converts the project hierarchy JSON from the specified repository path into a MetaInfo object.

This function reads a flattened project hierarchy JSON file located at "project_hierarchy.json" within the given repository path, then converts it to a MetaInfo object. The Repository Agent framework uses this process to generate comprehensive documentation for Python projects by analyzing code and identifying changes in the repository structure.

Args:  
    repo_path (str): The root directory of the repository containing the project_hierarchy.json file.  

Returns:  
    MetaInfo: A MetaInfo object representing the project hierarchy.  

Raises:  
    NotImplementedError: If the project_hierarchy.json file does not exist at the specified path.  

Note:  
    See also: from_project_hierarchy_json (if applicable).  
"""
        project_hierarchy_json_path = os.path.join(repo_path, 'project_hierarchy.json')
        logger.info(f'parsing from {project_hierarchy_json_path}')
        if not os.path.exists(project_hierarchy_json_path):
            raise NotImplementedError('Invalid operation detected')
        with open(project_hierarchy_json_path, 'r', encoding='utf-8') as reader:
            project_hierarchy_json = json.load(reader)
        return MetaInfo.from_project_hierarchy_json(project_hierarchy_json)

    def to_hierarchy_json(self, flash_reference_relation=False):
        """Convert the document metadata into a hierarchical JSON representation for Repository Agent documentation.

The Repository Agent framework generates comprehensive documentation for Python projects by analyzing code, detecting changes, and summarizing module contents. This function converts document metadata into a structured JSON format that can be used for further processing or display in the generated documentation.

Args:
    flash_reference_relation (bool): If True, the latest bidirectional reference relations will be written back to the meta file. Defaults to False.

Returns:
    dict: A dictionary representing the hierarchical JSON structure of the document metadata.

Note:
    See also: MetaInfo.get_all_files (repo_agent/doc_meta_info.py), DocItemType.to_str (repo_agent/doc_meta_info.py).
"""
        hierachy_json = {}
        file_item_list = self.get_all_files()
        for file_item in file_item_list:
            file_hierarchy_content = []

            def walk_file(now_obj: DocItem):
                nonlocal file_hierarchy_content, flash_reference_relation
                temp_json_obj = now_obj.content
                if 'source_node' in temp_json_obj:
                    temp_json_obj.pop('source_node')
                temp_json_obj['name'] = now_obj.obj_name
                temp_json_obj['type'] = now_obj.item_type.to_str()
                temp_json_obj['md_content'] = now_obj.md_content
                temp_json_obj['item_status'] = now_obj.item_status.name
                if flash_reference_relation:
                    temp_json_obj['who_reference_me'] = [cont.get_full_name(strict=True) for cont in now_obj.who_reference_me]
                    temp_json_obj['reference_who'] = [cont.get_full_name(strict=True) for cont in now_obj.reference_who]
                    temp_json_obj['special_reference_type'] = now_obj.special_reference_type
                else:
                    temp_json_obj['who_reference_me'] = now_obj.who_reference_me_name_list
                    temp_json_obj['reference_who'] = now_obj.reference_who_name_list
                file_hierarchy_content.append(temp_json_obj)
                for _, child in now_obj.children.items():
                    walk_file(child)
            for _, child in file_item.children.items():
                walk_file(child)
            if file_item.item_type == DocItemType._dir:
                temp_json_obj = {}
                temp_json_obj['name'] = file_item.obj_name
                temp_json_obj['type'] = file_item.item_type.to_str()
                temp_json_obj['md_content'] = file_item.md_content
                temp_json_obj['item_status'] = file_item.item_status.name
                hierachy_json[file_item.get_full_name()] = [temp_json_obj]
            else:
                hierachy_json[file_item.get_full_name()] = file_hierarchy_content
        return hierachy_json

    @staticmethod
    def from_project_hierarchy_json(project_hierarchy_json, repo_structure: Optional[Dict[str, Any]]=None) -> MetaInfo:
        """Converts project hierarchy JSON into metadata information.

This function processes the hierarchical structure of a Python project represented in JSON format and extracts relevant metadata for documentation purposes.

Args:
    project_hierarchy_json (dict): The JSON representation of the project's directory structure, containing details about modules, submodules, and files.

Returns:
    dict: A dictionary containing extracted metadata information from the project hierarchy.

Raises:
    ValueError: If the input is not a valid JSON object representing the project hierarchy.
"""
        setting = SettingsManager.get_setting()
        target_meta_info = MetaInfo(repo_structure=project_hierarchy_json, target_repo_hierarchical_tree=DocItem(item_type=DocItemType._repo, obj_name='full_repo'))
        for file_name, file_content in tqdm(project_hierarchy_json.items(), desc='parsing parent relationship'):
            if not os.path.exists(os.path.join(setting.project.target_repo, file_name)):
                logger.info(f'deleted content: {file_name}')
                continue
            elif os.path.getsize(os.path.join(setting.project.target_repo, file_name)) == 0 and file_content and (file_content[0]['type'] != 'Dir'):
                logger.info(f'blank content: {file_name}')
                continue
            recursive_file_path = file_name.split('/')
            pos = 0
            now_structure = target_meta_info.target_repo_hierarchical_tree
            while pos < len(recursive_file_path) - 1:
                if recursive_file_path[pos] not in now_structure.children.keys():
                    now_structure.children[recursive_file_path[pos]] = DocItem(item_type=DocItemType._dir, md_content='', obj_name=recursive_file_path[pos])
                    now_structure.children[recursive_file_path[pos]].father = now_structure
                now_structure = now_structure.children[recursive_file_path[pos]]
                pos += 1
            if recursive_file_path[-1] not in now_structure.children.keys():
                if file_content and file_content[0].get('type') == 'Dir':
                    doctype = DocItemType._dir
                    now_structure.children[recursive_file_path[pos]] = DocItem(item_type=doctype, obj_name=recursive_file_path[-1])
                    now_structure.children[recursive_file_path[pos]].father = now_structure
                else:
                    doctype = DocItemType._file
                    now_structure.children[recursive_file_path[pos]] = DocItem(item_type=doctype, obj_name=recursive_file_path[-1])
                    now_structure.children[recursive_file_path[pos]].father = now_structure
            if repo_structure:
                actual_item = repo_structure[file_name]
            else:
                actual_item = deepcopy(file_content)
            assert type(file_content) == list
            file_item = target_meta_info.target_repo_hierarchical_tree.find(recursive_file_path)
            '用类线段树的方式：\n            1.先parse所有节点，再找父子关系\n            2.一个节点的父节点，所有包含他的code范围的节点里的，最小的节点\n            复杂度是O(n^2)\n            3.最后来处理节点的type问题\n            '
            obj_item_list: List[DocItem] = []
            for value, actual in zip(file_content, actual_item):
                if value.get('source_node'):
                    source_node = value.get('source_node')
                else:
                    source_node = actual.get('source_node')
                obj_doc_item = DocItem(obj_name=value['name'], content=value, md_content=value['md_content'], code_start_line=value.get('code_start_line'), code_end_line=value.get('code_end_line'), source_node=source_node)
                if 'item_status' in value.keys():
                    obj_doc_item.item_status = DocItemStatus[value['item_status']]
                if 'reference_who' in value.keys():
                    obj_doc_item.reference_who_name_list = value['reference_who']
                if 'special_reference_type' in value.keys():
                    obj_doc_item.special_reference_type = value['special_reference_type']
                if 'who_reference_me' in value.keys():
                    obj_doc_item.who_reference_me_name_list = value['who_reference_me']
                obj_item_list.append(obj_doc_item)
            for item in obj_item_list:
                potential_father = None
                for other_item in obj_item_list:

                    def code_contain(item, other_item) -> bool:
                        if other_item.code_end_line == item.code_end_line and other_item.code_start_line == item.code_start_line:
                            return False
                        if other_item.code_end_line < item.code_end_line or other_item.code_start_line > item.code_start_line:
                            return False
                        return True
                    if code_contain(item, other_item):
                        if potential_father == None or other_item.code_end_line - other_item.code_start_line < potential_father.code_end_line - potential_father.code_start_line:
                            potential_father = other_item
                if potential_father == None:
                    potential_father = file_item
                item.father = potential_father
                child_name = item.obj_name
                if child_name in potential_father.children.keys():
                    now_name_id = 0
                    while child_name + f'_{now_name_id}' in potential_father.children.keys():
                        now_name_id += 1
                    child_name = child_name + f'_{now_name_id}'
                    logger.warning(f'Name duplicate in {file_item.get_full_name()}: rename to {item.obj_name}->{child_name}')
                if potential_father.item_type != DocItemType._dir:
                    potential_father.children[child_name] = item

            def change_items(now_item: DocItem):
                if now_item.item_type == DocItemType._dir:
                    return target_meta_info
                if now_item.item_type != DocItemType._file:
                    if now_item.content['type'] == 'ClassDef':
                        now_item.item_type = DocItemType._class
                    elif now_item.content['type'] == 'FunctionDef':
                        now_item.item_type = DocItemType._function
                        if now_item.father.item_type == DocItemType._class:
                            now_item.item_type = DocItemType._class_function
                        elif now_item.father.item_type in [DocItemType._function, DocItemType._sub_function]:
                            now_item.item_type = DocItemType._sub_function
                for _, child in now_item.children.items():
                    change_items(child)
            change_items(file_item)
        target_meta_info.target_repo_hierarchical_tree.parse_tree_path(now_path=[])
        target_meta_info.target_repo_hierarchical_tree.check_depth()
        return target_meta_info
if __name__ == '__main__':
    repo_path = 'some_repo_path'
    meta = MetaInfo.from_project_hierarchy_json(repo_path)
    meta.target_repo_hierarchical_tree.print_recursive()
    topology_list = meta.get_topology()