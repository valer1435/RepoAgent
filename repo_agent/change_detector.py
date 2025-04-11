import os
import re
import subprocess
import git
from colorama import Fore, Style
from repo_agent.file_handler import FileHandler
from repo_agent.settings import SettingsManager

class ChangeDetector:

    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def get_staged_pys(self):
        repo = self.repo
        staged_files = {}
        diffs = repo.index.diff('HEAD', R=True)
        for diff in diffs:
            if diff.change_type in ['A', 'M'] and diff.a_path.endswith('.py'):
                is_new_file = diff.change_type == 'A'
                staged_files[diff.a_path] = is_new_file
        return staged_files

    def get_file_diff(self, file_path, is_new_file):
        repo = self.repo
        if is_new_file:
            add_command = f'git -C {repo.working_dir} add {file_path}'
            subprocess.run(add_command, shell=True, check=True)
            diffs = repo.git.diff('--staged', file_path).splitlines()
        else:
            diffs = repo.git.diff('HEAD', file_path).splitlines()
        return diffs

    def parse_diffs(self, diffs):
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
        changes_in_structures = {'added': set(), 'removed': set()}
        for change_type, lines in changed_lines.items():
            for line_number, _ in lines:
                for structure_type, name, start_line, end_line, parent_structure in structures:
                    if start_line <= line_number <= end_line:
                        changes_in_structures[change_type].add((name, parent_structure))
        return changes_in_structures

    def get_to_be_staged_files(self):
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
        unstaged_files_meeting_conditions = self.get_to_be_staged_files()
        for file_path in unstaged_files_meeting_conditions:
            add_command = f'git -C {self.repo.working_dir} add {file_path}'
            subprocess.run(add_command, shell=True, check=True)
        return unstaged_files_meeting_conditions
