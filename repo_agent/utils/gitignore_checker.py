import fnmatch
import os
from repo_agent.settings import SettingsManager

class GitignoreChecker:
    def __init__(self, directory: str, gitignore_path: str):
        self.directory = directory
        self.gitignore_path = gitignore_path
        self.folder_patterns, self.file_patterns = self._load_gitignore_patterns()

    def _load_gitignore_patterns(self) -> tuple:
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
        patterns = []
        for line in gitignore_content.splitlines():
            line = line.strip()
            if line and (not line.startswith('#')):
                patterns.append(line)
        return patterns

    @staticmethod
    def _split_gitignore_patterns(gitignore_patterns: list) -> tuple:
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
        for pattern in patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
            if is_dir and pattern.endswith('/') and fnmatch.fnmatch(path, pattern[:-1]):
                return True
        return False

    def check_files_and_folders(self) -> list:
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