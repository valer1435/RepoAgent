import fnmatch
import os
from repo_agent.settings import SettingsManager

class GitignoreChecker:
    """Initialize the GitignoreChecker instance.
    
    This class is used to manage and check files and directories against .gitignore patterns, ensuring that only relevant files are included in documentation generation processes.
    
    Args:
        directory (str): The directory to be checked.
        gitignore_path (str): The path to the .gitignore file.
    
    Returns:
        None
    
    Raises:
        ValueError: If either `directory` or `gitignore_path` is invalid.
    
    Note:
        See also: _load_gitignore_patterns method for more details on how patterns are loaded.
    
    Load and parse the .gitignore file, then split the patterns into folder and file categories.
    
    If the specified .gitignore file is not found, the function falls back to a default path. This functionality ensures that irrelevant files are ignored during documentation generation, maintaining project cleanliness and consistency.
    
    Args:
        None
    
    Returns:
        tuple: A tuple containing two lists - one for folder patterns and one for file patterns.
    
    Raises:
        FileNotFoundError: If the specified .gitignore file cannot be found.
    
    Note:
        See also: _parse_gitignore method for more details on how patterns are parsed.
    
    Parse the .gitignore file content and extract patterns as a list.
    
    This function processes the content of a .gitignore file and returns a list of patterns that are defined within it, ensuring that irrelevant files are ignored during documentation generation.
    
    Args:
        gitignore_content (str): The content of the .gitignore file to be parsed.
    
    Returns:
        list: A list of patterns extracted from the .gitignore content.
    
    Note:
        This functionality is part of the Repository Agent's code analysis feature, which helps in generating and maintaining accurate documentation for Python projects.
    
    Split the .gitignore patterns into folder and file patterns.
    
    This function processes the list of patterns from the .gitignore file and categorizes them into two distinct lists: one for folder patterns and another for file patterns. This is useful in managing project structure by ensuring that documentation generation adheres to project guidelines and ignores irrelevant files.
    
    Args:
        gitignore_patterns (list): A list of patterns extracted from the .gitignore file.
    
    Returns:
        tuple: Two lists, where the first element is a list of folder patterns and the second element is a list of file patterns.
    
    Check if the given path matches any of the specified patterns.
    
    This function evaluates whether a given file or directory path is ignored based on a list of patterns, similar to how `.gitignore` files operate. This utility is part of the Repository Agent's functionality for managing and documenting repository contents efficiently by ensuring that irrelevant files are excluded from documentation generation.
    
    Args:
        path (str): The path to check.
        patterns (list): A list of patterns to match against the path.
        is_dir (bool, optional): True if the path is a directory, False otherwise. Defaults to False.
    
    Returns:
        bool: True if the path matches any pattern in the list, False otherwise.
    
    Note:
        See also: GitignoreChecker for more details on managing ignored files within the Repository Agent.
    
    Check all files and folders in the given directory against the split gitignore patterns.
    
    This function identifies Python files that are not ignored by the .gitignore rules within a specified repository directory, ensuring that only relevant files are included in documentation generation processes.
    
    Args:
        None
    
    Returns:
        list: A list of relative file paths to '.py' files that are not ignored by the gitignore rules.
    
    Raises:
        ValueError: If an invalid setting is provided by SettingsManager.
    
    Note:
        The returned file paths are relative to the self.directory."""

    def __init__(self, directory: str, gitignore_path: str):
        """Initializes the GitignoreChecker instance.
    
    This method initializes an instance of the GitignoreChecker class by setting up the directory and .gitignore file path, and loading patterns from the .gitignore file. This is part of the Repository Agent's utility functions designed to manage file operations and ensure that generated documentation adheres to project guidelines while ignoring irrelevant files.
    
    Args:
        directory (str): The directory to be checked.
        gitignore_path (str): The path to the .gitignore file.
    
    Returns:
        None
    
    Raises:
        ValueError: If either `directory` or `gitignore_path` is invalid.
    
    Note:
        See also: _load_gitignore_patterns method for more details on how patterns are loaded."""
        self.directory = directory
        self.gitignore_path = gitignore_path
        self.folder_patterns, self.file_patterns = self._load_gitignore_patterns()

    def _load_gitignore_patterns(self) -> tuple:
        """Loads the .gitignore file and parses its patterns into folder and file categories.
    
    This method reads the content of the .gitignore file and processes it to categorize the patterns into folder and file patterns. If the specified .gitignore file is not found, it falls back to a default path. This functionality ensures that irrelevant files are ignored during documentation generation, maintaining project cleanliness and consistency.
    
    Args:  
        None  
    
    Returns:  
        tuple: A tuple containing two lists - one for folder patterns and one for file patterns.  
    
    Raises:  
        FileNotFoundError: If the specified .gitignore file cannot be found.  
    
    Note:  
        See also: _parse_gitignore method for more details on how patterns are parsed."""
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
        """Parses the .gitignore file content and extracts patterns as a list.
    
    This method processes the content of a .gitignore file and returns a list of patterns that are defined within it, ensuring that irrelevant files are ignored during documentation generation.
    
    Args:
        gitignore_content (str): The content of the .gitignore file to be parsed.
    
    Returns:
        list: A list of patterns extracted from the .gitignore content.
    
    Note:
        This functionality is part of the Repository Agent's code analysis feature, which helps in generating and maintaining accurate documentation for Python projects."""
        patterns = []
        for line in gitignore_content.splitlines():
            line = line.strip()
            if line and (not line.startswith('#')):
                patterns.append(line)
        return patterns

    @staticmethod
    def _split_gitignore_patterns(gitignore_patterns: list) -> tuple:
        """Splits the .gitignore patterns into folder and file patterns.
    
    This method processes the list of patterns from the .gitignore file and categorizes them into two distinct lists: one for folder patterns and another for file patterns. This is useful in managing project structure by ensuring that documentation generation adheres to project guidelines and ignores irrelevant files.
    
    Args:
        gitignore_patterns (list): A list of patterns extracted from the .gitignore file.
    
    Returns:
        tuple: Two lists, where the first element is a list of folder patterns and the second element is a list of file patterns.
    
    Note:
        See also: _load_gitignore_patterns method for more details on how patterns are loaded and parsed."""
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
        """Check if the given path matches any of the specified patterns.
    
    This method evaluates whether a given file or directory path is ignored based on a list of patterns, similar to how `.gitignore` files operate. This utility is part of the Repository Agent's functionality for managing and documenting repository contents efficiently by ensuring that irrelevant files are excluded from documentation generation.
    
    Args:  
        path (str): The path to check.  
        patterns (list): A list of patterns to match against the path.  
        is_dir (bool, optional): True if the path is a directory, False otherwise. Defaults to False.
    
    Returns:  
        bool: True if the path matches any pattern in the list, False otherwise.
    
    Note:  
        See also: GitignoreChecker for more details on managing ignored files within the Repository Agent."""
        for pattern in patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
            if is_dir and pattern.endswith('/') and fnmatch.fnmatch(path, pattern[:-1]):
                return True
        return False

    def check_files_and_folders(self) -> list:
        """Check all files and folders in the given directory against the split gitignore patterns.
    
    This method identifies Python files that are not ignored by the .gitignore rules within a specified repository directory, ensuring that only relevant files are included in documentation generation processes.
    
    Args:
        None
    
    Returns:
        list: A list of relative file paths to '.py' files that are not ignored by the gitignore rules.
    
    Raises:
        ValueError: If an invalid setting is provided by SettingsManager.
    
    Note:
        The returned file paths are relative to the self.directory."""
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