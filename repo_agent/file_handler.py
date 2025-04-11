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
    def __init__(self, repo_path, file_path):
        self.file_path = file_path
        self.repo_path = repo_path
        setting = SettingsManager.get_setting()
        self.project_hierarchy = setting.project.target_repo / setting.project.hierarchy_name

    def read_file(self):
        abs_file_path = os.path.join(self.repo_path, self.file_path)
        with open(abs_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content

    def get_obj_code_info(self, code_type, code_name, start_line, end_line, params, file_path=None, docstring='', source_node=None):
        code_info = {}
        code_info['type'] = code_type
        code_info['name'] = code_name
        code_info['md_content'] = []
        code_info['code_start_line'] = start_line
        code_info['code_end_line'] = end_line
        code_info['params'] = params
        code_info['docstring'] = docstring
        code_info['source_node'] = source_node
        with open(os.path.join(self.repo_path, file_path if file_path != None else self.file_path), 'r', encoding='utf-8') as code_file:
            lines = code_file.readlines()
            code_content = ''.join(lines[start_line - 1:end_line])
            name_column = lines[start_line - 1].find(code_name)
            if 'return' in code_content:
                have_return = True
            else:
                have_return = False
            code_info['have_return'] = have_return
            code_info['code_content'] = code_content
            code_info['name_column'] = name_column
        return code_info

    def write_file(self, file_path, content):
        if file_path.startswith('/'):
            file_path = file_path[1:]
        abs_file_path = os.path.join(self.repo_path, file_path)
        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
        with open(abs_file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def get_modified_file_versions(self):
        repo = git.Repo(self.repo_path)
        current_version_path = os.path.join(self.repo_path, self.file_path)
        with open(current_version_path, 'r', encoding='utf-8') as file:
            current_version = file.read()
        commits = list(repo.iter_commits(paths=self.file_path, max_count=1))
        previous_version = None
        if commits:
            commit = commits[0]
            try:
                previous_version = (commit.tree / self.file_path).data_stream.read().decode('utf-8')
            except KeyError:
                previous_version = None
        return (current_version, previous_version)

    def get_end_lineno(self, node):
        if not hasattr(node, 'lineno'):
            return -1
        end_lineno = node.lineno
        for child in ast.iter_child_nodes(node):
            child_end = getattr(child, 'end_lineno', None) or self.get_end_lineno(child)
            if child_end > -1:
                end_lineno = max(end_lineno, child_end)
        return end_lineno

    def add_parent_references(self, node, parent=None):
        for child in ast.iter_child_nodes(node):
            child.parent = node
            self.add_parent_references(child, node)

    def get_functions_and_classes(self, code_content):
        tree = ast.parse(code_content)
        self.add_parent_references(tree)
        functions_and_classes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = self.get_end_lineno(node)
                parameters = [arg.arg for arg in node.args.args] if 'args' in dir(node) else []
                all_names = [item[1] for item in functions_and_classes]
                functions_and_classes.append((type(node).__name__, node.name, start_line, end_line, parameters, ast.get_docstring(node), node))
        return functions_and_classes

    def generate_file_structure(self, file_path):
        if os.path.isdir(os.path.join(self.repo_path, file_path)):
            return [{'type': 'Dir', 'name': file_path, 'content': '', 'md_content': [], 'code_start_line': -1, 'code_end_line': -1}]
        else:
            with open(os.path.join(self.repo_path, file_path), 'r', encoding='utf-8') as f:
                content = f.read()
                structures = self.get_functions_and_classes(content)
                file_objects = []
                for struct in structures:
                    structure_type, name, start_line, end_line, params, docstring, source_node = struct
                    code_info = self.get_obj_code_info(structure_type, name, start_line, end_line, params, file_path, docstring, source_node)
                    file_objects.append(code_info)
        return file_objects

    def generate_overall_structure(self, file_path_reflections, jump_files) -> dict:
        repo_structure = {}
        gitignore_checker = GitignoreChecker(directory=self.repo_path, gitignore_path=os.path.join(self.repo_path, '.gitignore'))
        bar = tqdm(gitignore_checker.check_files_and_folders())
        for not_ignored_files in bar:
            normal_file_names = not_ignored_files
            if not_ignored_files in jump_files:
                print(f'{Fore.LIGHTYELLOW_EX}[File-Handler] Unstaged AddFile, ignore this file: {Style.RESET_ALL}{normal_file_names}')
                continue
            elif not_ignored_files.endswith(latest_verison_substring):
                print(f'{Fore.LIGHTYELLOW_EX}[File-Handler] Skip Latest Version, Using Git-Status Version]: {Style.RESET_ALL}{normal_file_names}')
                continue
            try:
                repo_structure[normal_file_names] = self.generate_file_structure(not_ignored_files)
            except Exception as e:
                logger.error(f'Alert: An error occurred while generating file structure for {not_ignored_files}: {e}')
                continue
            bar.set_description(f'generating repo structure: {not_ignored_files}')
        return repo_structure

    def convert_to_markdown_file(self, file_path=None):
        with open(self.project_hierarchy, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        if file_path is None:
            file_path = self.file_path
        file_dict = json_data.get(file_path)
        if file_dict is None:
            raise ValueError(f'No file object found for {self.file_path} in project_hierarchy.json')
        markdown = ''
        parent_dict = {}
        objects = sorted(file_dict.values(), key=lambda obj: obj['code_start_line'])
        for obj in objects:
            if obj['parent'] is not None:
                parent_dict[obj['name']] = obj['parent']
        current_parent = None
        for obj in objects:
            level = 1
            parent = obj['parent']
            while parent is not None:
                level += 1
                parent = parent_dict.get(parent)
            if level == 1 and current_parent is not None:
                markdown += '***\n'
            current_parent = obj['name']
            params_str = ''
            if obj['type'] in ['FunctionDef', 'AsyncFunctionDef']:
                params_str = '()'
                if obj['params']:
                    params_str = f'({', '.join(obj['params'])})'
            markdown += f'{'#' * level} {obj['type']} {obj['name']}{params_str}:\n'
            markdown += f'{(obj['md_content'][-1] if len(obj['md_content']) > 0 else '')}\n'
        markdown += '***\n'
        return markdown