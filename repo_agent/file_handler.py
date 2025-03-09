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
    """Class FileHandler

A class for handling file operations such as reading, writing, generating file structures, and managing repository documentation.

Args:
    repo_path (str): The path to the repository.
    file_path (str): The relative path of the file within the repository.

Methods:

read_file()

Reads the content of a file.

Returns:
    str: The content of the current changed file.

get_obj_code_info(code_type, code_name, start_line, end_line, params, file_path=None, docstring="", source_node=None)

Gets the code information for a given object.

Args:
    code_type (str): The type of the code.
    code_name (str): The name of the code.
    start_line (int): The starting line number of the code.
    end_line (int): The ending line number of the code.
    params (list): Parameters for the code object.
    file_path (str, optional): The file path. Defaults to None.

Returns:
    dict: A dictionary containing the code information.

write_file(file_path, content)

Writes content to a file.

Args:
    file_path (str): The relative path of the file.
    content (str): The content to be written to the file.

get_modified_file_versions()

Gets the current and previous versions of the modified file.

Returns:
    tuple: A tuple containing the current version and the previous version of the file.

get_end_lineno(node)

Gets the end line number of a given node.

Args:
    node: The node for which to find the end line number.

Returns:
    int: The end line number of the node. Returns -1 if the node does not have a line number.

add_parent_references(node, parent=None)

Adds a parent reference to each node in the AST.

Args:
    node: The current node in the AST.
    parent (optional): The parent node. Defaults to None.

Returns:
    None

get_functions_and_classes(code_content)

Retrieves all functions, classes, their parameters (if any), and their hierarchical relationships.

Args:
    code_content (str): The code content of the whole file to be parsed.

Returns:
    list: A list of tuples containing the type of the node (FunctionDef, ClassDef, AsyncFunctionDef),
          the name of the node, the starting line number, the ending line number, the name of the parent node,
          and a list of parameters (if any).

generate_file_structure(file_path)

Generates the file structure for the given file path.

Args:
    file_path (str): The relative path of the file.

Returns:
    dict: A dictionary containing the file path and the generated file structure.

generate_overall_structure(file_path_reflections, jump_files)

Gets the overall repository structure by parsing files using AST-walk.

Args:
    file_path_reflections (dict): File path reflections.
    jump_files (list): Files to be skipped during processing.

Returns:
    dict: A dictionary containing the generated repository structure.

convert_to_markdown_file(file_path=None)

Converts the content of a file to markdown format.

Args:
    file_path (str, optional): The relative path of the file to be converted. Defaults to None.

Returns:
    str: The content of the file in markdown format.
"""

    def __init__(self, repo_path, file_path):
        """Initialize the FileHandler instance.

This function initializes an instance of the FileHandler class, setting up necessary configurations for handling files within a specified repository.

Args:  
    repo_path (str): The root path of the repository.  
    file_path (str): The relative path of the file within the repository.

Returns:  
    None  

Raises:  
    ValueError: If [condition].  

Note:  
    See also: SettingsManager.get_setting() for configuration details.
"""
        self.file_path = file_path
        self.repo_path = repo_path
        setting = SettingsManager.get_setting()
        self.project_hierarchy = setting.project.target_repo / setting.project.hierarchy_name

    def read_file(self):
        """Read the file content.

This function reads the content of a specified file within the repository. It relies on the `repo_path` and `file_path` attributes being correctly set before calling it.

Returns:
    str: The content of the current changed file

Raises:
    FileNotFoundError: If the specified file does not exist.
    PermissionError: If there are permission issues to read the file.

Note:
    This method is part of the Repository Agent framework, which automates documentation generation and maintenance for Python projects. Ensure that the necessary attributes (`repo_path` and `file_path`) are properly configured before invoking this function.
"""
        abs_file_path = os.path.join(self.repo_path, self.file_path)
        with open(abs_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content

    def get_obj_code_info(self, code_type, code_name, start_line, end_line, params, file_path=None, docstring='', source_node=None):
        """Retrieve the code information for a specified object within a Python project.

This function extracts detailed information about a given code object, including its type, name, markdown content, line numbers, parameters, docstring, source node, return statement status, and column position of the object's name. This is particularly useful in generating comprehensive documentation for Python projects using the Repository Agent framework.

Args:
    code_type (str): The type of the code.
    code_name (str): The name of the code.
    start_line (int): The starting line number of the code.
    end_line (int): The ending line number of the code.
    params (list): Parameters associated with the code.
    file_path (str, optional): The file path. Defaults to None.
    docstring (str, optional): The docstring for the code. Defaults to "".
    source_node (Any, optional): The source node for the code. Defaults to None.

Returns:
    dict: A dictionary containing the code information including type, name, markdown content, start and end lines, parameters, docstring, source node, whether it has a return statement, code content, and column position of the object's name.
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
        """Write content to a file.

This function writes the specified content to a given file path. It ensures that the file path is relative, adjusting absolute paths by removing the leading '/'.

Args:
    file_path (str): The relative path of the file.
    content (str): The content to be written to the file.

Returns:
    None

Raises:
    ValueError: If file_path is an absolute path starting with '/'.

Note:
    Ensure that file_path is a relative path. Absolute paths are adjusted by removing the leading '/'.
"""
        if file_path.startswith('/'):
            file_path = file_path[1:]
        abs_file_path = os.path.join(self.repo_path, file_path)
        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
        with open(abs_file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def get_modified_file_versions(self):
        """Get the current and previous versions of the modified file.

This function retrieves the latest version of the specified file along with its previous version from the repository, facilitating change detection and documentation updates.

Returns:
    tuple: A tuple containing the current version and the previous version of the file as strings.

Raises:
    FileNotFoundError: If the file path is incorrect or the file does not exist in the repository.
    KeyError: If the file was newly added and is not present in previous commits.
"""
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
        """Get the end line number of a given node.

This function is part of the Repository Agent framework, which automates documentation generation for Python projects by analyzing code elements such as functions and classes.

Args:
    node: The node for which to find the end line number.

Returns:
    int: The end line number of the node. Returns -1 if the node does not have a line number.
"""
        if not hasattr(node, 'lineno'):
            return -1
        end_lineno = node.lineno
        for child in ast.iter_child_nodes(node):
            child_end = getattr(child, 'end_lineno', None) or self.get_end_lineno(child)
            if child_end > -1:
                end_lineno = max(end_lineno, child_end)
        return end_lineno

    def add_parent_references(self, node, parent=None):
        """Adds a parent reference to each node in the AST.

This function iterates through the Abstract Syntax Tree (AST) and adds a 'parent' attribute to each node, linking it to its corresponding parent node.

Args:
    node (ast.AST): The current node in the AST.
    parent (ast.AST, optional): The parent node of the current node. Defaults to None.

Returns:
    None

Note:
    This function modifies the nodes by adding a 'parent' attribute.
"""
        for child in ast.iter_child_nodes(node):
            child.parent = node
            self.add_parent_references(child, node)

    def get_functions_and_classes(self, code_content):
        """Retrieves all functions, classes, their parameters (if any), and their hierarchical relationships.

Automates the process of documenting Python projects by analyzing the code to identify functions and classes along with their attributes and relationships.

Args:
    code_content (str): The code content of the whole file to be parsed. Represents the source code from which functions and classes are extracted.

Returns:
    list: A list of tuples containing the type of the node (FunctionDef, ClassDef, AsyncFunctionDef), the name of the node, the starting line number, the ending line number, a list of parameters (if any), and the docstring of the node.
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
        """Generates the file structure for the specified file path.

This function analyzes the given Python file and generates a detailed structure of its components, such as functions and classes, along with their attributes like start and end lines, types, and parent relationships.

Args:
    file_path (str): The relative or absolute path to the target file.

Returns:
    dict: A dictionary containing the file structure details. Each key is the name of a function or class, and each value is another dictionary that includes information such as type, start line, end line, and parent.

Example output:
{
    "function_name": {
        "type": "function",
        "start_line": 10,
        "end_line": 20,
        "parent": "class_name"
    },
    "class_name": {
        "type": "class",
        "start_line": 5,
        "end_line": 25,
        "parent": None
    }
}
"""
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
        """Generate the overall file structure of the repository by parsing AST-walk for all objects.

This function creates an organized representation of files within a Python project, ensuring that documentation generation is accurate and comprehensive.

Args:
    file_path_reflections (dict): A mapping of fake file paths to real file paths.
    jump_files (list): List of files to be skipped during the processing.

Returns:
    dict: A dictionary containing the generated file structure.

Raises:
    ValueError: If an invalid setting is provided by SettingsManager.

Note:
    See also: GitignoreChecker.check_files_and_folders
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
        """Converts the content of a file to markdown format.

The Repository Agent framework uses this function to convert file contents into markdown format, enhancing documentation generation for Python projects.

Args:
    file_path (str, optional): The relative path of the file to be converted. If not provided, the default file path will be used.

Returns:
    str: The content of the file in markdown format.

Raises:
    ValueError: If no file object is found for the specified file path in project_hierarchy.json.
"""
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