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
    """
    FileHandler class for managing and analyzing files within a repository.

    This class provides methods for reading, writing, and extracting information from
    files in a given repository, including code structure analysis using AST parsing.
    It also handles versioning through Git integration.
    """

    def __init__(self, repo_path, file_path):
        """
        Stores the repository and file paths, and determines the project hierarchy based on configured settings.

        Args:
            repo_path: The path to the repository.
            file_path: The path to the file.

        Returns:
            None

        """

        self.file_path = file_path
        self.repo_path = repo_path
        setting = SettingsManager.get_setting()
        self.project_hierarchy = (
            setting.project.target_repo / setting.project.hierarchy_name
        )

    def read_file(self):
        """
        No valid docstring found.

        """

        abs_file_path = os.path.join(self.repo_path, self.file_path)
        with open(abs_file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content

    def get_obj_code_info(
        self,
        code_type,
        code_name,
        start_line,
        end_line,
        params,
        file_path=None,
        docstring="",
        source_node=None,
    ):
        """
        Collects detailed information about a code element, including its type, name, location, parameters, documentation, and content. It determines if the code includes a return statement and identifies the starting column of the element's name within its source file.

        Args:
            code_type: The type of the code object (e.g., 'function', 'class').
            code_name: The name of the code object.
            start_line: The starting line number of the code object in its file.
            end_line: The ending line number of the code object in its file.
            params: A list of parameters associated with the code object.
            file_path: The path to the file containing the code object. Defaults to self.file_path if None.
            docstring: The docstring of the code object. Defaults to ''.
            source_node: The AST node representing the code object. Defaults to None.

        Returns:
            dict: A dictionary containing information about the code object, including its type, name,
                  code content, line numbers, parameters, docstring, whether it has a return statement,
                  and the column number where the name appears on the starting line.


        """

        code_info = {}
        code_info["type"] = code_type
        code_info["name"] = code_name
        code_info["md_content"] = []
        code_info["code_start_line"] = start_line
        code_info["code_end_line"] = end_line
        code_info["params"] = params
        code_info["docstring"] = docstring
        code_info["source_node"] = source_node
        with open(
            os.path.join(
                self.repo_path, file_path if file_path != None else self.file_path
            ),
            "r",
            encoding="utf-8",
        ) as code_file:
            lines = code_file.readlines()
            code_content = "".join(lines[start_line - 1 : end_line])
            name_column = lines[start_line - 1].find(code_name)
            if "return" in code_content:
                have_return = True
            else:
                have_return = False
            code_info["have_return"] = have_return
            code_info["code_content"] = code_content
            code_info["name_column"] = name_column
        return code_info

    def write_file(self, file_path, content):
        """
        Creates or overwrites a file at the specified path within the repository with the given content. Paths are relative to the repository root and any leading slashes are removed. Ensures necessary directories exist before writing.

        Args:
            file_path: The path to the file, relative to the repository root.
                       Leading slashes are removed.
            content: The string content to write to the file.

        Returns:
            None

        """

        if file_path.startswith("/"):
            file_path = file_path[1:]
        abs_file_path = os.path.join(self.repo_path, file_path)
        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
        with open(abs_file_path, "w", encoding="utf-8") as file:
            file.write(content)

    def get_modified_file_versions(self):
        """
        Obtains the content of the latest and prior revisions of a file within a Git repository. Returns `None` for the prior revision if no previous commits exist.

        Args:
            self: The instance containing repo_path and file_path attributes.

        Returns:
            tuple: A tuple containing the current version and previous version of the file as strings.
                   If the file has no prior commits, the previous version will be None.


        """

        repo = git.Repo(self.repo_path)
        current_version_path = os.path.join(self.repo_path, self.file_path)
        with open(current_version_path, "r", encoding="utf-8") as file:
            current_version = file.read()
        commits = list(repo.iter_commits(paths=self.file_path, max_count=1))
        previous_version = None
        if commits:
            commit = commits[0]
            try:
                previous_version = (
                    (commit.tree / self.file_path).data_stream.read().decode("utf-8")
                )
            except KeyError:
                previous_version = None
        return (current_version, previous_version)

    def get_end_lineno(self, node):
        """
        Determines the final line number spanned by a node and its descendants within the abstract syntax tree.

        Args:
            node: The AST node to get the end line number for.

        Returns:
            int: The end line number of the node, or -1 if it doesn't have one.

        """

        if not hasattr(node, "lineno"):
            return -1
        end_lineno = node.lineno
        for child in ast.iter_child_nodes(node):
            child_end = getattr(child, "end_lineno", None) or self.get_end_lineno(child)
            if child_end > -1:
                end_lineno = max(end_lineno, child_end)
        return end_lineno

    def add_parent_references(self, node, parent=None):
        """
        Recursively sets the `parent` attribute of each child node to the current node, enabling upward traversal of the AST.

        This method recursively iterates through the children of an AST node and
        sets their `parent` attribute to the current node. This is useful for
        traversing the AST in a bottom-up manner or accessing parent nodes from
        child nodes.

        Args:
            node: The AST node to start adding parent references from.
            parent: The parent of the current node.

        Returns:
            None

        """

        for child in ast.iter_child_nodes(node):
            child.parent = node
            self.add_parent_references(child, node)

    def get_functions_and_classes(self, code_content):
        """
        Identifies and extracts function and class definitions from source code, providing details such as name, location, parameters, and documentation.

        Args:
            code_content: The source code to analyze.

        Returns:
            list: A list of tuples, where each tuple contains information about a
                function or class: (type name, name, start line number, end line
                number, parameter names, docstring, AST node).


        """

        tree = ast.parse(code_content)
        self.add_parent_references(tree)
        functions_and_classes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = self.get_end_lineno(node)
                parameters = (
                    [arg.arg for arg in node.args.args] if "args" in dir(node) else []
                )
                all_names = [item[1] for item in functions_and_classes]
                functions_and_classes.append(
                    (
                        type(node).__name__,
                        node.name,
                        start_line,
                        end_line,
                        parameters,
                        ast.get_docstring(node),
                        node,
                    )
                )
        return functions_and_classes

    def generate_file_structure(self, file_path):
        """
        Creates a structured representation of a file's contents. Returns directory information if the path points to a directory, or details about functions and classes within the file otherwise. Each element in the returned structure provides metadata like type, name, location, and documentation.

        Args:
            file_path: The path to the file within the repository.

        Returns:
            list: A list of dictionaries, where each dictionary represents either a directory or a code object (function/class)
                  within the specified file.  If the path is a directory, returns a single dictionary representing that directory.
                  Otherwise, it returns a list of dictionaries containing information about functions and classes found in the file.


        """

        if os.path.isdir(os.path.join(self.repo_path, file_path)):
            return [
                {
                    "type": "Dir",
                    "name": file_path,
                    "content": "",
                    "md_content": [],
                    "code_start_line": -1,
                    "code_end_line": -1,
                }
            ]
        else:
            with open(
                os.path.join(self.repo_path, file_path), "r", encoding="utf-8"
            ) as f:
                content = f.read()
                structures = self.get_functions_and_classes(content)
                file_objects = []
                for struct in structures:
                    (
                        structure_type,
                        name,
                        start_line,
                        end_line,
                        params,
                        docstring,
                        source_node,
                    ) = struct
                    code_info = self.get_obj_code_info(
                        structure_type,
                        name,
                        start_line,
                        end_line,
                        params,
                        file_path,
                        docstring,
                        source_node,
                    )
                    file_objects.append(code_info)
        return file_objects

    def generate_overall_structure(self, file_path_reflections, jump_files) -> dict:
        """
        Analyzes files and folders within the repository, respecting `.gitignore` rules and specified exclusions, to construct a structured representation of the project's contents. The structure maps each file to its detailed content analysis generated by `generate_file_structure`. Files are skipped if they are present in a list of jump files or match a latest version substring. Errors during individual file processing are logged but do not halt overall structure generation.

        Args:
            file_path_reflections: A reference to file paths.
            jump_files: A list of files to ignore during structure generation.

        Returns:
            dict: A dictionary representing the repository structure, where keys are file names
                  and values are their corresponding structures generated by `generate_file_structure`.
                  Returns an empty dictionary if any error occurs during processing.


        """

        repo_structure = {}
        gitignore_checker = GitignoreChecker(
            directory=self.repo_path,
            gitignore_path=os.path.join(self.repo_path, ".gitignore"),
        )
        bar = tqdm(gitignore_checker.check_files_and_folders())
        for not_ignored_files in bar:
            normal_file_names = not_ignored_files
            if not_ignored_files in jump_files:
                print(
                    f"{Fore.LIGHTYELLOW_EX}[File-Handler] Unstaged AddFile, ignore this file: {Style.RESET_ALL}{normal_file_names}"
                )
                continue
            elif not_ignored_files.endswith(latest_verison_substring):
                print(
                    f"{Fore.LIGHTYELLOW_EX}[File-Handler] Skip Latest Version, Using Git-Status Version]: {Style.RESET_ALL}{normal_file_names}"
                )
                continue
            try:
                repo_structure[normal_file_names] = self.generate_file_structure(
                    not_ignored_files
                )
            except Exception as e:
                logger.error(
                    f"Alert: An error occurred while generating file structure for {not_ignored_files}: {e}"
                )
                continue
            bar.set_description(f"generating repo structure: {not_ignored_files}")
        return repo_structure

    def convert_to_markdown_file(self, file_path=None):
        """
        Generates a markdown representation of a file's content and structure based on the project hierarchy data.

        Args:
            file_path: The path to the file within the project hierarchy to convert.
                If None, uses the self.file_path attribute.

        Returns:
            str: A markdown formatted string representing the specified file's content and structure.


        """

        with open(self.project_hierarchy, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        if file_path is None:
            file_path = self.file_path
        file_dict = json_data.get(file_path)
        if file_dict is None:
            raise ValueError(
                f"No file object found for {self.file_path} in project_hierarchy.json"
            )
        markdown = ""
        parent_dict = {}
        objects = sorted(file_dict.values(), key=lambda obj: obj["code_start_line"])
        for obj in objects:
            if obj["parent"] is not None:
                parent_dict[obj["name"]] = obj["parent"]
        current_parent = None
        for obj in objects:
            level = 1
            parent = obj["parent"]
            while parent is not None:
                level += 1
                parent = parent_dict.get(parent)
            if level == 1 and current_parent is not None:
                markdown += "***\n"
            current_parent = obj["name"]
            params_str = ""
            if obj["type"] in ["FunctionDef", "AsyncFunctionDef"]:
                params_str = "()"
                if obj["params"]:
                    params_str = f"({', '.join(obj['params'])})"
            markdown += f"{'#' * level} {obj['type']} {obj['name']}{params_str}:\n"
            markdown += (
                f"{(obj['md_content'][-1] if len(obj['md_content']) > 0 else '')}\n"
            )
        markdown += "***\n"
        return markdown
