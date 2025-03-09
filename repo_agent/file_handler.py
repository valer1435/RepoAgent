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
    """Given the main idea of the project and the context provided, here's an updated docstring for the `FileHandler` class in `repo_agent/file_handler.py`. Since no specific methods or attributes are mentioned, I'll provide a general description based on the overall functionality described:

Manages file operations within the repository.

This class handles various file-related tasks such as creating, updating, and deleting files necessary for documentation generation. It ensures that all generated documentation adheres to project guidelines and ignores irrelevant files by leveraging utility functions like `GitignoreChecker`.



If you need further details or specific sections added based on actual methods within the class, please provide additional information about those methods."""

    def __init__(self, repo_path, file_path):
        """Initialize the FileHandler instance.

This function initializes an instance of the FileHandler class, setting up necessary configurations for handling files within a specified repository. The FileHandler is part of the Repository Agent tool, which automates documentation generation and management for Python projects.

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
        """Read the file content within the repository.

This function reads the content of a specified file within the repository. It relies on the `repo_path` and `file_path` attributes being correctly set before calling it. The Repository Agent framework uses this method to automate documentation generation and maintenance for Python projects, ensuring that all necessary files are processed accurately.

Returns:
    str: The content of the current changed file

Raises:
    FileNotFoundError: If the specified file does not exist.
    PermissionError: If there are permission issues to read the file.

Note:
    This function is part of the Repository Agent framework and should be used in conjunction with other components such as `ChatEngine` for automated documentation generation. Ensure that the necessary attributes (`repo_path` and `file_path`) are properly configured before invoking this function.
"""
        abs_file_path = os.path.join(self.repo_path, self.file_path)
        with open(abs_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content

    def get_obj_code_info(self, code_type, code_name, start_line, end_line, params, file_path=None, docstring='', source_node=None):
        """Retrieve the code information for a specified object within a Python project.

This function extracts detailed information about a given code object, which is useful in generating comprehensive documentation for Python projects using the Repository Agent framework.

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

This function writes the specified content to a given relative file path within the repository. It ensures that any absolute paths are adjusted by removing the leading '/' to maintain consistency in file operations.

Args:
    file_path (str): The relative path of the file.
    content (str): The content to be written to the file.

Returns:
    None

Raises:
    ValueError: If file_path is an absolute path starting with '/'.

Note:
    See also: `repo_agent.file_handler.FileHandler.get_functions_and_classes`, `repo_agent.file_handler.FileHandler.convert_to_markdown_file`.
"""
        if file_path.startswith('/'):
            file_path = file_path[1:]
        abs_file_path = os.path.join(self.repo_path, file_path)
        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
        with open(abs_file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def get_modified_file_versions(self):
        """Retrieve the current and previous versions of the modified file.

This function retrieves the latest version of the specified file along with its previous version from the repository, facilitating change detection and documentation updates for the Repository Agent project.

Returns:
    tuple: A tuple containing the current version and the previous version of the file as strings.

Raises:
    FileNotFoundError: If the file path is incorrect or the file does not exist in the repository.
    KeyError: If the file was newly added and is not present in previous commits.

Note:
    See also: FileHandler.get_functions_and_classes()
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
        """Adds parent references to each node in the AST.

This function iterates through the Abstract Syntax Tree (AST) and adds a 'parent' attribute to each node, linking it to its corresponding parent node. This is useful for navigating the hierarchical structure of the AST during further processing or analysis.

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

Automates the process of documenting Python projects by analyzing the source code to identify functions and classes along with their attributes and relationships.

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
        """Generates the file structure for the specified Python file.

This function analyzes the given Python file and generates a detailed structure of its components, such as functions and classes, along with their attributes like start and end lines, types, and parent relationships. This is part of the Repository Agent's utility functions to manage project documentation effectively.

Args:
    file_path (str): The relative or absolute path to the target Python file.

Returns:
    dict: A dictionary containing the file structure details. Each key is the name of a function or class, and each value is another dictionary that includes information such as type, start line, end line, and parent.

Raises:
    ValueError: If an invalid setting is provided by SettingsManager.

Note:
    See also: GitignoreChecker.check_files_and_folders
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
        """Generates the overall structure of the project documentation.

This function creates an overview of the entire project's documentation hierarchy by organizing and summarizing all relevant components and subcomponents.

Args:
    None

Returns:
    dict: A dictionary representing the overall structure of the project documentation, including summaries and references for each module and submodule.

Raises:
    ValueError: If there is a configuration issue preventing proper generation of the documentation structure.
    
Note:
    See also: ProjectManager (for managing the overall project hierarchy) and SettingsManager (for configuring documentation generation settings).
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

This function is part of the Repository Agent framework, which automates documentation generation for Python projects by converting file contents into markdown format to enhance documentation quality and consistency.

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