import fnmatch
import os
from repo_agent.settings import SettingsManager


class GitignoreChecker:
    """
    Checks for files and folders in a directory, excluding those ignored by .gitignore.

    This class provides functionality to scan a specified directory and identify
    files and folders that are not excluded by the provided .gitignore file."""

    def __init__(self, directory: str, gitignore_path: str):
        """
        Initializes a checker for ignored files and directories, storing the target directory and path to the .gitignore file. Loads patterns from the .gitignore file for efficient matching.


        Args:
            directory: The directory to scan for ignored files.
            gitignore_path: The path to the .gitignore file.

        Returns:
            None"""

        self.directory = directory
        self.gitignore_path = gitignore_path
        self.folder_patterns, self.file_patterns = self._load_gitignore_patterns()

    def _load_gitignore_patterns(self) -> tuple:
        """
        Reads patterns from a .gitignore file, falling back to a default location if the specified file is not found, then parses and splits them.

            Args:
                None

            Returns:
                tuple: A tuple containing the split Gitignore patterns.
        """

        try:
            with open(self.gitignore_path, "r", encoding="utf-8") as file:
                gitignore_content = file.read()
        except FileNotFoundError:
            default_path = os.path.join(
                os.path.dirname(__file__), "..", "..", ".gitignore"
            )
            with open(default_path, "r", encoding="utf-8") as file:
                gitignore_content = file.read()
        patterns = self._parse_gitignore(gitignore_content)
        return self._split_gitignore_patterns(patterns)

    @staticmethod
    def _parse_gitignore(gitignore_content: str) -> list:
        """
        No valid docstring found."""

        patterns = []
        for line in gitignore_content.splitlines():
            line = line.strip()
            if line and (not line.startswith("#")):
                patterns.append(line)
        return patterns

    @staticmethod
    def _split_gitignore_patterns(gitignore_patterns: list) -> tuple:
        """
        Separates provided patterns into those representing directories and files. Directory patterns are identified by a trailing slash, which is then removed.

            Args:
                gitignore_patterns: A list of strings representing .gitignore patterns.

            Returns:
                tuple: A tuple containing two lists:
                    - The first list contains folder patterns.
                    - The second list contains file patterns."""

        folder_patterns = [".git", ".github", ".idea", "venv", ".venv"]
        file_patterns = []
        for pattern in gitignore_patterns:
            if pattern.endswith("/"):
                folder_patterns.append(pattern.rstrip("/"))
            else:
                file_patterns.append(pattern)
        return (folder_patterns, file_patterns)

    @staticmethod
    def _is_ignored(path: str, patterns: list, is_dir: bool = False) -> bool:
        """
        No valid docstring found."""

        for pattern in patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
            if is_dir and pattern.endswith("/") and fnmatch.fnmatch(path, pattern[:-1]):
                return True
        return False

    def check_files_and_folders(self) -> list:
        """
        Identifies and lists Python files and non-ignored folders within the specified directory.

            Args:
                None

            Returns:
                list: A list of relative paths to the non-ignored Python files and directories.
        """

        ignored_folders = SettingsManager().get_setting().project.ignore_list
        not_ignored_files = []
        for root, dirs, files in os.walk(self.directory):
            dirs[:] = [
                d
                for d in dirs
                if not self._is_ignored(d, self.folder_patterns, is_dir=True)
                and (not any([d in i for i in ignored_folders]))
            ]
            not_ignored_files += [
                os.path.relpath(os.path.join(root, d), self.directory) for d in dirs
            ]
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.directory)
                if not self._is_ignored(
                    file, self.file_patterns
                ) and file_path.endswith(".py"):
                    not_ignored_files.append(relative_path)
        return not_ignored_files
