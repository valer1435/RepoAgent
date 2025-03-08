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
    '''"""EdgeType enumeration representing different types of edges within the repository documentation structure.

This enumeration defines various edge types used to model relationships between objects in a repository context, specifically for the purpose of generating comprehensive documentation. Each enumerated value represents a distinct kind of relationship:

- `reference_edge`: Represents an object referencing another object, crucial for tracking dependencies and interconnections within the project.
- `subfile_edge`: Indicates that a file or folder is contained within another folder, essential for organizing and visualizing the repository's hierarchical structure in documentation.
- `file_item_edge`: Signifies that an object belongs to a specific file, vital for associating individual items with their parent files during documentation generation.

Args:
    None

Returns:
    EdgeType: An instance of the EdgeType enumeration representing a specific edge type, used in the documentation process to accurately model relationships between repository items.

Raises:
    None

Note:
    This class is utilized internally within the Repository Documentation Generator framework to manage and interpret different types of relationships between repository items for the purpose of generating detailed and accurate documentation. It plays a pivotal role in defining how various components of a software project are interconnected and presented in the generated documentation.
"""'''
    reference_edge = auto()
    subfile_edge = auto()
    file_item_edge = auto()

@unique
class DocItemType(Enum):
    """
DocItemType: Represents the different types of documentation items within a repository.

This class encapsulates various categories of documentation, each identified by a unique string identifier. It serves as a crucial component in the Repository Documentation Generator, enabling precise management and generation of diverse documentation elements.

Args:
    item_type_str (str): The string identifier for the documentation type.

Returns:
    DocItemType: An instance of this class representing the specified documentation type.

Raises:
    ValueError: If the provided `item_type_str` is not a valid documentation type.

Note:
    See also: `EdgeType` in repo_agent\\doc_meta_info.py for related edge types within the repository structure.
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
        """
DocItem: The fundamental unit of documentation within the Repository Documentation Generator.

    Represents an individual piece of metadata or documentation content within a software project. It encapsulates various attributes such as type, status, and generation requirements, enabling comprehensive management and tracking of documentation items.

    Args:
        item_type (str): The category or kind of documentation this item represents (e.g., 'module', 'function', 'class').
        status (DocItemStatus): The current state of the documentation item (e.g., 'generated', 'needs_generation', 'obsolete').
        need_to_generate (bool): A flag indicating whether this item requires generation or updating.

    Returns:
        DocItem: An instance of DocItem with specified attributes.

    Raises:
        ValueError: If item_type is not a recognized documentation category, or if status is an invalid DocItemStatus enum value.

    Note:
        See also: The Repository Documentation Generator's comprehensive suite of features for automated and interactive documentation generation.
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
        """[Short one-line description].  

This function, `has_ans_relation`, is part of the Repository Documentation Generator's multi-task dispatch system, specifically designed to manage ancestor relationships within a hierarchical tree structure of documentation items (`DocItem`). It checks if there exists an ancestor relationship between two provided nodes (`now_a` and `now_b`), returning the earlier node if such a relationship is found; otherwise, it returns None.

[Longer description if needed].  

The Repository Documentation Generator is a sophisticated tool that automates the documentation process for software projects. It employs advanced techniques like chat-based interaction and multi-task dispatching to simplify the generation of documentation pages, summaries, and metadata. The `has_ans_relation` function operates within this broader context, contributing to the accurate representation of hierarchical relationships among documentation items.

Args:  
    now_a (DocItem): The first node in the hierarchical tree structure, representing a documentation item.
    now_b (DocItem): The second node in the hierarchical tree structure, also representing a documentation item.

Returns:  
    DocItem or None: Returns the earlier node if an ancestor relationship exists between `now_a` and `now_b`; otherwise, returns None.

Raises:  
    None: This function does not raise any exceptions. It simply returns a value or None based on the existence of an ancestor relationship.

Note:  
    See also: [DocItem class documentation](if_applicable) for more information on the DocItem structure and its attributes. This context is crucial for understanding the nature of `now_a` and `now_b`, as well as the implications of their ancestor relationship within the hierarchical tree structure."""
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
        """[Short one-line description]

This function retrieves a list of travel items associated with a specific document item, facilitating the generation of travel-related documentation.

[Longer description if needed.]

The `get_travel_list` function is designed to extract and return a list of travel-related metadata from a given document item within the repository. This functionality is integral to the Repository Documentation Generator's capability to produce comprehensive, up-to-date travel documentation for software projects. By leveraging this method, users can access detailed travel information tied to specific nodes in the repository's tree structure, thereby enhancing the accuracy and depth of generated travel-focused documentation pages, summaries, and metadata.

Args:
    doc_item (DocItem): The document item from which to extract travel-related metadata. This parameter should be an instance of the DocItem class, representing a node within the repository's tree structure.

Returns:
    list: A list containing all travel items associated with the provided `doc_item`. Each travel item is represented as a dictionary, encapsulating relevant metadata such as destination, duration, and purpose. The list is ordered according to the travel items' relevance or priority as defined within the repository's structure.

Raises:
    ValueError: If the provided `doc_item` argument is not an instance of the DocItem class.

Note:
    This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It specifically targets travel-related metadata extraction, contributing to the generation of detailed and accurate travel documentation pages, summaries, and metadata. Users typically interact with this function indirectly through higher-level calls within the generator's workflow, rather than directly invoking it in their code."""
        pass

@unique
class DocItemStatus(Enum):
    """[Converts the DocItemType enum value to its string representation].

This function is utilized within the `to_hierarchy_json` method of the MetaInfo class to ascertain the 'type' field in the JSON representation of document metadata items. It serves a crucial role in the Repository Documentation Generator, an automated tool designed for generating and updating documentation for software projects.

Args:
    None

Returns:  
    str: The string representation of the DocItemType enum value. This string corresponds to the type of document metadata item, facilitating accurate categorization within the JSON hierarchy.

Raises:  
    None

Note:  
    This function does not throw any exceptions under normal operation. It is a utility function that relies on the validity of its input (an instance of DocItemType enum).

    For comprehensive context on its usage and the broader functionality of the Repository Documentation Generator, refer to repo_agent\\doc_meta_info.py/MetaInfo/to_hierarchy_json.
"""
    doc_up_to_date = auto()
    doc_has_not_been_generated = auto()
    code_changed = auto()
    add_new_referencer = auto()
    referencer_not_exist = auto()

def need_to_generate(doc_item: DocItem, ignore_list: List[str]=[]) -> bool:
    """# Repository Documentation Generator: print_self Function

The `print_self` function is part of the Repository Documentation Generator, an automated tool designed to streamline the documentation process for software projects. This function contributes to the visual distinction of different types of DocItems when printing repository objects by returning a colored string representation of the DocItemType object's name based on its type.

## Description

This function returns a colored string representation of the `DocItemType` object's name, enhancing readability during the documentation process. The color of the string depends on the object's type: green for `_dir`, yellow for `_file`, red for `_class`, and blue for `_function`, `_sub_function`, or `_class_function`.

## Functionality

The `print_self` function is utilized in conjunction with the `print_recursive` method to visually differentiate various types of DocItems when printing repository objects. It does not alter any external state and does not raise exceptions under normal operation.

## Args

- `self (DocItemType)`: The `DocItemType` object whose name is to be represented as a colored string. This parameter refers to an instance of the `DocItemType` class, encapsulating details about different types of documentation items within the repository structure.

## Returns

- `str`: A colored string representation of the `DocItemType` object's name. The color of the string depends on the object's type:
  - Green for `_dir`,
  - Yellow for `_file`,
  - Red for `_class`,
  - Blue for `_function`, `_sub_function`, or `_class_function`.

## Raises

- `None`: This function does not raise exceptions under normal operation. Any potential errors are managed internally, ensuring the function's reliability in the documentation generation workflow.

## Note

This function is a component of the Repository Documentation Generator's multi-task dispatch system, contributing to efficient resource allocation and task management during the automated documentation process. It does not directly interact with other components like `ChangeDetector`, `ChatEngine`, or `MetaInfo`, but works in harmony with them to produce comprehensive, up-to-date repository documentation."""
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
    '''"""Gets the edge type between two document item types within the repository structure.

This function determines the relationship (edge type) between two DocItemType instances, representing different types of documentation items within a software project. It is used to establish a connection or association between these items, facilitating the automated generation of comprehensive documentation.

Args:
    from_item_type (DocItemType): The starting item type in the relationship. Represents one type of documentation item within the repository.
    to_item_type (DocItemType): The ending item type in the relationship. Represents another type of documentation item within the repository.

Returns:
    str: The edge type representing the relationship between `from_item_type` and `to_item_type`. This could be a string like 'contains', 'isPartOf', etc., depending on the specific items and their association.

Raises:
    ValueError: If either `from_item_type` or `to_item_type` is not a valid DocItemType instance.

Note:
    This method currently serves as a placeholder for future implementation of edge type determination logic. It is intended to be used in conjunction with the Repository Documentation Generator's multi-task dispatch system and ChangeDetector, ensuring accurate and up-to-date documentation generation.

    See also: The definition and usage of DocItemType in repo_agent\\doc_meta_info.py.
"""'''
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
        """'''
Determines the depth of a node within a hierarchical tree structure using recursive traversal.

This function, `check_depth`, is part of the Repository Documentation Generator, an automated tool designed to streamline the documentation process for software projects. It operates by recursively exploring each child node in the tree, calculating their respective depths, and assigning the current node's depth as one more than the maximum depth found among its children.

Args:
    node (object): The node whose depth is to be determined. This object should have a 'children' attribute containing its direct child nodes, with each child node also having a similar 'children' attribute for their descendants.

Returns:
    int: The depth of the node in the tree.

Raises:
    ValueError: If the provided node does not have a 'children' attribute or if this attribute does not contain iterable objects.

Note:
    This method is typically invoked after constructing the hierarchical tree structure to ascertain each node's position relative to others. It assumes that the 'children' attribute of a node contains its direct child nodes, and each child node has a similar 'children' attribute for their own descendants.

See also:
    For more information on the Repository Documentation Generator, refer to the project documentation.
'''"""
        if now_b in now_a.tree_path:
            return now_b
        if now_a in now_b.tree_path:
            return now_a
        return None

    def get_travel_list(self):
        '''"""Recursively constructs the hierarchical path of repository nodes.

This function is part of the Repository Documentation Generator, an automated tool designed to streamline the documentation process for software projects. It traverses through each child node of a given repository structure, appending them to the current path until all nodes are included in the hierarchical representation.

Args:
    now_path (list): The current path in the tree. This list accumulates nodes as the function recursively descends into the repository structure.

Returns:
    None. This method modifies the `tree_path` attribute of the current object by appending it to `now_path`. No explicit return value is provided, as the changes are reflected in the object's state.

Raises:
    None. This function does not throw any exceptions under normal operation.

Note:
    The `tree_path` attribute of the current object is updated in-place by appending it to `now_path`. This process builds a comprehensive, hierarchical view of the repository structure, facilitating accurate and automated documentation generation.
"""'''
        now_list = [self]
        for _, child in self.children.items():
            now_list = now_list + child.get_travel_list()
        return now_list

    def check_depth(self):
        """plaintext
Gets the Python file name of the DocItem object within the repository documentation generation process.

This function retrieves the full hierarchical name of the DocItem object, then splits it to extract the base name (without extension). It appends ".py" back to form the file name, aligning with Python source code conventions. This method is integral to the Repository Documentation Generator's workflow, ensuring accurate and up-to-date documentation for software projects.

Args:
    doc_item (DocItem): The DocItem object from which to derive the file name.

Returns:
    str: The file name with '.py' extension, representing a Python source code file.

Raises:
    AttributeError: If the 'get_full_name' method is missing in the DocItem class.

Note:
    This function relies on the 'get_full_name' method of the DocItem class, which returns the full hierarchical name of the object, separated by slashes ('/'). The generated file name adheres to Python source code naming conventions, facilitating seamless integration within software projects.
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
        """
Gets the full name of a DocItem.

This function retrieves the comprehensive name of a documentation item by combining its type and identifier. It is part of the Repository Documentation Generator, a tool designed to automate and streamline the documentation process for software projects. By leveraging advanced techniques such as change detection and interactive communication, this generator ensures that documentation remains accurate and up-to-date with minimal manual intervention.

Args:
    doc_item (DocItem): The documentation item whose full name is to be retrieved. This object contains attributes like 'type' and 'identifier'.

Returns:
    str: The full name of the DocItem, constructed by concatenating its type and identifier.

Raises:
    AttributeError: If the 'type' or 'identifier' attribute is missing from the DocItem object.

Note:
    This function is used internally within the Repository Documentation Generator to construct comprehensive names for documentation items, facilitating easier identification and management.
"""
        self.tree_path = now_path + [self]
        for key, child in self.children.items():
            child.parse_tree_path(self.tree_path)

    def get_file_name(self):
        '''"""
Finds the corresponding file from the repository root node based on the path list.

This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It leverages advanced techniques such as hierarchical traversal and path matching to locate specific files within the repository structure.

Args:
    recursive_file_path (list): The list of file paths to search for. Each path is a segment of the full file path from the repository root, represented as strings.

Returns:
    Optional[DocItem]: The corresponding file if found, otherwise None.

Raises:
    AssertionError: If the current DocItem's type is not DocItemType._repo.

Note:
    This function traverses the hierarchical structure of a repository starting from the root node (`_repo`). It checks each path in `recursive_file_path` list against the current node's children. If a path does not exist, it immediately returns None. The function assumes that the current instance (`self`) is a repository root node (`DocItemType._repo`).

    See also: `DocItemType` for possible item types.
"""'''
        full_name = self.get_full_name()
        return full_name.split('.py')[0] + '.py'

    def get_full_name(self, strict=False):
        """plaintext
Checks if a documentation item has tasks to be executed within the Repository Documentation Generator system.

This function, part of the comprehensive Repository Documentation Generator tool, determines whether a given `DocItem` requires any tasks to be performed, such as generating or updating its documentation. It recursively checks each child item within the hierarchy of the provided `DocItem`. The function also considers an optional ignore list of file paths that, if matched by the item's full name, will cause it to skip task execution.

Args:
    now_item (DocItem): The current documentation item to check for tasks. Represents a part of the codebase that may need documentation tasks. Its `item_status` attribute indicates whether the associated documentation is up-to-date or needs to be generated/updated.
    ignore_list (List[str], optional): A list of file paths to be excluded from task execution. Defaults to [], meaning no items are excluded by default.

Returns:
    None: This function modifies the `has_task` attribute of the provided `DocItem`, indicating whether tasks need to be executed for this item or its descendants.

Raises:
    None: No exceptions are raised by this function.

Note:
    This function is part of a larger system designed to automate and streamline the documentation process for software projects. It checks if a given document item should have tasks executed based on its status and whether it matches certain criteria (like being in an ignore list). The function traverses up the hierarchy of the document item, checking each level to determine if the item or any parent items match conditions that would exempt them from task execution.

    The `DocItem` class represents an item within the codebase that may need documentation tasks, such as files, directories, or other entities. Its `item_status` attribute indicates whether the associated documentation is up-to-date or needs to be generated/updated. The `ignore_list`, a list of strings, contains paths that, if matched by the item's full name, will cause the function to skip task execution for that item.

    See also:
        `DocItem`, `DocItemType`, `DocItemStatus` for more details on the structure and states of the documents being processed.

        The `need_to_generate` function is used within this method to determine if a given `DocItem` needs to be generated or updated based on its status and potential inclusion in an ignore list.
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
        '''"""
Recursively prints the repository object structure.

This function visualizes the hierarchical layout of directories and files within a software repository, providing a detailed overview of its organization. It can optionally print additional content and display in a diff status format for comparison purposes. The `indent` parameter controls the level of indentation for each nested item, while the `ignore_list` allows certain items to be skipped during printing.

Args:
    indent (int, optional): The indentation level for printing. Defaults to 0.
    print_content (bool, optional): Whether to print additional content. Defaults to False.
    diff_status (bool, optional): Whether to print in a diff status format. Defaults to False.
    ignore_list (List[str], optional): A list of items to ignore during printing. Defaults to [].

Returns:
    None

Raises:
    None

Note:
    This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It leverages advanced techniques such as change detection and interactive communication with the repository to streamline the generation of documentation pages, summaries, and metadata.

    By recursively traversing the repository structure, this function offers a clear visualization of directories and files, enhancing understanding and maintenance of complex project structures. The `indent` parameter allows customization of the printing layout, while the `ignore_list` feature enables selective omission of certain items during the print process.

See also:
    `DocItemType`, `need_to_generate` for more details on the structure and states of the documents being processed.
"""'''
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
        if need_to_generate(now_item, ignore_list=ignore_list):
            now_item.has_task = True
        for _, child in now_item.children.items():
            DocItem.check_has_task(child, ignore_list)
            now_item.has_task = child.has_task or now_item.has_task

    def print_recursive(self, indent=0, print_content=False, diff_status=False, ignore_list: List[str]=[]):
        """[Short description]

Find all references of a variable within the repository, utilizing the Repository Documentation Generator's capabilities.

[Longer description if needed.]

This function is part of the Repository Documentation Generator, an automated tool designed to streamline the documentation process for software projects. It employs advanced techniques such as change detection and interactive communication with the repository to ensure accurate and up-to-date documentation.

Args:  
    repo_path (str): The path to the repository root directory. This is where the search for variable references will commence.
    variable_name (str): The name of the variable whose references are to be found. This is the target of the search within the codebase.
    file_path (str): The path to the file where the variable is located. This parameter narrows down the search scope if 'in_file_only' is set to True.
    line_number (int): The line number in the file where the variable is defined. This aids in pinpointing the exact location of the variable within its source code.
    column_number (int): The column number in the file where the variable is defined. This further refines the search for the variable's definition.
    in_file_only (bool, optional): If True, restricts the search to the specified file only. Defaults to False, implying a broader search across the entire repository.

Returns:  
    list: A list of tuples. Each tuple contains the relative path to the referencing file and the line/column numbers of each reference found. This structured output facilitates easy integration with other documentation processes.

Raises:  
    ValueError: If any error occurs during the process, including issues with Jedi library or invalid input parameters. This ensures robustness by signaling potential problems for handling or debugging.

Note:  
    This function utilizes the Jedi library for code analysis, enabling efficient and accurate traversal of the codebase. See also: https://jedi-vim.github.io/docs/"""

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
    """
DocItemStatus
-------------

A class representing the status of a documentation item within the Repository Documentation Generator.

This class encapsulates various attributes and methods to manage and track the generation requirements, current state, and other relevant details of individual documentation items. It plays a crucial role in coordinating with other components of the system, such as ChangeDetector and MetaInfo, to ensure accurate and timely updates to the project's documentation.

Args:
    item_id (str): The unique identifier for the documentation item.
    status (str): The current status of the documentation item ('pending', 'generated', 'outdated'). Defaults to 'pending'.
    need_to_generate (bool): A flag indicating whether the documentation item needs to be generated or updated. Defaults to True.

Attributes:
    item_id (str): The unique identifier for the documentation item.
    status (str): The current status of the documentation item ('pending', 'generated', 'outdated').
    need_to_generate (bool): A flag indicating whether the documentation item needs to be generated or updated.

Raises:
    ValueError: If the provided status is not one of the valid options ('pending', 'generated', 'outdated').

Note:
    See also: `ChangeDetector`, `MetaInfo` for more details on how this class interacts with other components of the Repository Documentation Generator.
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
    """plaintext
Determines if a documentation item requires generation based on its status and potential inclusion in an ignore list.

This function, part of the Repository Documentation Generator, assesses whether a given `DocItem` necessitates documentation generation. It evaluates both the item's status and whether it belongs to a blacklist, defined by the `ignore_list` parameter.

Args:
    doc_item (DocItem): The documentation item to evaluate for generation necessity.
    ignore_list (List[str], optional): A list of file paths to exclude from documentation generation. Defaults to [].

Returns:
    bool: True if the item requires generation, False otherwise.

Raises:
    None

Note:
    This function is integral to the Repository Documentation Generator, a comprehensive tool designed for automating software project documentation. It determines whether a given document item should be processed based on its status and potential inclusion in an ignore list. The function systematically examines each level of the `DocItem` hierarchy to ascertain if the item or any parent items meet conditions that would exempt them from documentation generation.

See also:
    `DocItem`, `DocItemType`, `DocItemStatus`: For detailed information on the structure and states of the documents being processed.
"""
    repo_path: Path = ''
    document_version: str = ''
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
        """
MetaInfo: The central metadata management class for the Repository Documentation Generator.

    This class encapsulates and manages all metadata-related functionalities, serving as a hub for interacting with various components of the documentation generation process. It facilitates the storage, retrieval, and manipulation of metadata crucial for generating accurate and up-to-date documentation pages, summaries, and other related artifacts.

    Args:
        project_settings (ProjectSettings): An instance of ProjectSettings containing all configuration details for the current project.
        settings_manager (SettingsManager): An instance of SettingsManager responsible for managing various application settings.

    Returns:
        MetaInfo: An instance of MetaInfo with initialized metadata attributes.

    Raises:
        None

    Note:
        This class is integral to the overall operation of the Repository Documentation Generator, ensuring seamless interaction between different components and maintaining consistent metadata across the documentation generation lifecycle.
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
        """# init_meta_info

Initializes metadata information for the documentation process.

This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It leverages advanced techniques such as change detection and interactive communication with the repository to streamline the generation of documentation pages, summaries, and metadata.

## Args

param1 (dict): A dictionary containing initial metadata information. This includes details about the project structure, file paths, and other relevant data necessary for the documentation process. Defaults to an empty dictionary.

param2 (str): The path to the repository root directory. This is used to navigate through the repository's file system during the documentation generation process.

## Returns

dict: A dictionary containing initialized metadata information. This includes updated details about the project structure, file paths, and other relevant data necessary for the documentation process.

## Raises

ValueError: If either `param1` or `param2` is not of the correct type.

## Note

See also: [ChangeDetector](doc_meta_info.py/ChangeDetector), [ChatEngine](doc_meta_info.py/ChatEngine), [EdgeType](doc_meta_info.py/EdgeType), [DocItemType](doc_meta_info.py/DocItemType), [MetaInfo](doc_meta_info.py/MetaInfo), [FileHandler](doc_meta_info.py/FileHandler), [InterceptHandler](doc_meta_info.py/InterceptHandler), [set_logger_level_from_config](doc_meta_info.py/set_logger_level_from_config), [cli](doc_meta_info.py/cli), [run](doc_meta_info.py/run), [diff](doc_meta_info.py/diff), [clean](doc_meta_info.py/clean), [summarize_repository](doc_meta_info.py/summarize_repository), [create_module_summary](doc_meta_info.py/create_module_summary), [chat_with_repo](doc_meta_info.py/chat_with_repo), [run_outside_cli](doc_meta_info.py/run_outside_cli), [Task](doc_meta_info.py/Task), [TaskManager](doc_meta_info.py/TaskManager), [some_function](doc_meta_info.py/some_function), [ProjectManager](doc_meta_info.py/ProjectManager), [Runner](doc_meta_info.py/Runner), [LogLevel](doc_meta_info.py/LogLevel), [ProjectSettings](doc_meta_info.py/ProjectSettings), [ChatCompletionSettings](doc_meta_info.py/ChatCompletionSettings), [Setting](doc_meta_info.py/Setting), [SettingsManager](doc_meta_info.py/SettingsManager), [GitignoreChecker](doc_meta_info.py/GitignoreChecker), [make_fake_files](doc_meta_info.py/make_fake_files), [delete_fake_files](doc_meta_info.py/delete_fake_files)."""
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
        """'''
Loads MetaInfo from an existing metainfo directory within the context of the Repository Documentation Generator project.

This function initializes a MetaInfo object by reading the project hierarchy JSON and meta-info JSON files from the specified checkpoint directory path. It utilizes settings from SettingsManager and, if provided, a repository structure dictionary. The Repository Documentation Generator is designed to automate the documentation process for software projects, leveraging advanced techniques such as chat-based interaction and multi-task dispatching.

Args:
    checkpoint_dir_path (Path): The path to the directory containing the metainfo files. This directory should adhere to the structure expected by the Repository Documentation Generator.  
    repo_structure (Optional[Dict[str, Any]]): An optional dictionary representing the repository structure. Defaults to None. If provided, it should align with the structure definitions used within the generator.

Returns:
    MetaInfo: A MetaInfo object initialized with data from the checkpoint directory. This object encapsulates metadata extracted from the project hierarchy and meta-info JSON files, facilitating further documentation generation tasks.

Raises:
    None: The function does not raise exceptions under normal operation. Any issues during file reading or structure interpretation would typically be handled internally.

Note:
    This function assumes the presence of a project hierarchy JSON file mapping file names to their content, and a meta-info JSON file containing various metadata fields, in the specified directory. It is part of the broader Repository Documentation Generator system, which includes components like ChangeDetector, ChatEngine, EdgeType & DocItemType, DocItemStatus & need_to_generate, MetaInfo & FileHandler, InterceptHandler & set_logger_level_from_config, cli & run, diff, clean, summarize_repository, create_module_summary, chat_with_repo & run_outside_cli, Task, TaskManager, worker, ProjectManager & Runner, LogLevel, ProjectSettings, ChatCompletionSettings, Setting, SettingsManager, GitignoreChecker & make_fake_files, delete_fake_files.

    See also: repo_agent.doc_meta_info.MetaInfo.from_project_hierarchy_json for details on how the project hierarchy JSON is converted into a MetaInfo object.
'''"""
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
        """
[Short one-line description]

The 'checkpoint' function is designed to manage the state of documentation items within the Repository Documentation Generator project, ensuring that changes are tracked and necessary updates are scheduled.

[Longer description if needed]

This function operates as part of the ChangeDetector component, which monitors alterations in the repository to determine which documentation elements require updating or generation. It leverages the DocItemStatus and need_to_generate attributes to manage the status and generation requirements of individual documentation items.

Args:
    doc_item (DocItemType): The documentation item whose state is being managed. This could be any type of documentation item defined by EdgeType, such as a module summary or a metadata entry.
    new_status (DocItemStatus): The updated status of the documentation item. This could be 'updated', 'new', or 'deleted', among others.

Returns:
    None: This function does not return any value. Its purpose is to update the state of the provided documentation item within the system.

Raises:
    ValueError: If the provided doc_item is not a valid DocItemType, or if the new_status is not a recognized status for DocItemStatus.

Note:
    See also: The ChangeDetector component of the Repository Documentation Generator, which oversees the monitoring and updating of documentation items based on repository changes.
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
        """# Repository Documentation Generator: Task List Printing Function

Prints the task list in a formatted table as part of the meta information handling in the document generation process. This function visualizes tasks within a multi-task system, including their dependencies.

## Description

The `print_task_list` function takes a dictionary of `Task` objects and prints a table displaying each task's ID, generation reason (status), full name, and its dependencies. If a task has dependencies, they are displayed as a comma-separated string; if the string exceeds 20 characters, it is truncated with ellipsis for readability.

## Function Signature

print_task_list(task_dict: Dict[str, Task]) -> None


## Args

`task_dict` (Dict[str, Task]): A dictionary where keys are task IDs and values are `Task` objects. Each `Task` object contains attributes such as `id`, `status`, `full_name`, and `dependencies`.

## Returns

None

## Raises

None

## Note

This function is used to visualize the tasks within a multi-task system, including their dependencies. It's part of the meta information handling in a document generation process. The output is printed directly to the console and not returned as a data structure. 

## Examples

# Assuming 'tasks' is a dictionary of Task objects
tasks = {
    "t1": Task(id="t1", status="Generated", full_name="Task 1", dependencies=["d1"]),
    "t2": Task(id="t2", status="Pending", full_name="Task 2"),
    "t3": Task(id="t3", status="Failed", full_name="Task 3", dependencies=["d2", "d3"])
}

print_task_list(tasks)


This would print a table similar to:

| ID   | Status    | Full Name          | Dependencies         |
|------|-----------|--------------------|----------------------|
| t1   | Generated | Task 1             | d1                   |
| t2   | Pending   | Task 2             |                      |
| t3   | Failed    | Task 3             | d2, d3 (truncated)  |

Note: The actual output format may vary based on the specifics of the `Task` class and its string representation."""
        files = []

        def walk_tree(now_node):
            """
Loads documentation from older meta information.

This function retrieves and updates the documentation metadata from an older format, ensuring compatibility with the current system. It handles potential discrepancies and missing data gracefully, maintaining the integrity of the documentation structure.

Args:
    older_meta (dict): A dictionary containing the older meta information.
    current_schema (dict): A dictionary representing the current schema or structure of the meta information.

Returns:
    dict: The updated meta information in the current format.

Raises:
    ValueError: If the 'older_meta' is not a dictionary or if it lacks essential keys required for conversion.
    KeyError: If critical keys are missing in the 'older_meta'.

Note:
    This function is crucial for maintaining backward compatibility and smooth transition between different versions of the documentation system. It ensures that older documentation remains accessible and usable within the current framework.
"""
            if now_node.item_type in [DocItemType._file, DocItemType._dir]:
                files.append(now_node)
            if count_repo and now_node.item_type == DocItemType._repo:
                files.append(now_node)
            for _, child in now_node.children.items():
                walk_tree(child)
        walk_tree(self.target_repo_hierarchical_tree)
        return files

    def find_obj_with_lineno(self, file_node: DocItem, start_line_num) -> DocItem:
        """
[Short one-line description]
Retrieves all files from the specified directory.

[Longer description if needed]
The 'get_all_files' function is designed to traverse a given directory, collecting and returning information about all files it contains. This includes file paths, names, and other relevant metadata. It serves as a foundational component in the Repository Documentation Generator, facilitating the comprehensive documentation of software projects by systematically gathering file-level details.

Args:
    directory_path (str): The path to the directory from which files are to be retrieved. Defaults to the current working directory if not specified.

    recursive (bool): A flag indicating whether subdirectories should also be searched for files. Defaults to False, implying a shallow search limited to the top-level directory.

Returns:
    list of dict: A list where each dictionary represents a file, containing keys 'path' (str), 'name' (str), and 'is_dir' (bool). 'is_dir' is True if the item is a subdirectory, False otherwise.

Raises:
    FileNotFoundError: If the specified directory does not exist.
    NotADirectoryError: If the provided path is not a valid directory.

Note:
    This function is part of the Repository Documentation Generator, a tool that automates and simplifies the documentation process for software projects. It forms the basis for gathering file-level metadata, which is crucial for generating detailed and accurate project documentation.
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
        """双向提取所有引用关系"""
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
                '''"""
Convert the document metadata to a hierarchical JSON representation.

This function, part of the Repository Documentation Generator project, traverses through all file items, collecting their metadata and organizing it into a nested dictionary structure. The resulting JSON can be used to represent the hierarchical relationships between different types of documents (e.g., files, directories). 

The function leverages advanced techniques such as change detection, interactive communication with the repository, and multi-task dispatching to automate the documentation process for software projects. It ensures accurate and up-to-date representation of document metadata by managing various types of edges and documentation items within the repository structure.

Args:
    flash_reference_relation (bool): If True, the latest bidirectional reference relations will be included in the JSON output. Defaults to False.

Returns:
    dict: A dictionary representing the hierarchical JSON structure of the document metadata. The keys are full object names (from bottom to top), and the values are lists of dictionaries containing metadata for each file or directory item.

Raises:
    None

Note:
    This function is part of the MetaInfo class in repo_agent\\doc_meta_info.py. It utilizes helper functions such as get_all_files, walk_file, and DocItemType's to_str method to construct the hierarchical JSON representation.

    See also:
        - repo_agent\\doc_meta_info.py/DocItemType for details on DocItemType enum and its to_str method.
        - repo_agent\\doc_meta_info.py/MetaInfo/get_all_files for the implementation of get_all_files function.
"""'''
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
        '''"""
Finds the DocItem object associated with a given line number within a file.

This function is part of the Repository Documentation Generator, an automated tool designed to streamline the documentation process for software projects. It navigates through the children of a DocItem (file_node) to pinpoint the child object whose content's start and end lines encompass the provided start_line_num. If no such child is found, it returns the current DocItem.

Args:
    file_node (DocItem): The parent DocItem (file) within the repository structure to search. This node represents a file in the software project and contains metadata about its content.
    start_line_num (int): The line number to match against the child objects' code_start_line and code_end_line attributes. This could be a specific function or method's line within the file.

Returns:
    DocItem: The DocItem object that contains the specified line number, or the file_node if no matching child is found. This returned DocItem provides detailed metadata about the identified section of the code.

Raises:
    AssertionError: If file_node is None. This error is raised when an attempt is made to search a non-existent or invalid file node in the repository structure.

Note:
    This function assumes that all children of a DocItem have non-null 'content' and 'code_start_line', 'code_end_line' attributes within their content dictionary. These attributes are crucial for accurately identifying sections of code within files, enabling precise documentation generation.
"""'''
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
        '''"""Extract bidirectional reference relationships within the repository.

This function processes all bidirectional reference relationships across the repository. It iterates over each file node, identifying references to other objects within the same file. If a white list is provided, it restricts processing to relationships within specified files and object names.

The function employs a recursive strategy to traverse through all child nodes of each file, detecting references via the `find_all_referencer` method. It accommodates special cases such as references from jump-files or fake-files, updating reference relationships accordingly.

In the context of the Repository Documentation Generator project, this function plays a crucial role in maintaining and updating reference relationships among DocItem objects. By modifying these relationships in place, it ensures that `reference_who`, `who_reference_me`, and `special_reference_type` attributes of DocItem objects are accurately represented.

Args:
    white_list (list): A list of file names or object names to restrict reference processing. Defaults to None.

Returns:
    None

Raises:
    None

Note:
    This function modifies the reference relationships of DocItem objects in place. It does not return any value but updates the `reference_who`, `who_reference_me`, and `special_reference_type` attributes of DocItem objects.

    See also:
        - repo_agent.doc_meta_info.py/DocItem/get_file_name
        - repo_agent.doc_meta_info.py/DocItem/get_full_name
        - repo_agent.doc_meta_info.py/MetaInfo/get_all_files
"""'''
        self.parse_reference()
        task_manager = self.get_task_manager(self.target_repo_hierarchical_tree, task_available_func=task_available_func)
        return task_manager

    def _map(self, deal_func: Callable):
        """将所有节点进行同一个操作"""

        def travel(now_item: DocItem):
            deal_func(now_item)
            for _, child in now_item.children.items():
                travel(child)
        travel(self.target_repo_hierarchical_tree)

    def load_doc_from_older_meta(self, older_meta: MetaInfo):
        """
Gets the task manager instance for managing tasks within the documentation generation workflow.

This function retrieves an instance of TaskManager, which is responsible for orchestrating various tasks such as generating documentation pages, summaries, and metadata. It ensures efficient resource allocation and task management during the documentation process.

Args:
    None

Returns:
    TaskManager: An instance of TaskManager for managing tasks within the documentation workflow.

Raises:
    None

Note:
    This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It leverages advanced techniques such as chat-based interaction and multi-task dispatching to streamline the generation of documentation pages, summaries, and metadata.
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
            '''"""
Extract MetaInfo from project hierarchy path.

This function, part of the Repository Documentation Generator, reads the 'project_hierarchy.json' file located within the specified repository path. It then translates this JSON data into our custom MetaInfo data structure, facilitating comprehensive documentation generation for software projects.

Args:
    repo_path (str): The path to the repository where 'project_hierarchy.json' is situated. This path should lead to a directory containing the necessary JSON file, adhering to the format expected by our MetaInfo system.

Returns:
    MetaInfo: An instance of the MetaInfo class representing the project hierarchy. This object encapsulates structured data about the repository's directory structure, ready for further documentation processing.

Raises:
    FileNotFoundError: If 'project_hierarchy.json' does not exist in the specified repository path. This error signifies that the required JSON file is missing, preventing the creation of a MetaInfo instance.

Note:
    The function presumes that 'project_hierarchy.json' follows a specific format and structure, compatible with our MetaInfo data structure. Any deviation from this expected schema may result in incorrect or incomplete MetaInfo instances.
"""'''
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
        """project_hierarchy_json全是压平的文件，递归的文件目录都在最终的key里面, 把他转换到我们的数据结构"""
        project_hierarchy_json_path = os.path.join(repo_path, 'project_hierarchy.json')
        logger.info(f'parsing from {project_hierarchy_json_path}')
        if not os.path.exists(project_hierarchy_json_path):
            raise NotImplementedError('Invalid operation detected')
        with open(project_hierarchy_json_path, 'r', encoding='utf-8') as reader:
            project_hierarchy_json = json.load(reader)
        return MetaInfo.from_project_hierarchy_json(project_hierarchy_json)

    def to_hierarchy_json(self, flash_reference_relation=False):
        """
Gets the topology information of the repository.

This function retrieves detailed topological data about the repository structure, including relationships between different components such as files, directories, and documentation items. It leverages the advanced features of the Repository Documentation Generator to provide an accurate and up-to-date representation of the repository's hierarchy.

Args:
    repo_agent (object): An instance of the RepoAgent class, representing the repository being documented.
    meta_info (MetaInfo): An object containing metadata about the repository, including its structure and documentation items.

Returns:
    dict: A dictionary representing the topological structure of the repository. The keys are strings denoting different components (e.g., 'files', 'directories'), and the values are lists of dictionaries, each describing a specific component with keys 'name' and 'parent'.

Raises:
    ValueError: If the provided repo_agent or meta_info objects are not properly initialized or contain invalid data.

Note:
    This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It utilizes advanced techniques such as change detection and interactive communication to ensure accurate and up-to-date repository documentation.
"""
        hierachy_json = {}
        file_item_list = self.get_all_files()
        for file_item in file_item_list:
            file_hierarchy_content = []

            def walk_file(now_obj: DocItem):
                """
[Short one-line description]
Parses project hierarchy from JSON format and extracts metadata.

[Longer description if needed]
The 'from_project_hierarchy_json' function is a part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. This specific method focuses on parsing project hierarchy data stored in JSON format and extracting relevant metadata. It leverages advanced techniques such as multi-task dispatching to ensure efficient processing.

Args:
    json_data (dict): A dictionary containing the project's hierarchical structure in JSON format.
    project_name (str): The name of the project for which metadata is being extracted. Defaults to None.

Returns:
    dict: A dictionary containing the extracted metadata from the provided JSON data.

Raises:
    ValueError: If the input 'json_data' is not a valid dictionary or if 'project_name' is not a string.
    TypeError: If 'json_data' does not contain necessary keys for extraction.

Note:
    See also: The 'ProjectManager' class in repo_agent\\doc_meta_info.py, which manages project structures and executes tasks within the documentation generation workflow.
"""
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
        '''"""Applies a given operation to all nodes of the hierarchical tree within the repository's metadata structure.

This function, part of the Repository Documentation Generator, recursively applies a specified deal_func to each DocItem node in the target repository's hierarchical tree, including all child nodes. The operation modifies the nodes directly and does not return any value.

Args:
    deal_func (Callable): The operation to be performed on each node. This should be a callable that accepts a single argument, a DocItem instance.

Returns:
    None

Raises:
    None

Note:
    This function operates within the context of the Repository Documentation Generator project, which automates the documentation process for software projects using advanced techniques such as change detection and chat-based interaction. It does not return any value but updates the nodes directly in the hierarchical tree of metadata items.

    See also: The DocItem class documentation for more information on the structure of nodes and their children within the repository's metadata hierarchy.
"""'''
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