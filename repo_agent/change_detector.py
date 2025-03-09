import os
import re
import subprocess
import git
from colorama import Fore, Style
from repo_agent.file_handler import FileHandler
from repo_agent.settings import SettingsManager

class ChangeDetector:
    """Class ChangeDetector

The ChangeDetector class is designed to handle file differences and change detection within a Git repository as part of the Repository Agent framework. It focuses on identifying changes in Python files that have been staged using `git add` and integrates with other components to automate documentation generation.

Args:
    repo_path (str): The path to the repository.

Note:  
    See also: Repository Agent Documentation Generator.


def __init__(self, repo_path):
Initializes a ChangeDetector object for monitoring changes in the specified repository.

Args:
    repo_path (str): The path to the repository.

Returns:
    None

Raises:
    ValueError: If the repository path is invalid or does not exist.
    
Note:
    See also: git.Repo documentation for more information on initializing a Git repository object.


def get_staged_pys(self):
Identifies Python files in Git that have been staged using `git add`.

Returns:
    dict: A dictionary where keys are file paths of changed Python files and values are booleans indicating whether each file is newly created or not.

Raises:
    None


def get_file_diff(self, file_path, is_new_file):
Retrieves the differences made to a specific file using Git commands.

Args:
    file_path (str): The relative path of the file.
    is_new_file (bool): Indicates whether the file is a new file.

Returns:
    list: List of changes made to the file, represented as lines from git diff output.

Raises:
    subprocess.CalledProcessError: If the Git command execution fails.


def parse_diffs(self, diffs):
Processes differences detected in files within a repository and identifies added or removed lines.

Args:
    diffs (list): A list containing difference content. Obtained by the get_file_diff() function inside the class.

Returns:
    dict: A dictionary containing added and deleted line information with keys 'added' and 'removed'. Each key maps to a list of tuples where each tuple contains the line number and the corresponding code line.


def identify_changes_in_structure(self, changed_lines, structures):
Identifies the structures (functions or classes) where changes have occurred based on the changed lines.

Args:
    changed_lines (dict): A dictionary containing the line numbers where changes have occurred. The format is {'added': [(line number, change content)], 'removed': [(line number, change content)]}.
    structures (list): A list of function or class structures from get_functions_and_classes. Each structure contains the type, name, start line number, end line number, and parent structure name.

Returns:
    dict: A dictionary containing the names of structures where changes have occurred. The key is the change type ('added' for new structures, 'removed' for removed structures), and the value is a set of tuples (structure name, parent structure name).

Examples:
changed_lines = {'added': [(10, 'new line'), (20, 'another new line')], 'removed': []}
structures = [('function', 'func_name', 5, 15, None), ('class', 'ClassName', 16, 30, '__main__')]
result = identify_changes_in_structure(changed_lines, structures)
print(result)  # Output: {'added': {('func_name', None)}, 'removed': set()}

Note:
    See also: process_file_changes (for context on how this function is used).


def get_to_be_staged_files(self):
Identifies unstaged files that meet specific conditions and returns their paths.

Returns:
    List[str]: A list of relative file paths within the repository that are either modified but not staged, or untracked, and meet one of the specified conditions.


def add_unstaged_files(self):
Adds unstaged files which meet specific conditions to the Git staging area.

Returns:
    List[str]: A list of relative file paths within the repository that were added to the staging area.

Raises:
    subprocess.CalledProcessError: If a git add command fails.
"""

    def __init__(self, repo_path):
        """Initializes a ChangeDetector object.

The ChangeDetector class monitors the specified repository for modifications and updates documentation accordingly as part of the Repository Agent framework, which automates the generation and management of Python project documentation using large language models (LLMs).

Args:
    repo_path (str): The path to the repository.

Returns:
    None

Raises:
    ValueError: If the repository path is invalid or does not exist.
    
Note:
    See also: git.Repo documentation for more information on initializing a Git repository object.
"""
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def get_staged_pys(self):
        """Get added Python files in the repository that have been staged.

This function identifies Python files in Git that have been staged using `git add`. It is part of the Repository Agent framework, which automates documentation generation and management for Python projects by analyzing code changes and updating documentation accordingly.

Args:
    None

Returns:
    dict: A dictionary where keys are file paths of changed Python files and values are booleans indicating whether each file is newly created or not.

Raises:
    None

Note:
    The logic of the GitPython library differs from git. Here, the R=True parameter is used to reverse the version comparison logic.
"""
        repo = self.repo
        staged_files = {}
        diffs = repo.index.diff('HEAD', R=True)
        for diff in diffs:
            if diff.change_type in ['A', 'M'] and diff.a_path.endswith('.py'):
                is_new_file = diff.change_type == 'A'
                staged_files[diff.a_path] = is_new_file
        return staged_files

    def get_file_diff(self, file_path, is_new_file):
        """Retrieve the differences made to a specific file using Git commands.

This function is part of the Repository Agent framework, which automates documentation generation and maintenance for Python projects by analyzing code changes and updating documentation accordingly.

Args:
    file_path (str): The relative path of the file.
    is_new_file (bool): Indicates whether the file is a new file.

Returns:
    list: List of changes made to the file, represented as lines from git diff output.

Raises:
    subprocess.CalledProcessError: If the Git command execution fails.

Note:
    See also: ChangeDetector
"""
        repo = self.repo
        if is_new_file:
            add_command = f'git -C {repo.working_dir} add {file_path}'
            subprocess.run(add_command, shell=True, check=True)
            diffs = repo.git.diff('--staged', file_path).splitlines()
        else:
            diffs = repo.git.diff('HEAD', file_path).splitlines()
        return diffs

    def parse_diffs(self, diffs):
        """Parse the difference content from diffs and extract added and deleted line information.

This function processes the differences detected in files within a repository, identifying lines that have been added or removed. It is an essential part of the Repository Agent's change detection feature, which helps maintain up-to-date documentation by tracking modifications in Python projects.

Args:
    diffs (list): A list containing difference content. Obtained by the get_file_diff() function inside the class.

Returns:
    dict: A dictionary containing added and removed lines, with keys 'added' and 'removed'. Each key maps to a list of tuples where each tuple contains the line number and the corresponding code line.

Note:
    See also: ChangeDetector
"""
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
        """Identify the structures where changes have occurred based on the changed lines.

This function traverses all changed lines and checks if each line falls within the start and end lines of a structure (function or class). If so, it adds the name and parent structure name to the corresponding set in the result dictionary `changes_in_structures`.

Args:
    changed_lines (dict): A dictionary containing the line numbers where changes have occurred. The format is {'added': [(line number, change content)], 'removed': [(line number, change content)]}.
    structures (list): A list of function or class structures from get_functions_and_classes. Each structure contains the type, name, start line number, end line number, and parent structure name.

Returns:
    dict: A dictionary containing the names of structures where changes have occurred. The key is the change type ('added' for new structures, 'removed' for removed structures), and the value is a set of tuples (structure name, parent structure name).

Examples:
changed_lines = {'added': [(10, 'new line'), (20, 'another new line')], 'removed': []}
structures = [('function', 'func_name', 5, 15, None), ('class', 'ClassName', 16, 30, '__main__')]
result = identify_changes_in_structure(changed_lines, structures)
print(result)  # Output: {'added': {('func_name', None)}, 'removed': set()}


Note:
    See also: process_file_changes (for context on how this function is used).
"""
        changes_in_structures = {'added': set(), 'removed': set()}
        for change_type, lines in changed_lines.items():
            for line_number, _ in lines:
                for structure_type, name, start_line, end_line, parent_structure in structures:
                    if start_line <= line_number <= end_line:
                        changes_in_structures[change_type].add((name, parent_structure))
        return changes_in_structures

    def get_to_be_staged_files(self):
        """Retrieves all unstaged files in the repository that meet specific conditions.

This method identifies files that are either modified but not staged or untracked, and checks if they match one of two criteria: their path corresponds to a staged file with a different extension (e.g., .md for a staged .py file), or their path matches the 'project_hierarchy' field in the CONFIG. It returns a list of these files.

Args:
    None

Returns:
    List[str]: A list of relative file paths within the repository that are either modified but not staged, or untracked, and meet one of the specified conditions.

Raises:
    ValueError: If an invalid setting key is provided when calling SettingsManager.get_setting().

Note:
    See also: Configuration management (if applicable).
"""
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
        """Add unstaged files which meet specific conditions to the staging area.

This function identifies unstaged files that either match certain criteria or are untracked, then adds these files to the Git staging area using appropriate Git commands. This is part of the Repository Agent's workflow for automating documentation generation and management in Python projects.

Args:
    None

Returns:
    List[str]: A list of relative file paths within the repository that were added to the staging area.

Raises:
    subprocess.CalledProcessError: If a git add command fails.

Note:
    See also: ChangeDetector.get_to_be_staged_files
"""
        unstaged_files_meeting_conditions = self.get_to_be_staged_files()
        for file_path in unstaged_files_meeting_conditions:
            add_command = f'git -C {self.repo.working_dir} add {file_path}'
            subprocess.run(add_command, shell=True, check=True)
        return unstaged_files_meeting_conditions
if __name__ == '__main__':
    repo_path = '/path/to/your/repo/'
    change_detector = ChangeDetector(repo_path)
    changed_files = change_detector.get_staged_pys()
    print(f'\nchanged_files:{changed_files}\n\n')
    for file_path, is_new_file in changed_files.items():
        changed_lines = change_detector.parse_diffs(change_detector.get_file_diff(file_path, is_new_file))
        file_handler = FileHandler(repo_path=repo_path, file_path=file_path)
        changes_in_pyfile = change_detector.identify_changes_in_structure(changed_lines, file_handler.get_functions_and_classes(file_handler.read_file()))
        print(f'Changes in {file_path} Structures:{changes_in_pyfile}\n')