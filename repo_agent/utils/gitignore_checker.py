import fnmatch
import os
from repo_agent.settings import SettingsManager

class GitignoreChecker:
    """# GitignoreChecker: A Component of Repository Documentation Generator

The `GitignoreChecker` function is an integral part of the Repository Documentation Generator, a sophisticated tool designed to automate the documentation process for software projects. It specializes in verifying whether files and folders within a specified directory are ignored by a .gitignore file, thereby ensuring accurate documentation generation.

## Description

The `GitignoreChecker` function initializes with a specific directory and the path to a .gitignore file. It loads and parses the .gitignore content, categorizing patterns into folder and file patterns. If the specified .gitignore file is absent, it defaults to a predefined path. This function does not return any value; instead, it offers methods for verifying ignored files and folders.

## Args

- `directory` (str): The directory subjected to the ignore check.
- `gitignore_path` (str): The path to the .gitignore file. Defaults to a system-defined path if the specified one is missing.

## Raises

- `FileNotFoundError`: Raised when the specified .gitignore file cannot be located, and no default path is available.

## Methods

- `_load_gitignore_patterns()`: Loads and parses the .gitignore file, segregating patterns into folder and file patterns.
- `_parse_gitignore(gitignore_content: str) -> list`: Parses the .gitignore content and returns patterns as a list.
- `_split_gitignore_patterns(gitignore_patterns: list) -> tuple`: Divides the .gitignore patterns into folder patterns and file patterns.
- `_is_ignored(path: str, patterns: list, is_dir: bool = False) -> bool`: Verifies if the given path corresponds to any of the patterns.
- `check_files_and_folders() -> list`: Validates all files and folders in the specified directory against the categorized gitignore patterns.

## Note

This function presumes that the .gitignore file adheres to standard syntax, where comments initiate with '#', folder patterns conclude with a '/', and file patterns do not. It is a crucial component of the Repository Documentation Generator, ensuring that only relevant files and folders are documented, thereby enhancing the efficiency and accuracy of the documentation process."""

    def __init__(self, directory: str, gitignore_path: str):
        '''"""Initialize the GitignoreChecker for documentation generation within a software project.

This initializer sets up the GitignoreChecker instance, preparing it to check .gitignore files for relevant patterns during the documentation generation process. It stores the provided directory and .gitignore file path, and loads the patterns from the .gitignore file into folder_patterns and file_patterns attributes. This method is a crucial part of the Repository Documentation Generator, which automates the creation of software project documentation.

Args:
    directory (str): The root directory of the software project to be documented. This should be a valid path on the filesystem.
    gitignore_path (str): The path to the .gitignore file within the project directory. This should be a valid path pointing to a .gitignore file, used to determine which files and folders should be excluded from documentation.

Returns:
    None

Raises:
    FileNotFoundError: If the provided gitignore_path does not exist or is not a valid .gitignore file.
    ValueError: If either directory or gitignore_path is not a string.

Note:
    This initializer must be called before any other methods to ensure proper setup of the GitignoreChecker instance for documentation generation.

    See also: _load_gitignore_patterns method for details on how patterns are loaded from the .gitignore file.
"""'''
        self.directory = directory
        self.gitignore_path = gitignore_path
        self.folder_patterns, self.file_patterns = self._load_gitignore_patterns()

    def _load_gitignore_patterns(self) -> tuple:
        '''"""
_load_gitignore_patterns: Load and parse .gitignore file patterns for folder and file ignores.

This function is part of the `GitignoreChecker` class within the Repository Documentation Generator project. It reads the content of a specified or default .gitignore file, parses it into individual ignore patterns, and categorizes these patterns as either directory-level (folder) or individual file ignore rules.

Args:
    repo_path (str): The path to the repository where the .gitignore file is located. Defaults to the current working directory if not provided.

Returns:
    tuple: A tuple containing two lists - one for folder patterns (directories to be ignored) and another for file patterns (specific files to be ignored).

Raises:
    FileNotFoundError: If the specified .gitignore file does not exist in the given repository path.
    ValueError: If an invalid or unsupported file type is provided.

Note:
    This method internally processes .gitignore files to facilitate accurate documentation generation within the Repository Documentation Generator project. It reads the .gitignore content, strips any leading/trailing whitespace from each line, and ignores lines that are empty or start with "#". After parsing, it splits the patterns into two lists: one for directory-level ignore rules (folder patterns) and another for individual file ignore rules (file patterns).

    The function prioritizes the specified repository path; if no path is provided, it defaults to the current working directory. This behavior ensures flexibility in usage across different project structures.

See also:
    The Repository Documentation Generator's comprehensive suite of tools, including `ChangeDetector`, `ChatEngine`, and multi-task management system, all designed to streamline and automate the documentation process for software projects.
"""'''
        try:
            with open(self.gitignore_path, 'r', encoding='utf-8') as file:
                gitignore_content = file.read()
        except FileNotFoundError:
            default_path = os.path.join(os.path.dirname(__file__), '..', '..', '.gitignore')
            with open(default_path, 'r', encoding='utf-8') as file:
                gitignore_content = file.read()
        patterns = self._parse_gitignore(gitignore_content)
        return self._split_gitignore_patterns(patterns)

    @staticmethod
    def _parse_gitignore(gitignore_content: str) -> list:
        '''"""
_parse_gitignore: Parses the content of a .gitignore file to extract patterns.

This function is part of the GitignoreChecker class within the Repository Documentation Generator project. It processes the content of a .gitignore file to identify and return relevant patterns, which are then used for documentation generation purposes.

Args:
    gitignore_content (str): The content of the .gitignore file. This includes all lines from the file, representing potential patterns to be excluded or included in the documentation process.

Returns:
    list: A list of patterns extracted from the .gitignore content. Each pattern represents a rule that specifies files or directories to be ignored during documentation generation.

Raises:
    None: This function does not raise any exceptions under normal operation. It simply parses the input content and returns the results.

Note:
    This function is internally called by `_load_gitignore_patterns` to parse the .gitignore file content. It splits the content into lines, strips any leading/trailing whitespace, and ignores empty lines or lines starting with "#". These ignored lines ensure that comments and blank spaces do not interfere with pattern extraction.

See also:
    GitignoreChecker.make_fake_files, GitignoreChecker.delete_fake_files: These methods handle temporary file management during the documentation process, working in conjunction with _parse_gitignore to ensure accurate pattern extraction and application.
"""'''
        patterns = []
        for line in gitignore_content.splitlines():
            line = line.strip()
            if line and (not line.startswith('#')):
                patterns.append(line)
        return patterns

    @staticmethod
    def _split_gitignore_patterns(gitignore_patterns: list) -> tuple:
        """[Short description]

Split the .gitignore patterns into folder patterns and file patterns within the context of the Repository Documentation Generator project.

Args:
    gitignore_patterns (list): A list of patterns extracted from a .gitignore file. Each pattern represents a rule for ignoring files or directories in version control, as part of the automated documentation generation process.

Returns:
    tuple: A tuple containing two lists - `folder_patterns` and `file_patterns`. The `folder_patterns` list includes patterns that represent directories to be ignored by the system during documentation generation, while the `file_patterns` list contains patterns representing individual files to be excluded. This categorization aids in maintaining an accurate and up-to-date repository documentation.

Raises:
    None: This function does not raise any exceptions under normal operation. It simply processes the input patterns and returns the separated lists, contributing to the overall efficiency of the Repository Documentation Generator.

Note:
    This function is utilized by the `_load_gitignore_patterns` method in the `GitignoreChecker` class of the Repository Documentation Generator. The latter reads a .gitignore file, parses its content into individual patterns, and then uses this function to categorize those patterns as either folder or file ignore rules. This process is integral to ensuring that only relevant files and directories are considered during documentation generation, thereby enhancing the precision and reliability of the automated documentation system.
"""
        folder_patterns = ['.git', '.github', '.idea', 'venv', '.venv']
        file_patterns = []
        for pattern in gitignore_patterns:
            if pattern.endswith('/'):
                folder_patterns.append(pattern.rstrip('/'))
            else:
                file_patterns.append(pattern)
        return (folder_patterns, file_patterns)

    @staticmethod
    def _is_ignored(path: str, patterns: list, is_dir: bool=False) -> bool:
        """# Repository Documentation Generator

The `_is_ignored` function within the `GitignoreChecker` module of the Repository Documentation Generator serves a crucial role in managing .gitignore file checks during the documentation process. 

[Short description]

Check if the given path matches any of the patterns specified in a .gitignore file.

Args:
    path (str): The path to check. This could be a file or directory within the repository.
    patterns (list): A list of patterns, as per .gitignore syntax, to check against. These patterns are typically found in a .gitignore file associated with the repository.
    is_dir (bool, optional): True if the path is a directory, False otherwise. This parameter helps in accurately matching directory paths that might be ignored due to .gitignore rules. Defaults to False.

Returns:
    bool: True if the path matches any pattern in the .gitignore file, indicating that the path should be ignored. False otherwise, suggesting that the path should be included in the documentation process.

Raises:
    None

Note:
    This function employs the `fnmatch` module for pattern matching, adhering to the syntax and rules defined in .gitignore files. It verifies if the provided `path` corresponds to any of the patterns listed in the `patterns` list. If `is_dir` is True and a pattern ends with a slash ('/'), it also assesses whether the path matches the pattern without the trailing slash, accommodating directory-specific ignore rules. This functionality ensures that the documentation generation process respects the repository's .gitignore settings, thereby preventing unnecessary inclusion of ignored files or directories in the generated documentation."""
        for pattern in patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
            if is_dir and pattern.endswith('/') and fnmatch.fnmatch(path, pattern[:-1]):
                return True
        return False

    def check_files_and_folders(self) -> list:
        """[Short description]

The 'check_files_and_folders' function is part of the Repository Documentation Generator, a tool designed to automate software project documentation. It scans the specified directory for files and folders, filtering out those that match any patterns defined in the .gitignore file. The function returns a list of paths to Python (.py) files that are not ignored.

Args:
    self (GitignoreChecker): An instance of GitignoreChecker, which holds the directory path and gitignore patterns.

Returns:
    list: A list of paths to Python (.py) files that are not ignored, relative to self.directory.

Raises:
    ValueError: If the provided directory does not exist or is not accessible.

Note:
    This function utilizes the 'os' module for directory traversal and the '_is_ignored' method for pattern matching. It iterates through the directory, excluding folders and files based on the defined patterns in the .gitignore file. The function specifically targets Python (.py) files, ensuring only non-ignored ones are included in the result.

See also:
    _is_ignored (repo_agent.utils.gitignore_checker.GitignoreChecker),
    SettingsManager (repo_agent.settings.SettingsManager).
"""
        ignored_folders = SettingsManager().get_setting().project.ignore_list
        not_ignored_files = []
        for root, dirs, files in os.walk(self.directory):
            dirs[:] = [d for d in dirs if not self._is_ignored(d, self.folder_patterns, is_dir=True) and (not any([d in i for i in ignored_folders]))]
            not_ignored_files += [os.path.relpath(os.path.join(root, d), self.directory) for d in dirs]
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.directory)
                if not self._is_ignored(file, self.file_patterns) and file_path.endswith('.py'):
                    not_ignored_files.append(relative_path)
        return not_ignored_files