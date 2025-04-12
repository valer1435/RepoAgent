import os
import re
import subprocess
import git
from colorama import Fore, Style
from repo_agent.file_handler import FileHandler
from repo_agent.settings import SettingsManager

class ChangeDetector:
    """ChangeDetector is a class for detecting changes in Python files within a Git repository.

Attributes:
    repo_path (str): The path to the Git repository.
    repo (git.Repo): The Git repository object.

Methods:
    __init__(self, repo_path)
        Initializes the ChangeDetector with the specified repository path.

        Args:
            repo_path (str): The path to the Git repository.

    get_staged_pys(self)
        Retrieves staged Python files and their status (new or modified).

        Returns:
            dict: A dictionary mapping file paths to a boolean indicating if the file is new.

    get_file_diff(self, file_path, is_new_file)
        Retrieves the diff for a specific file.

        Args:
            file_path (str): The path to the file.
            is_new_file (bool): Whether the file is new.

        Returns:
            list: A list of diff lines.

    parse_diffs(self, diffs)
        Parses the diff lines to identify added and removed lines.

        Args:
            diffs (list): A list of diff lines.

        Returns:
            dict: A dictionary with 'added' and 'removed' keys, each mapping to a list of tuples (line_number, line_content).

    identify_changes_in_structure(self, changed_lines, structures)
        Identifies changes in specified structures within the diff.

        Args:
            changed_lines (dict): A dictionary with 'added' and 'removed' keys, each mapping to a list of tuples (line_number, line_content).
            structures (list): A list of tuples representing structures (structure_type, name, start_line, end_line, parent_structure).

        Returns:
            dict: A dictionary with 'added' and 'removed' keys, each mapping to a set of tuples (name, parent_structure).

    get_to_be_staged_files(self)
        Identifies files that should be staged based on certain conditions.

        Returns:
            list: A list of file paths that should be staged.

    add_unstaged_files(self)
        Adds unstaged files that meet certain conditions to the staging area.

        Returns:
            list: A list of file paths that were added to the staging area."""

    def __init__(self, repo_path):
        """Initializes the ChangeDetector instance.

Sets up the repository path and initializes a Git repository object. This method is crucial for the tool's ability to detect changes, manage file operations, and generate accurate documentation for the Git repository.

Args:
    repo_path (str): The path to the Git repository.

Raises:
    git.exc.InvalidGitRepositoryError: If the provided path is not a valid Git repository.

Note:
    This method is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository. It ensures that the repository is correctly set up for subsequent operations such as change detection and file management."""
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def get_staged_pys(self):
        """Retrieves a dictionary of staged Python files in the repository.

This method identifies Python files that have been added or modified and are currently staged for the next commit. It is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository, ensuring that documentation is up-to-date and reflects the current state of the codebase.

Args:  
    self: The instance of the ChangeDetector class.

Returns:  
    dict: A dictionary where keys are the paths of the staged Python files and values are boolean indicating whether the file is new (True) or modified (False).

Raises:  
    ValueError: If the repository is not properly initialized or the diff operation fails.

Note:  
    This method only considers files that are staged and have a .py extension. It is particularly useful for large repositories where manual tracking of changes can be time-consuming and error-prone."""
        repo = self.repo
        staged_files = {}
        diffs = repo.index.diff('HEAD', R=True)
        for diff in diffs:
            if diff.change_type in ['A', 'M'] and diff.a_path.endswith('.py'):
                is_new_file = diff.change_type == 'A'
                staged_files[diff.a_path] = is_new_file
        return staged_files

    def get_file_diff(self, file_path, is_new_file):
        """Retrieves the differences between the current state of a file and its last committed state in the repository.

This method is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository. It integrates various functionalities to detect changes, handle file operations, manage project settings, and generate summaries for modules and directories.

Args:
    file_path (str): The path to the file for which to retrieve the differences.
    is_new_file (bool): Indicates whether the file is new and needs to be staged.

Returns:
    list: A list of lines representing the differences in the file.

Raises:
    subprocess.CalledProcessError: If the git command fails to execute.

Note:
    This method stages new files before retrieving the differences."""
        repo = self.repo
        if is_new_file:
            add_command = f'git -C {repo.working_dir} add {file_path}'
            subprocess.run(add_command, shell=True, check=True)
            diffs = repo.git.diff('--staged', file_path).splitlines()
        else:
            diffs = repo.git.diff('HEAD', file_path).splitlines()
        return diffs

    def parse_diffs(self, diffs):
        """Parses the differences between two versions of a file and identifies the added and removed lines.

This method processes the output of a diff command, typically generated by version control systems like Git, to extract the line numbers and content of lines that have been added or removed. It is a crucial part of the automated documentation generation tool, which ensures that documentation remains up-to-date and reflects the current state of the codebase.

Args:
    diffs (list[str]): A list of strings representing the diff output.

Returns:
    dict: A dictionary containing two lists, 'added' and 'removed', each with tuples of line numbers and the corresponding lines.

Raises:
    ValueError: If the diff format is invalid and the line number information cannot be parsed.

Note:
    This method is used in conjunction with other functionalities to automate the detection of changes and the generation of documentation summaries for modules and directories. It helps in reducing manual effort and ensuring accuracy in the documentation process."""
        changed_lines = {'added': [], 'removed': []}
        line_number_current = 0
        line_number_change = 0
        for line in diffs:
            line_number_info = re.match('@@ \\-(\\d+),\\d+ \\+(\\d+),\\d+ @@', line)
            if line_number_info:
                line_number_current = int(line_number_info.group(1))
                line_number_change = int(line_number_info.group(2))
                continue
            if line.startswith('+') and (not line.startswith('+++')):
                changed_lines['added'].append((line_number_change, line[1:]))
                line_number_change += 1
            elif line.startswith('-') and (not line.startswith('---')):
                changed_lines['removed'].append((line_number_current, line[1:]))
                line_number_current += 1
            else:
                line_number_current += 1
                line_number_change += 1
        return changed_lines

    def identify_changes_in_structure(self, changed_lines, structures):
        """Identifies changes in the structure of a Python file.

This method takes a dictionary of changed lines and a list of structures (functions and classes) and identifies which structures have been added or removed based on the line numbers of the changes. It is used in conjunction with other methods to process file changes and update the project hierarchy, ensuring that documentation remains accurate and up-to-date.

Args:
    changed_lines (Dict[str, List[Tuple[int, str]]]): A dictionary where keys are 'added' or 'removed' and values are lists of tuples containing the line number and the line content of the changes.
    structures (List[Tuple[str, str, int, int, str]]): A list of tuples representing the structures in the file. Each tuple contains the structure type (e.g., 'function', 'class'), the name of the structure, the start line, the end line, and the parent structure (if any).

Returns:
    Dict[str, Set[Tuple[str, str]]]: A dictionary with keys 'added' and 'removed', and values are sets of tuples containing the name of the structure and its parent structure.

Raises:
    None

Note:
    This method is a crucial part of the project's change detection system, which automates the generation and management of documentation for a Git repository. It helps in maintaining an accurate and up-to-date project hierarchy by identifying structural changes in Python files."""
        changes_in_structures = {'added': set(), 'removed': set()}
        for change_type, lines in changed_lines.items():
            for line_number, _ in lines:
                for structure_type, name, start_line, end_line, parent_structure in structures:
                    if start_line <= line_number <= end_line:
                        changes_in_structures[change_type].add((name, parent_structure))
        return changes_in_structures

    def get_to_be_staged_files(self):
        """Retrieves a list of files that need to be staged based on the current repository state and project settings.

This method identifies untracked and unstaged files that meet certain conditions and adds them to a list of files to be staged. It prints intermediate results for debugging purposes.

Args:
    None

Returns:
    list[str]: A list of file paths that need to be staged.

Raises:
    None

Note:
    - The method uses the `SettingsManager` class to retrieve project settings.
    - The method prints the repository path, already staged files, untracked files, and newly staged files for debugging.
    - This method is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository, ensuring that documentation is up-to-date and accurate."""
        to_be_staged_files = []
        staged_files = [item.a_path for item in self.repo.index.diff('HEAD')]
        print(f'{Fore.LIGHTYELLOW_EX}target_repo_path{Style.RESET_ALL}: {self.repo_path}')
        print(f'{Fore.LIGHTMAGENTA_EX}already_staged_files{Style.RESET_ALL}:{staged_files}')
        setting = SettingsManager.get_setting()
        project_hierarchy = setting.project.hierarchy_name
        diffs = self.repo.index.diff(None)
        untracked_files = self.repo.untracked_files
        print(f'{Fore.LIGHTCYAN_EX}untracked_files{Style.RESET_ALL}: {untracked_files}')
        for untracked_file in untracked_files:
            if untracked_file.startswith(setting.project.markdown_docs_name):
                to_be_staged_files.append(untracked_file)
            continue
            print(f'rel_untracked_file:{rel_untracked_file}')
            if rel_untracked_file.endswith('.md'):
                rel_untracked_file = os.path.relpath(rel_untracked_file, setting.project.markdown_docs_name)
                corresponding_py_file = os.path.splitext(rel_untracked_file)[0] + '.py'
                print(f'corresponding_py_file in untracked_files:{corresponding_py_file}')
                if corresponding_py_file in staged_files:
                    to_be_staged_files.append(os.path.join(self.repo_path.lstrip('/'), setting.project.markdown_docs_name, rel_untracked_file))
            elif rel_untracked_file == project_hierarchy:
                to_be_staged_files.append(rel_untracked_file)
        unstaged_files = [diff.b_path for diff in diffs]
        print(f'{Fore.LIGHTCYAN_EX}unstaged_files{Style.RESET_ALL}: {unstaged_files}')
        for unstaged_file in unstaged_files:
            if unstaged_file.startswith(setting.project.markdown_docs_name) or unstaged_file.startswith(setting.project.hierarchy_name):
                to_be_staged_files.append(unstaged_file)
            elif unstaged_file == project_hierarchy:
                to_be_staged_files.append(unstaged_file)
            continue
            abs_unstaged_file = os.path.join(self.repo_path, unstaged_file)
            rel_unstaged_file = os.path.relpath(abs_unstaged_file, self.repo_path)
            print(f'rel_unstaged_file:{rel_unstaged_file}')
            if unstaged_file.endswith('.md'):
                rel_unstaged_file = os.path.relpath(rel_unstaged_file, setting.project.markdown_docs_name)
                corresponding_py_file = os.path.splitext(rel_unstaged_file)[0] + '.py'
                print(f'corresponding_py_file:{corresponding_py_file}')
                if corresponding_py_file in staged_files:
                    to_be_staged_files.append(os.path.join(self.repo_path.lstrip('/'), setting.project.markdown_docs_name, rel_unstaged_file))
            elif unstaged_file == project_hierarchy:
                to_be_staged_files.append(unstaged_file)
        print(f'{Fore.LIGHTRED_EX}newly_staged_files{Style.RESET_ALL}: {to_be_staged_files}')
        return to_be_staged_files

    def add_unstaged_files(self):
        """Adds unstaged files to the Git staging area.

This method retrieves a list of files that need to be staged based on the current repository state and project settings. It then adds these files to the Git staging area using the `git add` command.

Args:
    None

Returns:
    list[str]: A list of file paths that were added to the staging area.

Raises:
    None

Note:
    - The method uses the `get_to_be_staged_files` method to determine which files need to be staged.
    - The method prints intermediate results for debugging purposes.
    - This functionality is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository, ensuring that documentation is up-to-date and reflects the current state of the codebase."""
        unstaged_files_meeting_conditions = self.get_to_be_staged_files()
        for file_path in unstaged_files_meeting_conditions:
            add_command = f'git -C {self.repo.working_dir} add {file_path}'
            subprocess.run(add_command, shell=True, check=True)
        return unstaged_files_meeting_conditions