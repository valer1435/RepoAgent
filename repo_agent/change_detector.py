import os
import re
import subprocess
import git
from colorama import Fore, Style
from repo_agent.file_handler import FileHandler
from repo_agent.settings import SettingsManager

class ChangeDetector:
    """# ChangeDetector Class

The `ChangeDetector` class is a core component of the Repository Documentation Generator, responsible for monitoring changes within a repository to determine which documentation items require updating or generation.

## Description

This class operates by tracking modifications in the repository's structure and content, identifying discrepancies between existing documentation and current project state. It then communicates these changes to other components of the system, facilitating the timely update or creation of relevant documentation.

## Args

None

## Returns

- `dict`: A dictionary containing details about detected changes. The keys include:
  - `added` (list): Files or directories that have been newly added to the repository.
  - `modified` (list): Files or directories that have been altered since the last documentation generation.
  - `deleted` (list): Files or directories that have been removed from the repository.

## Raises

- `ValueError`: If an unexpected error occurs during change detection, such as issues with file system access or parsing errors.

## Notes

This class is designed to work in conjunction with other components of the Repository Documentation Generator, such as `ChatEngine`, `FileHandler`, and `TaskManager`. It plays a crucial role in maintaining accurate and up-to-date documentation by identifying necessary updates promptly. 

See also: [Repository Documentation Generator](https://github.com/your_repo/repository_documentation_generator) (for more information on the overall system)."""

    def __init__(self, repo_path):
        '''"""Initializes a ChangeDetector instance for repository documentation generation.

This method sets up a ChangeDetector object, which is a crucial component of the Repository Documentation Generator. It accepts the path to a repository as input, initializing the `repo_path` attribute and creating a git.Repo object using the provided repository path. This process is integral to monitoring changes in the repository to determine which documentation items need updating or generating.

Args:
    repo_path (str): The path to the repository. This should be a string representing the local or remote directory of the Git repository.

Returns:
    None

Raises:
    ValueError: If the provided `repo_path` is not a valid directory or does not contain a Git repository.

Note:
    This method does not return any value but initializes internal attributes for further use in other methods of the ChangeDetector class. These attributes are essential for the ChangeDetector's role in monitoring changes and determining documentation update requirements within the Repository Documentation Generator framework.

    See also: git.Repo documentation (https://gitpython.readthedocs.io/en/stable/pages/repo.html) for more details on the git.Repo object, which is utilized to interact with the Git repository.
"""'''
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def get_staged_pys(self):
        '''"""
Get staged Python files in the repository for documentation generation.

This function uses GitPython library to identify Python files within the staged changes of a Git repository. It is part of the ChangeDetector module, which monitors repository modifications to determine what documentation needs updating or generating. 

The function specifically targets Python files that have been added using `git add`, indicating new or modified content. It returns a dictionary where keys are file paths and values are booleans indicating whether the file is newly created ('True') or not ('False').

Args:
    self (object): An instance of the ChangeDetector class, which holds the Git repository (`self.repo`). This object should be initialized with a valid Git repository.

Returns:
    dict: A dictionary where keys are file paths of staged Python files and values are booleans indicating whether the file is newly created ('True') or not ('False').

Raises:
    ValueError: If the provided `self` instance does not contain a valid Git repository (`self.repo`).

Note:
    This function assumes that the Git repository has been properly initialized within the object instance (`self.repo`). It does not handle cases where the repository is not set up correctly or where the current working directory is not a part of a valid Git repository.

    See also: `GitPython` library documentation for more details on its diff method usage - https://gitpython.readthedocs.io/en/stable/
"""'''
        repo = self.repo
        staged_files = {}
        diffs = repo.index.diff('HEAD', R=True)
        for diff in diffs:
            if diff.change_type in ['A', 'M'] and diff.a_path.endswith('.py'):
                is_new_file = diff.change_type == 'A'
                staged_files[diff.a_path] = is_new_file
        return staged_files

    def get_file_diff(self, file_path, is_new_file):
        """[Short one-line description]

The function 'get_file_diff' retrieves the changes made to a specific file within the repository, utilizing the ChangeDetector component of the Repository Documentation Generator.

[Longer description if needed.]

This function is part of the Repository Documentation Generator, an automated tool designed for generating and updating documentation for software projects. It employs advanced techniques such as change detection and chat-based interaction to streamline the documentation process.

Args:
    file_path (str): The relative path of the file within the repository. This parameter is crucial for identifying the specific file whose changes need to be retrieved.  
    is_new_file (bool): A boolean flag indicating whether the file in question is a newly added file. This information helps determine the appropriate git command to execute.

Returns:
    list: A list of strings, each representing a change made to the file. The format adheres to conventions used by git diff output, providing detailed insights into modifications such as additions, deletions, and contextual changes.

Raises:
    subprocess.CalledProcessError: If there's an issue executing the git command due to problems like incorrect paths or insufficient permissions. This error is not handled within this function and may result in a raised exception.

Note:
    This function interacts directly with the Git repository, leveraging subprocess to execute git commands. Consequently, any issues related to these commands (like path errors or permission problems) are beyond its scope and could potentially lead to exceptions.

    See also: The 'git diff' documentation for a comprehensive understanding of its output format: https://git-scm.com/docs/git-diff
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
        """[Short description]

The `parse_diffs` function, part of the ChangeDetector module within the Repository Documentation Generator, processes a list of differences (diffs) to extract added and deleted lines. This function is instrumental in identifying modifications within source code files, which are then utilized for updating or generating documentation.

[Longer description]

The `parse_diffs` function operates on a list of difference content, typically obtained via the `get_file_diff()` method. Its primary role is to discern lines that have been added or removed from the source code. The function outputs a dictionary containing sets of tuples. Each tuple signifies an added or removed line, comprising its corresponding line number and content.

This function does not differentiate between newly added objects and modified ones. For distinguishing new objects, users should employ the `get_added_objs()` method. The returned dictionary format mirrors this structure: {'added': [(line_number, 'content'), ...], 'removed': []}. Here, 'added' denotes lines that have been inserted or altered, while 'removed' signifies lines that have been deleted.

Args:
    diffs (list): A list of difference content. This is usually acquired by calling the `get_file_diff()` method within the class. Each element in this list represents a change in the source code - an addition or deletion of lines.

Returns:
    dict: A dictionary with two keys, 'added' and 'removed', each mapping to a set of tuples. The tuples contain line numbers and their respective content. The format is as follows: {'added': [(line_number, 'content'), ...], 'removed': []}.

Raises:
    None: This function does not raise any exceptions under normal operation.

Note:
    To determine if an object (like a class or function) is newly added based on line modifications, utilize the `get_added_objs()` method. This function complements `parse_diffs` by providing a more granular analysis of code changes.

    The Repository Documentation Generator automates and streamlines the documentation process for software projects. It achieves this through various modules, including ChangeDetector, which employs functions like `parse_diffs` to monitor repository changes and update documentation accordingly.
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
        """[Short description]

Identify changes in the structure of functions or classes within a codebase by analyzing changed lines. This function is part of the ChangeDetector module, which monitors repository modifications to determine necessary documentation updates.

Args:
    changed_lines (dict): A dictionary containing line numbers where changes have occurred. The format is {'added': [(line number, change content)], 'removed': [(line number, change content)]}.
    structures (list): A list of function or class structures, each represented as a tuple (structure type, name, start line number, end line number, parent structure name).

Returns:
    dict: A dictionary containing the structures where changes have occurred. The key is the change type ('added' for new, 'removed' for removed), and the value is a set of structure names and parent structure names.

Raises:
    None

Note:
    This function operates within the Repository Documentation Generator project, which automates the documentation process for software projects using advanced techniques like chat-based interaction and multi-task dispatching. It specifically focuses on the 'ChangeDetector' module to identify modified structures in a codebase. The results are used to update project hierarchy JSON data and generate Markdown documentation.

"""
        changes_in_structures = {'added': set(), 'removed': set()}
        for change_type, lines in changed_lines.items():
            for line_number, _ in lines:
                for structure_type, name, start_line, end_line, parent_structure in structures:
                    if start_line <= line_number <= end_line:
                        changes_in_structures[change_type].add((name, parent_structure))
        return changes_in_structures

    def get_to_be_staged_files(self):
        """'''
Determines files in the repository to be staged based on specific conditions.

This function scans the repository for unstaged changes (diffs) and untracked files, then identifies those that meet certain criteria. The criteria are:
1. The file, when its extension is altered to .md, corresponds to a file already staged.
2. The file's path aligns with the 'project_hierarchy' field in the CONFIG.

Files meeting these conditions are added to a list for staging.

Args:
    self (ChangeDetector): An instance of the ChangeDetector class, which is part of the Repository Documentation Generator. This class monitors changes in the repository to determine which documentation items need updating or generating.

Returns:
    List[str]: A list of relative file paths within the repository that are either modified but not staged, or untracked, and satisfy one of the conditions above. These files are intended for staging.

Raises:
    None

Note:
    This function utilizes the git Python library to interact with the repository. It first identifies all unstaged changes (diffs) and untracked files in the repository. Subsequently, it iterates over these files, evaluating each against the specified conditions. If a file meets one of the conditions, its path is included in the list of files designated for staging.

See also:
    RepositoryDocumentationGenerator.ChangeDetector.project_hierarchy - The field in CONFIG used to match file paths.
    RepositoryDocumentationGenerator.GitignoreChecker - Handles .gitignore file checks and temporary file management during documentation process.
'''"""
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
        """
[Short one-line description]
Adds unstaged files to the change detector's tracking list.

[Longer description if needed.]
The 'add_unstaged_files' function is part of the ChangeDetector module within the Repository Documentation Generator. This tool automates the documentation process for software projects by monitoring changes in the repository and determining which documentation items need updating or generating. 

This specific method, 'add_unstaged_files', is designed to expand the scope of the change detector by incorporating any unstaged files into its tracking list. Unstaged files are those that have been modified but not yet committed to the repository, and their inclusion ensures comprehensive detection of changes.

Args:
    file_paths (list): A list of paths to the unstaged files.  
    repo_path (str): The path to the root directory of the repository.  

Returns:
    None: This method does not return any value; it updates the internal state of the ChangeDetector object directly.  

Raises:
    ValueError: If 'file_paths' is not a list or contains non-string elements, or if 'repo_path' is not a valid directory path.  

Note:  
    See also: The 'ChangeDetector' class and its methods for managing tracked changes and generating documentation updates.  
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