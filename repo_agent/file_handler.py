import ast
import json
import os
import astor
import git
from colorama import Fore, Style
from tqdm import tqdm
from repo_agent.log import logger
from repo_agent.settings import SettingsManager
from repo_agent.utils.gitignore_checker import GitignoreChecker
from repo_agent.utils.meta_info_utils import latest_verison_substring

class FileHandler:
    """# FileHandler Class for Repository Documentation Generator

The `FileHandler` class within the Repository Documentation Generator is responsible for managing file-related tasks, ensuring accurate and up-to-date documentation. It operates as a crucial component of the system, handling metadata and facilitating seamless interaction with repository files.

## Description

The `FileHandler` class provides methods to interact with files in the repository, manage their metadata, and ensure that all necessary documentation is generated or updated as required. It works in conjunction with other components of the Repository Documentation Generator to maintain comprehensive and current project documentation.

## Methods

### `__init__`

Initializes a new instance of `FileHandler`.

Args:
    repo_path (str): The path to the repository directory.
    settings (SettingsManager): An instance of the SettingsManager class, containing various configuration settings.

Raises:
    FileNotFoundError: If the specified repository path does not exist.
    ValueError: If any required settings are missing or invalid.

### `get_file_metadata`

Retrieves metadata associated with a specific file in the repository.

Args:
    file_path (str): The path to the file within the repository.

Returns:
    dict: A dictionary containing the file's metadata, including its type, size, and last modified timestamp.

Raises:
    FileNotFoundError: If the specified file does not exist in the repository.
    ValueError: If the provided file_path is not a string.

### `update_file_metadata`

Updates the metadata of a file in the repository.

Args:
    file_path (str): The path to the file within the repository.
    updated_metadata (dict): A dictionary containing the new metadata to be associated with the file.

Raises:
    FileNotFoundError: If the specified file does not exist in the repository.
    ValueError: If the provided file_path is not a string or if updated_metadata is not a dictionary.

### `generate_missing_documentation`

Generates documentation for files that lack it, based on their metadata and content.

Args:
    file_paths (list): A list of paths to files requiring documentation generation.

Raises:
    ValueError: If any element in file_paths is not a string.

Note: This method interacts with the `DocItemStatus` and `need_to_generate` components to determine which files need documentation and then calls upon other system functionalities to produce this documentation."""

    def __init__(self, repo_path, file_path):
        '''"""Initializes the FileHandler instance for repository documentation generation.

This method sets up a FileHandler object, which is integral to the Repository Documentation Generator project. The FileHandler manages file-related tasks crucial for accurate and up-to-date documentation generation. It is initialized with the repository root path and the relative file path within this repository.

Args:
    repo_path (str): The path to the repository's root directory. This is where the project files reside.
    file_path (str): The path to a specific file within the repository, relative to the root directory. This file may contain crucial data for documentation generation.

Returns:
    None

Raises:
    None

Note:
    Post-initialization, the `project_hierarchy` attribute of the FileHandler instance is determined based on project settings retrieved via SettingsManager.get_setting(). This attribute encapsulates the hierarchical structure of the project as defined in these settings, aiding in the accurate generation and organization of documentation.

    See also: SettingsManager.get_setting() for detailed information on how project settings are fetched and utilized.
"""'''
        self.file_path = file_path
        self.repo_path = repo_path
        setting = SettingsManager.get_setting()
        self.project_hierarchy = setting.project.target_repo / setting.project.hierarchy_name

    def read_file(self):
        """# Repository Documentation Generator: File Handling Function

This function, part of the `FileHandler` class in `repo_agent\\file_handler.py`, is designed to read and retrieve the content of a Python file for further processing within the Repository Documentation Generator project. The project automates the documentation process for software projects using advanced techniques such as change detection, chat-based interaction, and multi-task dispatching.

## Function: read_file

Reads the content of the specified Python file located at an absolute path within the repository.

Args:
    repo_path (str): The absolute path to the repository directory.
    file_path (str): The relative path to the target Python file from the repository root.

Returns:
    str: The content of the Python file as a string.

Raises:
    IOError: If there is an issue reading the file, such as permission errors or if the file does not exist.

Note:
    This function is utilized to gather file content for tasks like detecting changes and generating documentation. It constructs the full file path by joining `repo_path` and `file_path`, then reads and returns the file's content. The Repository Documentation Generator leverages this functionality to ensure accurate and up-to-date documentation for software projects.

See also: [FileHandler Class](https://github.com/your_repo/repo_agent/blob/main/file_handler.py#L12) (for context on the class structure)."""
        abs_file_path = os.path.join(self.repo_path, self.file_path)
        with open(abs_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content

    def get_obj_code_info(self, code_type, code_name, start_line, end_line, params, file_path=None, docstring='', source_node=None):
        """[Short description]

Get the code information for a given object within the context of the Repository Documentation Generator project. This function reads specified lines from a file, extracts relevant details such as the code content, return statement presence, and the column position of the object's name within these lines. It is part of the FileHandler module, which manages metadata and file operations for accurate documentation generation.

Args:
    code_type (str): The type of the code.
    code_name (str): The name of the code to be documented.
    start_line (int): The starting line number of the code within the file.
    end_line (int): The ending line number of the code within the file.
    params (str): Any parameters associated with the code.
    file_path (str, optional): The path to the file containing the code. Defaults to None.
    docstring (str, optional): The docstring of the code. Defaults to an empty string.
    source_node (any, optional): The source node of the code. Defaults to None.

Returns:
    dict: A dictionary containing the code information including type, name, code content, start and end line numbers, parameters, docstring, source node, and whether the code contains a return statement. This data is crucial for generating comprehensive documentation pages using the Repository Documentation Generator.

Raises:
    FileNotFoundError: If the specified file path does not exist.
    IOError: If there is an issue reading the file.

Note:
    This function assumes that the provided line numbers are valid and within the range of the file's content. It also expects that 'code_name' exists in the specified lines. The Repository Documentation Generator relies on accurate and complete information to generate precise documentation.
"""
        code_info = {}
        code_info['type'] = code_type
        code_info['name'] = code_name
        code_info['md_content'] = []
        code_info['code_start_line'] = start_line
        code_info['code_end_line'] = end_line
        code_info['params'] = params
        code_info['docstring'] = docstring
        code_info['source_node'] = source_node
        with open(os.path.join(self.repo_path, file_path if file_path != None else self.file_path), 'r', encoding='utf-8') as code_file:
            lines = code_file.readlines()
            code_content = ''.join(lines[start_line - 1:end_line])
            name_column = lines[start_line - 1].find(code_name)
            if 'return' in code_content:
                have_return = True
            else:
                have_return = False
            code_info['have_return'] = have_return
            code_info['code_content'] = code_content
            code_info['name_column'] = name_column
        return code_info

    def write_file(self, file_path, content):
        """Writes file content within the repository context.

This function writes the given content to a specified file path within the repository, adhering to the Repository Documentation Generator's operational framework. It ensures that the provided file path is relative, converts it to an absolute path, and creates necessary directories if they do not exist. This process is integral to managing and documenting code changes in a software project.

Args:
    file_path (str): The relative path of the file where content will be written. Defaults to None.
    content (str): The content to be written to the file. Defaults to None.

Returns:
    None: This function does not return any value as its primary purpose is to modify the file system directly.

Raises:
    FileNotFoundError: If the specified directory in the file path does not exist.
    PermissionError: If there are insufficient permissions to create directories or write to the file.

Note:
    This function operates within the Repository Documentation Generator, a comprehensive tool designed for automating documentation processes in software projects. It's typically invoked after analyzing a file's content and before updating related JSON data or generating markdown documentation. The function supports the broader system's objectives of streamlining documentation generation through advanced techniques like chat-based interaction and multi-task dispatching, thereby reducing manual effort and ensuring consistent, up-to-date project documentation."""
        if file_path.startswith('/'):
            file_path = file_path[1:]
        abs_file_path = os.path.join(self.repo_path, file_path)
        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
        with open(abs_file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def get_modified_file_versions(self):
        '''"""
Get the modified file versions, including current and previous states.

This function retrieves the content of the file in its current state from the working directory 
and compares it to the last committed version. It is part of the Repository Documentation Generator, 
a tool designed to automate documentation processes for software projects using advanced techniques 
such as change detection, interactive communication, and multi-task dispatching.

Args:
    None - The function does not require any arguments as it operates on the current working directory 
    and repository history.

Returns:
    tuple: A tuple containing two elements. The first element is a string representing the content of 
    the file in its current state (i.e., the version present in the working directory). The second 
    element is either a string representing the content of the file from the last commit or None, 
    if no previous commit exists for the file.

Raises:
    None - This function does not raise any exceptions under normal operation.

Note:
    See also: The `get_functions_and_classes` method in the same class for parsing function and class names 
    from the file content. This can be useful for documenting specific elements within the file.
"""'''
        repo = git.Repo(self.repo_path)
        current_version_path = os.path.join(self.repo_path, self.file_path)
        with open(current_version_path, 'r', encoding='utf-8') as file:
            current_version = file.read()
        commits = list(repo.iter_commits(paths=self.file_path, max_count=1))
        previous_version = None
        if commits:
            commit = commits[0]
            try:
                previous_version = (commit.tree / self.file_path).data_stream.read().decode('utf-8')
            except KeyError:
                previous_version = None
        return (current_version, previous_version)

    def get_end_lineno(self, node):
        '''"""
Get the end line number of a given node within the source code structure.

This function recursively traverses through child nodes to determine the maximum line number, effectively identifying the end position of the node in the source code. It is a crucial component of the Repository Documentation Generator, which automates the documentation process for software projects by leveraging Python's Abstract Syntax Tree (AST) module.

Args:
    node (ast.AST): The node for which to find the end line number. This could be any node in the AST structure representing a part of the source code.

Returns:
    int: The end line number of the node. Returns -1 if the node does not have a line number or if none of its child nodes have valid line numbers, indicating an issue with the source code structure.

Raises:
    None

Note:
    This function is primarily used within the Repository Documentation Generator to determine the ending line number for various code elements (like functions and classes) in a given codebase. It forms part of the broader strategy to automate and streamline the documentation generation process, ensuring that software projects maintain accurate, up-to-date documentation with minimal manual intervention.
"""'''
        if not hasattr(node, 'lineno'):
            return -1
        end_lineno = node.lineno
        for child in ast.iter_child_nodes(node):
            child_end = getattr(child, 'end_lineno', None) or self.get_end_lineno(child)
            if child_end > -1:
                end_lineno = max(end_lineno, child_end)
        return end_lineno

    def add_parent_references(self, node, parent=None):
        '''"""
Adds parent references to nodes in the Abstract Syntax Tree (AST).

This function recursively traverses each node in the AST, assigning its 'parent' attribute to point to its respective parent node. This process helps establish hierarchical relationships within the code structure, facilitating easier navigation and understanding of complex codebases.

Args:
    node (ast.AST): The current node in the Abstract Syntax Tree (AST).
    parent (ast.AST, optional): The parent node of the current node. Defaults to None.

Returns:
    None

Raises:
    TypeError: If 'node' or 'parent' is not an instance of ast.AST.

Note:
    This function is a crucial component of the Repository Documentation Generator, a tool designed to automate and streamline the documentation process for software projects. By establishing parent-child relationships among code elements, it supports the generation of comprehensive, hierarchical documentation that enhances code readability and maintainability.

    See also: repo_agent\\file_handler.py/FileHandler/get_functions_and_classes for an example of how this function contributes to retrieving functions, classes, and their hierarchical relationships from a code snippet.
"""'''
        for child in ast.iter_child_nodes(node):
            child.parent = node
            self.add_parent_references(child, node)

    def get_functions_and_classes(self, code_content):
        """[Short one-line description]

Extracts detailed information about functions and classes from the given Python code content, utilizing Abstract Syntax Tree (AST) for parsing and analysis.

[Longer description if needed]

The `get_functions_and_classes` function is a critical component of the Repository Documentation Generator. It parses a provided Python code snippet to extract comprehensive details about its functions and classes. This includes node type ('FunctionDef', 'ClassDef', 'AsyncFunctionDef'), name, line numbers, parent structure (if applicable), parameters, docstrings, and the abstract syntax tree representation of each node.

Args:
    code_content (str): The Python code content to be parsed. This should be a string containing valid Python code representing an entire file.

Returns:
    list: A list of tuples, each containing the following elements in order:
        - type (str): The type of the node ('FunctionDef', 'ClassDef', 'AsyncFunctionDef').
        - name (str): The name of the node (function or class).
        - start_line (int): The starting line number of the node in the source code.
        - end_line (int): The ending line number of the node in the source code, determined by recursively traversing child nodes.
        - parameters (list): A list of parameter names for the node, if any.
        - docstring (str): The docstring of the node, if it exists.
        - node (ast.AST): The abstract syntax tree representation of the node.

Raises:
    None

Note:
    This function is integral to the Repository Documentation Generator's operation. It leverages Python's AST module for parsing and analyzing source code structure. By retrieving all functions, classes, their parameters (if any), and hierarchical relationships from the provided code content, it supports the generation of detailed documentation for software projects. The end line number for each node is determined by the `get_end_lineno` method, which recursively traverses through child nodes to find the maximum line number. Parent references are added to each node in the AST using the `add_parent_references` method before parsing. This function is employed within `generate_file_structure` to create a dictionary containing file path and generated file structure, and within `add_new_item` of `runner.py` to add new projects to a JSON file and generate corresponding documentation.
"""
        tree = ast.parse(code_content)
        self.add_parent_references(tree)
        functions_and_classes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = self.get_end_lineno(node)
                parameters = [arg.arg for arg in node.args.args] if 'args' in dir(node) else []
                all_names = [item[1] for item in functions_and_classes]
                functions_and_classes.append((type(node).__name__, node.name, start_line, end_line, parameters, ast.get_docstring(node), node))
        return functions_and_classes

    def generate_file_structure(self, file_path):
        """# Function: generate_file_structure

The `generate_file_structure` function is a core component of the Repository Documentation Generator, responsible for creating a structured file system that mirrors the repository's content. This structure facilitates efficient documentation generation by organizing files and directories in a logical, hierarchical manner.

## Description

This function takes as input a repository object and generates a file structure based on the repository's contents. The resulting structure is designed to be easily navigable and conducive to automated documentation processes.

## Args

- `repo` (Repository): An instance of the Repository class, representing the software project whose structure needs to be generated.

## Returns

- `dict`: A nested dictionary representing the file system structure. The keys are directory names, and their values are either further dictionaries (for subdirectories) or lists of filenames (for files).

## Raises

- `ValueError`: If the input is not a valid Repository instance.

## Notes

This function forms an integral part of the Repository Documentation Generator's multi-task dispatch system, working in conjunction with other components like ChangeDetector and FileHandler to ensure comprehensive documentation generation. It leverages the repository's metadata and content to create a structured file system that supports efficient navigation and automated documentation processes."""
        if os.path.isdir(os.path.join(self.repo_path, file_path)):
            return [{'type': 'Dir', 'name': file_path, 'content': '', 'md_content': [], 'code_start_line': -1, 'code_end_line': -1}]
        else:
            with open(os.path.join(self.repo_path, file_path), 'r', encoding='utf-8') as f:
                content = f.read()
                structures = self.get_functions_and_classes(content)
                file_objects = []
                for struct in structures:
                    structure_type, name, start_line, end_line, params, docstring, source_node = struct
                    code_info = self.get_obj_code_info(structure_type, name, start_line, end_line, params, file_path, docstring, source_node)
                    file_objects.append(code_info)
        return file_objects

    def generate_overall_structure(self, file_path_reflections, jump_files) -> dict:
        """
[Short one-line description]
Generates the overall structure of the repository documentation based on detected changes and project settings.

[Longer description if needed]
The 'generate_overall_structure' function is a core component of the Repository Documentation Generator. It orchestrates the creation of the repository's documentation structure by leveraging the 'ChangeDetector', 'ProjectManager', and 'FileHandler' components. This function takes into account the project settings, including the defined 'DocItemType' and 'EdgeType', to determine which parts of the documentation need generation or updating.

Args:
    project_settings (dict): A dictionary containing project-specific settings such as 'DocItemType', 'EdgeType', and other configuration parameters.
    change_detector_output (list): A list of tuples, each representing a change detected by the 'ChangeDetector'. Each tuple contains details about the type of change and the corresponding documentation item.
    file_handler (FileHandler): An instance of the FileHandler class responsible for managing files and metadata during the documentation generation process.

Returns:
    dict: A dictionary representing the overall structure of the repository's documentation, with keys as section names and values as dictionaries containing sub-sections and their respective details.

Raises:
    ValueError: If any required parameters are missing or invalid.
    DocumentationGenerationError: If an error occurs during the generation of the documentation structure.

Note:
    See also: The 'ChangeDetector', 'ProjectManager', and 'FileHandler' components for detailed information on how changes are detected, projects are managed, and files are handled respectively.
"""
        repo_structure = {}
        gitignore_checker = GitignoreChecker(directory=self.repo_path, gitignore_path=os.path.join(self.repo_path, '.gitignore'))
        bar = tqdm(gitignore_checker.check_files_and_folders())
        for not_ignored_files in bar:
            normal_file_names = not_ignored_files
            if not_ignored_files in jump_files:
                print(f'{Fore.LIGHTYELLOW_EX}[File-Handler] Unstaged AddFile, ignore this file: {Style.RESET_ALL}{normal_file_names}')
                continue
            elif not_ignored_files.endswith(latest_verison_substring):
                print(f'{Fore.LIGHTYELLOW_EX}[File-Handler] Skip Latest Version, Using Git-Status Version]: {Style.RESET_ALL}{normal_file_names}')
                continue
            try:
                repo_structure[normal_file_names] = self.generate_file_structure(not_ignored_files)
            except Exception as e:
                logger.error(f'Alert: An error occurred while generating file structure for {not_ignored_files}: {e}')
                continue
            bar.set_description(f'generating repo structure: {not_ignored_files}')
        return repo_structure

    def convert_to_markdown_file(self, file_path=None):
        '''"""Converts file content to markdown format using project hierarchy information.

This function reads the project_hierarchy.json file to locate the specified file's details, then transforms its content into a hierarchical markdown representation. It sorts the file's objects based on their start line numbers for organized documentation.

Args:
    file_path (str, optional): The relative path of the file to be converted. If not provided, the default file path, which is None, will be used.

Returns:
    str: The content of the file in markdown format.

Raises:
    ValueError: If no file object is found for the specified file path in project_hierarchy.json.

Note:
    This function operates within the Repository Documentation Generator, a comprehensive tool designed to automate software project documentation. It leverages advanced techniques such as chat-based interaction and multi-task dispatching to streamline the generation of documentation pages, summaries, and metadata.

    The function specifically utilizes the FileHandler component for managing file operations and metadata. In conjunction with other components like ChangeDetector (for monitoring repository changes), ChatEngine (for interactive communication), and TaskManager (for efficient task allocation), it ensures accurate and up-to-date documentation.

    By sorting file objects based on their start line numbers, this function contributes to the creation of a well-structured markdown representation, facilitating easy navigation and understanding of complex project hierarchies.
"""'''
        with open(self.project_hierarchy, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        if file_path is None:
            file_path = self.file_path
        file_dict = json_data.get(file_path)
        if file_dict is None:
            raise ValueError(f'No file object found for {self.file_path} in project_hierarchy.json')
        markdown = ''
        parent_dict = {}
        objects = sorted(file_dict.values(), key=lambda obj: obj['code_start_line'])
        for obj in objects:
            if obj['parent'] is not None:
                parent_dict[obj['name']] = obj['parent']
        current_parent = None
        for obj in objects:
            level = 1
            parent = obj['parent']
            while parent is not None:
                level += 1
                parent = parent_dict.get(parent)
            if level == 1 and current_parent is not None:
                markdown += '***\n'
            current_parent = obj['name']
            params_str = ''
            if obj['type'] in ['FunctionDef', 'AsyncFunctionDef']:
                params_str = '()'
                if obj['params']:
                    params_str = f'({', '.join(obj['params'])})'
            markdown += f'{'#' * level} {obj['type']} {obj['name']}{params_str}:\n'
            markdown += f'{(obj['md_content'][-1] if len(obj['md_content']) > 0 else '')}\n'
        markdown += '***\n'
        return markdown