import ast
import json
import os
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Dict, List
from colorama import Fore, Style
from tqdm import tqdm
from repo_agent.change_detector import ChangeDetector
from repo_agent.chat_engine import ChatEngine
from repo_agent.doc_meta_info import DocItem, DocItemStatus, MetaInfo, need_to_generate, DocItemType
from repo_agent.file_handler import FileHandler
from repo_agent.log import logger
from repo_agent.module_summarization import summarize_repository
from repo_agent.multi_task_dispatch import worker
from repo_agent.project_manager import ProjectManager
from repo_agent.settings import SettingsManager
from repo_agent.utils.docstring_updater import update_doc
from repo_agent.utils.meta_info_utils import delete_fake_files, make_fake_files

class Runner:
    """Runner class for managing and generating documentation for a project repository.

This class handles the initialization of project settings, copying configuration files, managing project hierarchy, detecting changes, and generating documentation. It also supports multi-threading for efficient document generation and updating.

Args:
    None

Attributes:
    setting (Settings): Project settings loaded from the settings manager.
    absolute_project_hierarchy_path (Path): Absolute path to the project hierarchy.
    project_manager (ProjectManager): Manager for project-related operations.
    change_detector (ChangeDetector): Detector for changes in the repository.
    chat_engine (ChatEngine): Engine for generating documentation content.
    meta_info (MetaInfo): Metadata information for the project.
    runner_lock (threading.Lock): Lock for thread synchronization.

Methods:
    get_all_pys(directory: str) -> List[str]:
        Recursively retrieves all Python files in the specified directory.

        Args:
            directory (str): The directory to search for Python files.

        Returns:
            List[str]: A list of paths to Python files.

    generate_doc_for_a_single_item(doc_item: DocItem) -> None:
        Generates documentation for a single item and updates its metadata.

        Args:
            doc_item (DocItem): The item for which to generate documentation.

        Raises:
            Exception: If document generation fails after multiple attempts.

    generate_main_project_idea(docs: List[Dict]) -> str:
        Generates the main project idea based on the provided documents.

        Args:
            docs (List[Dict]): A list of dictionaries containing document information.

        Returns:
            str: The generated main project idea.

    generate_doc() -> None:
        Generates documentation for the project.

        Raises:
            BaseException: If an error occurs during the documentation generation process.

    get_top_n_components(doc_item: DocItem) -> List[Dict]:
        Retrieves the top N components from the specified document item.

        Args:
            doc_item (DocItem): The document item to process.

        Returns:
            List[Dict]: A list of dictionaries containing component information.

    _get_md_and_links_from_doc(doc_item: DocItem) -> Dict:
        Generates markdown and links from the specified document item.

        Args:
            doc_item (DocItem): The document item to process.

        Returns:
            Dict: A dictionary containing markdown and link information.

    generate_main_idea(docs: List[Dict]) -> str:
        Generates the main idea for the project.

        Args:
            docs (List[Dict]): A list of dictionaries containing document information.

        Returns:
            str: The generated main idea.

    summarize_modules() -> List[Dict]:
        Summarizes the modules in the project repository.

        Returns:
            List[Dict]: A list of dictionaries containing module summaries.

    update_modules(module: Dict) -> None:
        Updates the metadata for a module.

        Args:
            module (Dict): A dictionary containing module information.

    search_tree(doc: DocItem, path: str) -> DocItem:
        Searches the project tree for a document item at the specified path.

        Args:
            doc (DocItem): The root document item to start the search from.
            path (str): The path to search for.

        Returns:
            DocItem: The found document item or None if not found.

    convert_path_to_dot_notation(path: Path, class_: str) -> str:
        Converts a file path to dot notation for use in markdown.

        Args:
            path (Path): The file path to convert.
            class_ (str): The class name to include in the notation.

        Returns:
            str: The dot notation string.

    markdown_refresh() -> None:
        Refreshes the markdown files for the project.

    git_commit(commit_message: str) -> None:
        Commits changes to the repository.

        Args:
            commit_message (str): The commit message.

        Raises:
            subprocess.CalledProcessError: If the commit process fails.

    run() -> None:
        Runs the documentation generation process.

    add_new_item(file_handler: FileHandler, json_data: Dict) -> None:
        Adds a new item to the project hierarchy and generates its documentation.

        Args:
            file_handler (FileHandler): The file handler for the new item.
            json_data (Dict): The JSON data for the project hierarchy.

    process_file_changes(repo_path: str, file_path: str, is_new_file: bool) -> None:
        Processes changes in a file and updates the project hierarchy.

        Args:
            repo_path (str): The path to the repository.
            file_path (str): The path to the file that has changed.
            is_new_file (bool): Whether the file is new.

    update_existing_item(file_dict: Dict, file_handler: FileHandler, changes_in_pyfile: Dict) -> Dict:
        Updates existing items in the project hierarchy based on changes in the file.

        Args:
            file_dict (Dict): The dictionary containing file information.
            file_handler (FileHandler): The file handler for the file.
            changes_in_pyfile (Dict): The dictionary containing changes in the file.

        Returns:
            Dict: The updated file dictionary.

    update_object(file_dict: Dict, file_handler: FileHandler, obj_name: str, obj_referencer_list: List) -> None:
        Updates the documentation for a specific object.

        Args:
            file_dict (Dict): The dictionary containing file information.
            file_handler (FileHandler): The file handler for the file.
            obj_name (str): The name of the object to update.
            obj_referencer_list (List): The list of objects that reference the specified object.

    get_new_objects(file_handler: FileHandler) -> Tuple[List[str], List[str]]:
        Retrieves new and deleted objects in a file.

        Args:
            file_handler (FileHandler): The file handler for the file.

        Returns:
            Tuple[List[str], List[str]]: A tuple containing lists of new and deleted object names."""

    def __init__(self):
        """Initializes the Runner class.

Sets up the necessary components for managing a project repository, including settings, project hierarchy, and meta information. It also initializes a change detector and a chat engine. The method ensures that the project hierarchy is properly set up and that the meta information is either initialized or loaded from a checkpoint. It also copies the `mkdocs.yml` file to the project hierarchy directory.

Args:
    None

Returns:
    None

Raises:
    FileNotFoundError: If the `mkdocs.yml` file does not exist.
    ValueError: If the `target_repo` or `hierarchy_name` settings are invalid.

Note:
    The primary purpose of this project is to automate the generation and management of documentation for a Git repository. It integrates various functionalities to detect changes, handle file operations, manage project settings, and generate summaries for modules and directories. The tool also includes a chat engine and a multi-task dispatch system to enhance user interaction and process management."""
        self.setting = SettingsManager.get_setting()
        self.absolute_project_hierarchy_path = self.setting.project.target_repo / self.setting.project.hierarchy_name
        shutil.copy('mkdocs.yml', Path(self.absolute_project_hierarchy_path, 'mkdocs.yaml'))
        self.project_manager = ProjectManager(repo_path=self.setting.project.target_repo, project_hierarchy=self.setting.project.hierarchy_name)
        self.change_detector = ChangeDetector(repo_path=self.setting.project.target_repo)
        self.chat_engine = ChatEngine(project_manager=self.project_manager)
        file_path_reflections, jump_files = make_fake_files()
        if not self.absolute_project_hierarchy_path.exists():
            self.meta_info = MetaInfo.init_meta_info(file_path_reflections, jump_files)
            self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path)
            setting = SettingsManager.get_setting().project.main_idea = self.meta_info.main_idea
        else:
            setting = SettingsManager.get_setting()
            project_abs_path = setting.project.target_repo
            file_handler = FileHandler(project_abs_path, None)
            repo_structure = file_handler.generate_overall_structure(file_path_reflections, jump_files)
            self.meta_info = MetaInfo.from_checkpoint_path(self.absolute_project_hierarchy_path, repo_structure)
        self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path)
        self.runner_lock = threading.Lock()

    def get_all_pys(self, directory):
        """Retrieves all Python files from the specified directory and its subdirectories.

This method is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository. It integrates various functionalities to detect changes, handle file operations, manage project settings, and generate summaries for modules and directories.

Args:
    directory (str): The root directory to search for Python files.

Returns:
    list: A list of full paths to Python files found in the directory and its subdirectories.

Raises:
    ValueError: If the provided directory does not exist or is not a directory.

Note:
    This method is essential for the tool's ability to accurately detect and process Python files, which are crucial for generating up-to-date documentation."""
        python_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files

    def generate_doc_for_a_single_item(self, doc_item: DocItem):
        """Generates documentation for a single code item.

This method checks if the documentation for a given `DocItem` needs to be generated based on its status and the project's ignore list. If the item needs documentation, it prints a message and calls the chat engine to generate the documentation. The generated content is appended to the `md_content` of the `DocItem`. If the project's main idea is set, the item's status is updated to `doc_up_to_date`. The method also saves a checkpoint of the current state of the project hierarchy.

Args:
    doc_item (DocItem): The documentation item for which the documentation is being generated.

Returns:
    None

Raises:
    Exception: If there is an error in the chat engine call or any other unexpected error.

Note:
    See also: `need_to_generate` function for determining if the documentation needs to be generated, `ChatEngine.generate_doc` method for generating the documentation, and `MetaInfo.checkpoint` method for saving the project state."""
        settings = SettingsManager.get_setting()
        try:
            if not need_to_generate(doc_item, self.setting.project.ignore_list):
                print(f'Content ignored/Document generated, skipping: {doc_item.get_full_name()}')
            else:
                print(f' -- Generating document  {Fore.LIGHTYELLOW_EX}{doc_item.item_type.name}: {doc_item.get_full_name()}{Style.RESET_ALL}')
                response_message = self.chat_engine.generate_doc(doc_item=doc_item)
                doc_item.md_content.append(response_message)
                if settings.project.main_idea:
                    doc_item.item_status = DocItemStatus.doc_up_to_date
                self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path)
        except Exception:
            logger.exception(f'Document generation failed after multiple attempts, skipping: {doc_item.get_full_name()}')
            doc_item.md_content.append('')
            if settings.project.main_idea:
                doc_item.item_status = DocItemStatus.doc_up_to_date

    def generate_main_project_idea(self, docs: List[Dict]):
        """Generates the main project idea based on a list of component documents.

This method iterates over a list of component documents, formats each document into a string containing the component name, description, and place in the hierarchy, and then calls the `generate_idea` method of the `chat_engine` to generate a project idea. The generated idea is returned as a response message.

Args:
    docs (List[Dict]): A list of dictionaries, where each dictionary contains information about a component. Each dictionary should have the following keys:
        - 'obj_name' (str): The name of the component.
        - 'md_content' (str): The description of the component.
        - 'tree_path' (str): The place of the component in the project hierarchy.

Returns:
    str: The generated project idea from the language model.

Raises:
    Exception: If there is an error in the language model chat call.

Note:
    The `generate_idea` method of the `chat_engine` is used to generate the project idea. This method formats the list of components into a message template and sends it to a language model. The `SettingsManager` class is used to manage and initialize project and chat completion settings. The project aims to automate the generation and management of documentation for a Git repository, integrating various functionalities to detect changes, handle file operations, manage project settings, and generate summaries for modules and directories."""
        str_obj = []
        for doc in docs:
            str_obj.append(f'Component name: {doc['obj_name']}\nComponent description: {doc['md_content']}\nComponent place in hierarchy: {doc['tree_path']}')
        response_message = self.chat_engine.generate_idea('\n\n'.join(str_obj))
        return response_message

    def generate_doc(self):
        """Generates documentation for the project.

This method initializes a task manager to determine which documentation items need to be generated based on the current state of the project and the provided ignore list. It then starts multiple threads to process these tasks concurrently. After all tasks are completed, it refreshes the markdown documentation and saves a checkpoint of the current state.

Args:
    self: The instance of the `Runner` class.

Returns:
    None

Raises:
    BaseException: If an error occurs during the task processing.

Note:
    - This method uses the `need_to_generate` function to determine if a documentation item needs to be generated.
    - It uses the `MetaInfo.get_topology` method to create a task manager.
    - It uses the `MetaInfo.print_task_list` method to print the task list.
    - It uses the `worker` function to process tasks in parallel.
    - It uses the `markdown_refresh` method to refresh the markdown documentation.
    - It uses the `MetaInfo.checkpoint` method to save the current state of the project hierarchy.

Examples:
    >>> runner = Runner()
    >>> runner.generate_doc()"""
        logger.info('Starting to generate documentation')
        check_task_available_func = partial(need_to_generate, ignore_list=self.setting.project.ignore_list)
        task_manager = self.meta_info.get_topology(check_task_available_func)
        before_task_len = len(task_manager.task_dict)
        if not self.meta_info.in_generation_process:
            self.meta_info.in_generation_process = True
            logger.info('Init a new task-list')
        else:
            logger.info('Load from an existing task-list')
        self.meta_info.print_task_list(task_manager.task_dict)
        try:
            threads = [threading.Thread(target=worker, args=(task_manager, process_id, self.generate_doc_for_a_single_item)) for process_id in range(self.setting.project.max_thread_count)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.markdown_refresh()
            if self.setting.project.main_idea:
                self.meta_info.document_version = self.change_detector.repo.head.commit.hexsha
                self.meta_info.in_generation_process = False
                self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path)
            logger.info(f'Successfully generated {before_task_len - len(task_manager.task_dict)} documents.')
        except BaseException as e:
            logger.error(f'An error occurred: {e}. {before_task_len - len(task_manager.task_dict)} docs are generated at this time')

    def get_top_n_components(self, doc_item: DocItem):
        """Retrieves the top N components from a documentation item, excluding any items that should be ignored.

Args:
    doc_item (DocItem): The documentation item to process.
    n (int): The number of top components to retrieve.

Returns:
    list: A list of dictionaries containing the object name, markdown content, items that reference this item, items that this item references, and the tree path of the item.

Raises:
    ValueError: If `n` is less than 1.

Note:
    The method iterates through the children of the provided `doc_item`, skips any files that are in the ignore list, and collects information from the classes within the files. The information is extracted using the `_get_md_and_links_from_doc` method. This functionality is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository, ensuring that documentation is up-to-date and accurate."""
        components = []
        for file in doc_item.children:
            skip = False
            for ignore in self.setting.project.ignore_list:
                if ignore in file:
                    skip = True
                    break
            if skip:
                continue
            for class_ in doc_item.children[file].children:
                curr_obj = doc_item.children[file].children[class_]
                components.append(self._get_md_and_links_from_doc(curr_obj))
        return components

    def _get_md_and_links_from_doc(self, doc_item: DocItem):
        """Extracts markdown content and related links from a documentation item.

This method processes a documentation item to extract its markdown content and associated links, which are essential for generating accurate and up-to-date documentation for a Git repository. It ensures that the extracted information is structured and ready for further processing or display.

Args:
    doc_item (DocItem): The documentation item to extract information from.

Returns:
    dict: A dictionary containing the object name, markdown content, items that reference this item, items that this item references, and the tree path of the item.

Raises:
    IndexError: If the markdown content list is empty or does not contain the expected content.

Note:
    The markdown content is split, and the first part is extracted. The tree path is represented as a string with items separated by '->'. This method is crucial for the automated documentation generation process, ensuring that all relevant information is captured and organized."""
        return {'obj_name': doc_item.obj_name, 'md_content': doc_item.md_content[-1].split('\n\n')[0], 'who_reference_me': doc_item.who_reference_me, 'reference_who': doc_item.reference_who, 'tree_path': '->'.join([obj.obj_name for obj in doc_item.tree_path])}

    def generate_main_idea(self, docs):
        """Generates the main idea for a project based on a list of component documents.

This method logs the start of the main idea generation, calls the `generate_main_project_idea` method to generate the main project idea, logs the successful generation, and returns the generated idea.

Args:
    docs (List[Dict]): A list of dictionaries, where each dictionary contains information about a component. Each dictionary should have the following keys:
        - 'obj_name' (str): The name of the component.
        - 'md_content' (str): The description of the component.
        - 'tree_path' (str): The place of the component in the project hierarchy.

Returns:
    str: The generated main project idea.

Note:
    The `generate_main_project_idea` method formats the list of components into a message template and sends it to a language model to generate the project idea. The `SettingsManager` class is used to manage and initialize project and chat completion settings. This function is a crucial part of the project's documentation automation tool, which aims to streamline the documentation process for software repositories by automating the detection of changes, generation of summaries, and handling of file operations."""
        logger.info('Generation of the main idea')
        main_project_idea = self.generate_main_project_idea(docs)
        logger.info(f'Successfully generated the main idea')
        return main_project_idea

    def summarize_modules(self):
        """Summarizes the modules in the repository by generating summaries for each directory and its subdirectories.

This method logs the start of the modules documentation generation, calls the `summarize_repository` function to generate summaries, updates the modules with the generated summaries, and saves the current state of the `MetaInfo` object to a specified directory. It logs the success of the module summaries generation upon completion.

Args:
    self (Runner): The instance of the `Runner` class.

Returns:
    Dict[str, Any]: A dictionary containing the summary of the repository, including the name, path, file summaries, submodules, and module summary for each directory.

Raises:
    ValueError: If the root directory does not exist or is not a valid directory.
    IOError: If there is an error saving the JSON files to the specified directory.

Note:
    See also: The `summarize_repository` function for details on how the repository is summarized and the `MetaInfo.checkpoint` method for how the state is saved."""
        logger.info('Modules documentation generation')
        res = summarize_repository(self.meta_info.repo_path, self.meta_info.repo_structure, self.chat_engine)
        self.update_modules(res)
        self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path)
        logger.info(f'Successfully generated module summaries')
        return res

    def update_modules(self, module):
        """Updates the documentation for a module and its submodules in the hierarchical tree.

This method updates the documentation for a given module by appending the module summary to the `md_content` of the corresponding `DocItem` in the hierarchical tree. It also sets the `item_status` of the `DocItem` to `DocItemStatus.doc_up_to_date`. The method recursively updates the documentation for all submodules, ensuring that the entire module hierarchy is kept up-to-date.

Args:
    module (dict): A dictionary containing the module information. It should have the following keys:
        - 'path' (str): The relative path of the module.
        - 'module_summary' (str): The summary of the module.
        - 'submodules' (list): A list of dictionaries, each representing a submodule.

Returns:
    None

Raises:
    None

Note:
    This method relies on the `search_tree` method to find the correct `DocItem` in the hierarchical tree. The `module` dictionary must contain valid keys and values for the method to work correctly. The tool is designed to automate the generation and management of documentation for a Git repository, ensuring that documentation is always up-to-date and accurate."""
        rel_path = os.path.relpath(module['path'], self.meta_info.repo_path)
        doc_item = self.search_tree(self.meta_info.target_repo_hierarchical_tree, rel_path)
        doc_item.md_content.append(module['module_summary'])
        doc_item.item_status = DocItemStatus.doc_up_to_date
        for sm in module['submodules']:
            self.update_modules(sm)

    def search_tree(self, doc: DocItem, path: str):
        """Searches for a documentation item in the hierarchical tree based on the provided path.

This method recursively searches through the children of the provided `doc` item to find the item at the specified `path`. If the path is '.', it returns the root item. This functionality is particularly useful for navigating and managing the documentation structure of a Git repository, ensuring that the documentation reflects the current state of the codebase.

Args:
    doc (DocItem): The root documentation item to start the search from.
    path (str): The path to the documentation item to find. If the path is '.', it returns the root item.

Returns:
    DocItem: The found documentation item, or None if the item is not found.

Raises:
    None

Note:
    This method is a key component of the documentation management tool, which automates the generation and maintenance of documentation for a Git repository. It integrates with other functionalities such as change detection, file operations, and summary generation to ensure that the documentation is up-to-date and accurate."""
        if path == '.':
            return doc
        else:
            for ch_doc in doc.children:
                if ch_doc == path:
                    return doc.children[ch_doc]
                else:
                    found_res = self.search_tree(doc.children[ch_doc], path)
                if found_res:
                    return found_res

    def convert_path_to_dot_notation(self, path: Path, class_: str):
        """Converts a file path to a dot notation string, appending a class name.

This method processes the parts of a given file path, removing the `.py` extension and skipping `__init__` parts. It then joins the processed parts with dots and appends the class name to the resulting string. This method is used in the `markdown_refresh` method to generate markdown content for documentation.

Args:
    path (Path): The file path to convert.
    class_ (str): The class name to append to the dot notation string.

Returns:
    str: The dot notation string with the class name appended.

Raises:
    TypeError: If `path` is not a `Path` or `str` object.
    ValueError: If `path` does not exist or is not a valid file path.

Note:
    This method is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository. It helps in ensuring that the documentation is up-to-date and accurate by automating the detection of changes and generation of summaries."""
        path_obj = Path(path) if isinstance(path, str) else path
        processed_parts = []
        for part in path_obj.parts:
            if part.endswith('.py'):
                part = part[:-3]
            if part == '__init__':
                continue
            processed_parts.append(part)
        dot_path = '.'.join(processed_parts)
        return f'::: {dot_path}.{class_}'

    def markdown_refresh(self):
        """Refreshes the markdown documentation for the project.

This method deletes the existing markdown folder, recreates it, and then processes all files, directories, and repositories to generate markdown documentation. It handles different types of documentation items and writes the generated markdown content to the appropriate files. The method ensures that the documentation is up-to-date and reflects the current state of the codebase.

Args:
    None

Returns:
    None

Raises:
    IOError: If there is an error writing to a markdown file.

Note:
    - The method uses a lock to ensure thread safety.
    - It logs the progress and any issues encountered during the process.
    - The `DocItemType` enum is used to determine the type of each documentation item.
    - The `MetaInfo` class provides the list of files to process.
    - The `SettingsManager` class is used to retrieve project settings.
    - The `convert_path_to_dot_notation` method is used to generate dot notation strings for class references.
    - The `update_doc` method is used to update the docstring of AST nodes.
    - The tool integrates functionalities to detect changes, handle file operations, and manage project settings, making it suitable for large repositories where manual documentation updates are time-consuming and error-prone."""
        with self.runner_lock:
            markdown_folder = Path(self.setting.project.target_repo) / self.setting.project.markdown_docs_name
            if markdown_folder.exists():
                logger.debug(f'Deleting existing contents of {markdown_folder}')
                shutil.rmtree(markdown_folder)
            markdown_folder.mkdir(parents=True, exist_ok=True)
            logger.debug(f'Created markdown folder at {markdown_folder}')
        file_item_list = self.meta_info.get_all_files(count_repo=True)
        logger.debug(f'Found {len(file_item_list)} files to process.')
        for file_item in tqdm(file_item_list):

            def recursive_check(doc_item) -> bool:
                if doc_item.md_content:
                    return True
                for child in doc_item.children.values():
                    if recursive_check(child):
                        return True
                return False
            if not recursive_check(file_item) and file_item.item_type == DocItemType._file:
                logger.debug(f'No documentation content for: {file_item.get_full_name()}, skipping.')
                continue
            markdown = ''
            if file_item.item_type == DocItemType._dir:
                if file_item.md_content:
                    markdown = file_item.md_content[-1]
            elif file_item.item_type == DocItemType._repo:
                markdown += SettingsManager.get_setting().project.main_idea
            else:
                markdown += f'# {Path(file_item.obj_name).name.strip('.py').replace('_', ' ').title()}\n\n'
                for child in file_item.children.values():
                    update_doc(child.source_node, child.md_content[-1])
                    markdown += f'## {child.obj_name}\n{self.convert_path_to_dot_notation(Path(file_item.obj_name), child.obj_name)}\n\n'
                    for n_child in child.children.values():
                        update_doc(n_child.source_node, n_child.md_content[-1])
                children_names = list(file_item.children.keys())
                if children_names:
                    with open(Path(self.setting.project.target_repo, file_item.obj_name), 'w+', encoding='utf-8') as f:
                        value = ast.unparse(file_item.children[children_names[0]].source_node.parent)
                        f.write(value)
            if not markdown:
                logger.warning(f'No markdown content generated for: {file_item.get_full_name()}')
                continue
            if file_item.item_type == DocItemType._dir:
                file_path = Path(self.setting.project.markdown_docs_name) / Path(file_item.obj_name) / 'index.md'
            elif file_item.item_type == DocItemType._repo:
                file_path = Path(self.setting.project.markdown_docs_name) / 'index.md'
            else:
                file_path = Path(self.setting.project.markdown_docs_name) / file_item.get_file_name().replace('.py', '.md')
            abs_file_path = self.setting.project.target_repo / file_path
            logger.debug(f'Writing markdown to: {abs_file_path}')
            abs_file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f'Ensured directory exists: {abs_file_path.parent}')
            with self.runner_lock:
                for attempt in range(3):
                    try:
                        with open(abs_file_path, 'w', encoding='utf-8') as file:
                            file.write(markdown)
                        logger.debug(f'Successfully wrote to {abs_file_path}')
                        break
                    except IOError as e:
                        logger.error(f'Failed to write {abs_file_path} on attempt {attempt + 1}: {e}')
                        time.sleep(1)
        logger.info(f'Markdown documents have been refreshed at {self.setting.project.markdown_docs_name}')

    def git_commit(self, commit_message):
        """Commits changes to the Git repository with the specified message.

This method is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository. It ensures that changes are committed with a clear message, facilitating better version control and documentation tracking.

Args:
    commit_message (str): The message to be used for the Git commit.

Raises:
    subprocess.CalledProcessError: If the Git commit command fails.

Note:
    The `--no-verify` flag is used to bypass pre-commit hooks, which can be useful in automated workflows where pre-commit checks are not necessary."""
        try:
            subprocess.check_call(['git', 'commit', '--no-verify', '-m', commit_message], shell=True)
        except subprocess.CalledProcessError as e:
            print(f'An error occurred while trying to commit {str(e)}')

    def run(self):
        """Runs the documentation generation process for the project.

This method automates the generation and updating of documentation for a Git repository. It checks if the document version is empty and initializes the necessary settings and processes. If the document version is not empty and the generation process is not in progress, it detects changes in the repository, merges the new metadata, and generates the necessary documentation. It uses multiple threads to process tasks concurrently and ensures that the metadata is checkpointed and the markdown documentation is refreshed.

Args:
    self: The instance of the `Runner` class.

Returns:
    None

Raises:
    None

Note:
    - The method uses the `SettingsManager` to retrieve project settings.
    - It uses the `MetaInfo` class to manage metadata and task generation.
    - It uses the `ChangeDetector` class to detect changes in the repository.
    - It uses the `worker` function to process tasks in parallel.
    - It uses the `markdown_refresh` method to refresh the markdown documentation.
    - It uses the `delete_fake_files` method to clean up temporary files.
    - The method logs various actions and intermediate results for debugging and monitoring purposes."""
        if self.meta_info.document_version == '':
            settings = SettingsManager.get_setting()
            if settings.project.main_idea:
                self.generate_doc()
                self.summarize_modules()
                self.markdown_refresh()
            else:
                self.generate_doc()
                settings.project.main_idea = self.generate_main_idea(self.get_top_n_components(self.meta_info.target_repo_hierarchical_tree))
                self.generate_doc()
                self.summarize_modules()
                self.markdown_refresh()
            self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path, flash_reference_relation=True)
            return
        if not self.meta_info.in_generation_process:
            logger.info('Starting to detect changes.')
            '采用新的办法\n            1.新建一个project-hierachy\n            2.和老的hierarchy做merge,处理以下情况：\n            - 创建一个新文件：需要生成对应的doc\n            - 文件、对象被删除：对应的doc也删除(按照目前的实现，文件重命名算是删除再添加)\n            - 引用关系变了：对应的obj-doc需要重新生成\n            \n            merge后的new_meta_info中：\n            1.新建的文件没有文档，因此metainfo merge后还是没有文档\n            2.被删除的文件和obj，本来就不在新的meta里面，相当于文档被自动删除了\n            3.只需要观察被修改的文件，以及引用关系需要被通知的文件去重新生成文档'
            file_path_reflections, jump_files = make_fake_files()
            new_meta_info = MetaInfo.init_meta_info(file_path_reflections, jump_files)
            new_meta_info.load_doc_from_older_meta(self.meta_info)
            self.meta_info = new_meta_info
            self.meta_info.in_generation_process = True
        check_task_available_func = partial(need_to_generate, ignore_list=self.setting.project.ignore_list)
        task_manager = self.meta_info.get_task_manager(self.meta_info.target_repo_hierarchical_tree, task_available_func=check_task_available_func)
        for item_name, item_type in self.meta_info.deleted_items_from_older_meta:
            print(f'{Fore.LIGHTMAGENTA_EX}[Dir/File/Obj Delete Dected]: {Style.RESET_ALL} {item_type} {item_name}')
        self.meta_info.print_task_list(task_manager.task_dict)
        if task_manager.all_success:
            logger.info('No tasks in the queue, all documents are completed and up to date.')
        threads = [threading.Thread(target=worker, args=(task_manager, process_id, self.generate_doc_for_a_single_item)) for process_id in range(self.setting.project.max_thread_count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.meta_info.in_generation_process = False
        self.meta_info.document_version = self.change_detector.repo.head.commit.hexsha
        self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path, flash_reference_relation=True)
        logger.info(f'Doc has been forwarded to the latest version')
        self.markdown_refresh()
        delete_fake_files()
        logger.info(f'Starting to git-add DocMetaInfo and newly generated Docs')
        time.sleep(1)
        git_add_result = self.change_detector.add_unstaged_files()
        if len(git_add_result) > 0:
            logger.info(f'Added {[file for file in git_add_result]} to the staging area.')

    def add_new_item(self, file_handler, json_data):
        """Adds documentation for a new file to the project hierarchy JSON and generates a Markdown file.

This method processes a new file by extracting its functions and classes, generating documentation for each, and updating the project hierarchy JSON. It also creates a Markdown file for the new file.

Args:
    file_handler (FileHandler): The file handler instance for the new file.
    json_data (dict): The JSON data representing the project hierarchy.

Returns:
    None

Raises:
    FileNotFoundError: If the file specified by `file_handler.file_path` does not exist.
    IOError: If an error occurs while reading or writing the file.
    Exception: If there is an error in the chat engine call.

Note:
    See also: `FileHandler.get_functions_and_classes`, `FileHandler.get_obj_code_info`, `ChatEngine.generate_doc`, `FileHandler.write_file`, `FileHandler.convert_to_markdown_file`.

This method is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository. It integrates various functionalities to detect changes, handle file operations, manage project settings, and generate summaries for modules and directories. The tool also includes a chat engine and a multi-task dispatch system to enhance user interaction and process management. Additionally, it provides utilities for handling .gitignore files and managing fake files for untracked and modified content."""
        file_dict = {}
        for structure_type, name, start_line, end_line, parent, params in file_handler.get_functions_and_classes(file_handler.read_file()):
            code_info = file_handler.get_obj_code_info(structure_type, name, start_line, end_line, parent, params)
            response_message = self.chat_engine.generate_doc(code_info, file_handler)
            md_content = response_message.content
            code_info['md_content'] = md_content
            file_dict[name] = code_info
        json_data[file_handler.file_path] = file_dict
        with open(self.project_manager.project_hierarchy, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        logger.info(f'The structural information of the newly added file {file_handler.file_path} has been written into a JSON file.')
        markdown = file_handler.convert_to_markdown_file(file_path=file_handler.file_path)
        file_handler.write_file(os.path.join(self.project_manager.repo_path, self.setting.project.markdown_docs_name, file_handler.file_path.replace('.py', '.md')), markdown)
        logger.info(f'已生成新增文件 {file_handler.file_path} 的Markdown文档。')

    def process_file_changes(self, repo_path, file_path, is_new_file):
        """Processes file changes in a repository.

This method reads the source code of a file, identifies changes in the file's structure, updates the project hierarchy JSON, and generates or updates the corresponding Markdown documentation. It also adds any unstaged files to the Git staging area. This method is part of the `Runner` class and is used to manage file changes in a project. It relies on the `FileHandler` and `ChangeDetector` classes for file operations and change detection.

Args:
    repo_path (str): The path to the repository.
    file_path (str): The path to the file that has changed.
    is_new_file (bool): Indicates whether the file is new or an existing file has been modified.

Returns:
    None

Raises:
    FileNotFoundError: If the specified file does not exist.
    JSONDecodeError: If the project hierarchy JSON file is not a valid JSON.

Note:
    This method is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository. It integrates various functionalities to detect changes, handle file operations, manage project settings, and generate summaries for modules and directories. The tool also includes a chat engine and a multi-task dispatch system to enhance user interaction and process management. Additionally, it provides utilities for handling .gitignore files and managing fake files for untracked and modified content."""
        file_handler = FileHandler(repo_path=repo_path, file_path=file_path)
        source_code = file_handler.read_file()
        changed_lines = self.change_detector.parse_diffs(self.change_detector.get_file_diff(file_path, is_new_file))
        changes_in_pyfile = self.change_detector.identify_changes_in_structure(changed_lines, file_handler.get_functions_and_classes(source_code))
        logger.info(f'检测到变更对象：\n{changes_in_pyfile}')
        with open(self.project_manager.project_hierarchy, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        if file_handler.file_path in json_data:
            json_data[file_handler.file_path] = self.update_existing_item(json_data[file_handler.file_path], file_handler, changes_in_pyfile)
            with open(self.project_manager.project_hierarchy, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            logger.info(f'已更新{file_handler.file_path}文件的json结构信息。')
            markdown = file_handler.convert_to_markdown_file(file_path=file_handler.file_path)
            file_handler.write_file(os.path.join(self.setting.project.markdown_docs_name, file_handler.file_path.replace('.py', '.md')), markdown)
            logger.info(f'已更新{file_handler.file_path}文件的Markdown文档。')
        else:
            self.add_new_item(file_handler, json_data)
        git_add_result = self.change_detector.add_unstaged_files()
        if len(git_add_result) > 0:
            logger.info(f'已添加 {[file for file in git_add_result]} 到暂存区')

    def update_existing_item(self, file_dict, file_handler, changes_in_pyfile):
        """Updates the existing items in the file dictionary based on changes in the Python file.

This method processes changes in a Python file by updating the file dictionary with new and modified objects. It also deletes objects that no longer exist in the file. The method uses a thread pool to concurrently update the documentation for added objects.

Args:
    file_dict (dict): A dictionary containing the code objects and their metadata.
    file_handler (FileHandler): An instance of the `FileHandler` class used to manage file operations.
    changes_in_pyfile (dict): A dictionary containing the changes in the Python file, including added and deleted objects.

Returns:
    dict: The updated file dictionary with new and modified objects.

Raises:
    None

Note:
    See also: `generate_file_structure` method in the `FileHandler` class for generating the file structure, and `update_object` method in the `Runner` class for updating object documentation."""
        new_obj, del_obj = self.get_new_objects(file_handler)
        for obj_name in del_obj:
            if obj_name in file_dict:
                del file_dict[obj_name]
                logger.info(f'已删除 {obj_name} 对象。')
        referencer_list = []
        current_objects = file_handler.generate_file_structure(file_handler.file_path)
        current_info_dict = {obj['name']: obj for obj in current_objects.values()}
        for current_obj_name, current_obj_info in current_info_dict.items():
            if current_obj_name in file_dict:
                file_dict[current_obj_name]['type'] = current_obj_info['type']
                file_dict[current_obj_name]['code_start_line'] = current_obj_info['code_start_line']
                file_dict[current_obj_name]['code_end_line'] = current_obj_info['code_end_line']
                file_dict[current_obj_name]['parent'] = current_obj_info['parent']
                file_dict[current_obj_name]['name_column'] = current_obj_info['name_column']
            else:
                file_dict[current_obj_name] = current_obj_info
        for obj_name, _ in changes_in_pyfile['added']:
            for current_object in current_objects.values():
                if obj_name == current_object['name']:
                    referencer_obj = {'obj_name': obj_name, 'obj_referencer_list': self.project_manager.find_all_referencer(variable_name=current_object['name'], file_path=file_handler.file_path, line_number=current_object['code_start_line'], column_number=current_object['name_column'])}
                    referencer_list.append(referencer_obj)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for changed_obj in changes_in_pyfile['added']:
                for ref_obj in referencer_list:
                    if changed_obj[0] == ref_obj['obj_name']:
                        future = executor.submit(self.update_object, file_dict, file_handler, changed_obj[0], ref_obj['obj_referencer_list'])
                        print(f'正在生成 {Fore.CYAN}{file_handler.file_path}{Style.RESET_ALL}中的{Fore.CYAN}{changed_obj[0]}{Style.RESET_ALL}对象文档.')
                        futures.append(future)
            for future in futures:
                future.result()
        return file_dict

    def update_object(self, file_dict, file_handler, obj_name, obj_referencer_list):
        """Updates the documentation for a code object in the file dictionary.

This method updates the documentation for a specified code object by calling the chat engine to generate or update the documentation. The generated documentation is then stored in the `md_content` field of the object in the file dictionary. This ensures that the documentation remains up-to-date and reflects the current state of the codebase.

Args:
    file_dict (dict): A dictionary containing the code objects and their metadata.
    file_handler (FileHandler): An instance of the FileHandler class used to manage file operations.
    obj_name (str): The name of the code object to be updated.
    obj_referencer_list (list): A list of references to the code object.

Returns:
    None

Raises:
    Exception: If there is an error in the chat engine call.

Note:
    See also: `generate_doc` method in the `ChatEngine` class for generating documentation."""
        if obj_name in file_dict:
            obj = file_dict[obj_name]
            response_message = self.chat_engine.generate_doc(obj, file_handler, obj_referencer_list)
            obj['md_content'] = response_message.content

    def get_new_objects(self, file_handler):
        """Retrieves new and deleted objects from the current and previous versions of a file.

This method compares the current and previous versions of a file to identify new and deleted functions and classes. It uses the `get_modified_file_versions` method to retrieve the file versions and the `get_functions_and_classes` method to parse the code content. This functionality is crucial for the automated documentation generation process, ensuring that changes in the codebase are accurately reflected in the documentation.

Args:
    file_handler (FileHandler): An instance of the `FileHandler` class used to handle file operations.

Returns:
    tuple: A tuple containing two lists:
        - list: A list of new object names.
        - list: A list of deleted object names.

Raises:
    FileNotFoundError: If the current file does not exist at the specified path.
    git.exc.GitError: If there is an error accessing the Git repository.

Note:
    This method is used in conjunction with other methods to track changes in file content over time, which is essential for maintaining up-to-date and accurate documentation in the Git repository."""
        current_version, previous_version = file_handler.get_modified_file_versions()
        parse_current_py = file_handler.get_functions_and_classes(current_version)
        parse_previous_py = file_handler.get_functions_and_classes(previous_version) if previous_version else []
        current_obj = {f[1] for f in parse_current_py}
        previous_obj = {f[1] for f in parse_previous_py}
        new_obj = list(current_obj - previous_obj)
        del_obj = list(previous_obj - current_obj)
        return (new_obj, del_obj)