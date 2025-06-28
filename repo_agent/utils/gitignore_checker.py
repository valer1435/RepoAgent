import fnmatch
import os
from repo_agent.settings import SettingsManager


class GitignoreChecker:
    """
    Checks a directory for files and folders, respecting .gitignore rules."""

    def __init__(self, directory: str, gitignore_path: str):
        """
        Initializes a checker for identifying ignored files and directories within a project, storing the target directory and path to the .gitignore file. It then loads patterns from the .gitignore file to determine which items should be excluded during analysis.

            Args:
                directory: The directory to scan.
                gitignore_path: The path to the .gitignore file.

            Returns:
                None
        """

        self.directory = directory
        self.gitignore_path = gitignore_path
        self.folder_patterns, self.file_patterns = self._load_gitignore_patterns()

    def _load_gitignore_patterns(self) -> tuple:
        """
        Reads patterns from the .gitignore file, falling back to a default location if the project-specific file is not found. These patterns are then parsed and split for use in filtering files during repository analysis.

            Attempts to load patterns from the instance's gitignore path,
            and if that fails, falls back to a default location.

            Args:
                None

            Returns:
                tuple: A tuple of strings representing the gitignore patterns.
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
        Extracts patterns from a .gitignore file content.

            Args:
                gitignore_content: The string content of the .gitignore file.

            Returns:
                list: A list of strings, where each string is a pattern from the
                    .gitignore file.  Empty lines and comments (lines starting with '#')
                    are ignored.
        """

        patterns = []
        for line in gitignore_content.splitlines():
            line = line.strip()
            if line and (not line.startswith("#")):
                patterns.append(line)
        return patterns

    @staticmethod
    def _split_gitignore_patterns(gitignore_patterns: list) -> tuple:
        """
        Categorizes gitignore patterns, separating those representing directories from those representing files.

            Args:
                gitignore_patterns: A list of strings representing gitignore patterns.

            Returns:
                A tuple containing two lists:
                - The first list contains folder patterns (ending with '/').
                - The second list contains file patterns (not ending with '/').
        """

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
        Determines if a file or directory path matches any of the provided ignore patterns.

          Args:
            path: The path to check.
            patterns: A list of glob-style patterns to match against the path.
            is_dir: Whether the path is a directory. Defaults to False.

          Returns:
            bool: True if the path matches any of the ignore patterns, False otherwise.
        """

        for pattern in patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
            if is_dir and pattern.endswith("/") and fnmatch.fnmatch(path, pattern[:-1]):
                return True
        return False

    def check_files_and_folders(self) -> list:
        """
        Identifies and lists project files and folders that are not ignored based on configured patterns and settings.

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
