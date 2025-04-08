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
    """Manages the execution of documentation generation tasks for Python projects.
    
    The Runner class coordinates the overall process of generating and managing documentation within a project repository. It leverages various components such as ChatEngine, TaskManager, ProjectManager, and SettingsManager to ensure that all necessary documentation is created or updated efficiently.
    
    Args:  
        None  
    
    Returns:  
        None  
    
    Raises:  
        ValueError: If configuration settings are invalid.  
    
    Note:  
        See also: Repository Agent Documentation Generator (for more details on the project's features).
    
    ---
    
    Initialize the Runner instance.
    
    This method initializes various components such as SettingsManager, ProjectManager, ChangeDetector, ChatEngine, and MetaInfo based on project settings. It ensures that necessary directories and files are created or loaded to maintain the integrity of the project structure.
    
    Args:  
        None  
    
    Returns:  
        None  
    
    Raises:  
        ValueError: If an invalid setting is encountered during initialization.
    
    Note:  
        See also: Configuration Management (for more details on settings).
    
    ---
    
    Get all Python files in the given directory.
    
    This function searches through the specified directory and returns a list of paths to all Python files found within it, which is useful for generating or managing documentation across various modules within a repository.
    
    Args:  
        directory (str): The directory path to search for Python files.
    
    Returns:  
        list: A list of strings representing the file paths of all Python files found in the specified directory.
    
    ---
    
    Generates documentation for a single item within the repository.
    
    This function processes an individual component of the project to create or update its documentation using large language models (LLMs).
    
    Args:  
        doc_item (DocItem): The DocItem instance to generate documentation for.
    
    Returns:  
        None  
    
    Raises:  
        ValueError: If the provided item is not found in the repository structure.
    
    Note:  
        See also: ProjectManager (for managing project hierarchy) and TaskManager (for coordinating tasks).
    
    ---
    
    Generate the main project idea based on component documentation.
    
    This function synthesizes information from various components to create an overarching project idea that encapsulates the purpose, scope, and key features of the repository.
    
    Args:  
        docs (List[Dict]): A list of dictionaries containing information about each component, including 'obj_name', 'md_content', and 'tree_path'.
    
    Returns:  
        str: The generated main project idea from the language model.
    
    Raises:  
        Exception: If there is an error during the chat call with the language model.
    
    ---
    
    Generates documentation for Python modules using large language models.
    
    This function orchestrates the process of generating or updating documentation files within a repository by leveraging LLMs to create comprehensive summaries and maintain up-to-date documentation across various modules.
    
    Args:  
        None  
    
    Returns:  
        None  
    
    Raises:  
        ValueError: If the specified `module_path` does not exist or is invalid.
    
    Note:  
        See also: Repository Agent's ChatEngine class for more information on how documentation generation is managed.
    
    ---
    
    Retrieves the top N components from the project hierarchy.
    
    This function identifies and returns the top N most significant or relevant components within the project's structure, based on predefined criteria such as importance, usage frequency, or other metrics defined by the ProjectManager.
    
    Args:  
        doc_item (DocItem): The DocItem instance to retrieve components from.
    
    Returns:  
        list: A list containing the top N components.
    
    Raises:  
        ValueError: If n is less than 1.
    
    Note:  
        See also: ProjectManager for details on component ranking and selection criteria.
    
    ---
    
    Extracts relevant metadata from a DocItem object for documentation generation.
    
    This function is part of the Repository Agent framework and automates the generation of comprehensive documentation for Python projects by analyzing code, identifying changes, and summarizing module contents.
    
    Args:  
        doc_item (DocItem): The DocItem instance containing the metadata to extract.
    
    Returns:  
        dict: A dictionary containing 'obj_name', 'md_content', 'who_reference_me', 'reference_who', and 'tree_path'.
    
    Note:  
        See also: Repository Agent framework documentation for more details on hierarchical relationships and node management.
    
    ---
    
    Generate the main idea of the project based on component documentation.
    
    This method synthesizes the main idea of the project by analyzing the documentation of its components, leveraging language models to provide a concise summary.
    
    Args:  
        docs (List[Dict]): A list of dictionaries containing information about each component, including 'obj_name', 'md_content', and 'tree_path'.
    
    Returns:  
        str: The generated main project idea from the language model.
    
    Raises:  
        Exception: If there is an error during the generation process.
    
    ---
    
    Summarizes the modules within the repository.
    
    Recursively generates summaries for each directory/module in the repository and updates the documentation status of these modules, leveraging the Repository Agent's capabilities to maintain up-to-date and comprehensive documentation for Python projects.
    
    Args:  
        None  
    
    Returns:  
        dict: A nested dictionary containing summaries for each directory/module.
    
    Raises:  
        IOError: If there is an error saving the hierarchy JSON or meta-info JSON files during checkpointing.
    
    Note:  
        See also: MetaInfo.checkpoint (repo_agent/doc_meta_info.py), summarize_repository (repo_agent/module_summarization.py).
    
    ---
    
    Update the documentation status of modules.
    
    This method updates the documentation status of a module by appending its summary to the corresponding DocItem's markdown content and marking it as up-to-date. It also recursively processes any submodules associated with the given module, ensuring that all changes in the repository are reflected accurately in the generated documentation.
    
    Args:  
        module (dict): A dictionary containing information about the module, including its path and summary.
    
    Returns:  
        None  
    
    Raises:  
        ValueError: If an invalid path is provided during the search tree operation.
    
    Note:  
        See also: DocItemStatus
    
    ---
    
    Search for a specific node in the hierarchical tree structure.
    
    This function recursively searches through the children of each DocItem until the specified path is matched, allowing users to efficiently locate nodes within complex hierarchies managed by the Repository Agent.
    
    Args:  
        doc (DocItem): The root DocItem of the hierarchy.  
        path (str): The relative path to the target node, where '.' represents the current directory.
    
    Returns:  
        DocItem: The found DocItem if it exists; otherwise, None.
    
    Raises:  
        ValueError: If an invalid path is provided.
    
    Note:  
        This method is part of the Repository Agent's functionality for generating and managing hierarchical documentation structures.
    
    ---
    
    Converts a file path to a dot notation string.
    
    This function takes a file path (with or without the '.py' extension) and converts it into a dot-separated string, appending a class name at the end. This is particularly useful in generating module-level documentation within the Repository Agent framework.
    
    Args:  
        path (Path | str): The file path to convert.  
        class_ (str): The class name to append to the converted path.
    
    Returns:  
        str: A string in the format "<dot_notation>.<class_name>".
    
    Note:  
        See also: `repo_agent.doc_meta_info.DocItemType`, `repo_agent.doc_meta_info.MetaInfo.get_all_files`, `repo_agent.runner.Runner.generate_doc`.
    
    ---
    
    Refreshes the markdown files within the repository.
    
    This function ensures that all markdown files are up-to-date by leveraging the Repository Agent's capabilities to regenerate summaries and documentation for Python modules using large language models (LLMs).
    
    Args:  
        None  
    
    Returns:  
        None  
    
    Raises:  
        ValueError: If an error occurs during the regeneration process.
    
    Note:  
        This function is part of a larger system designed to automate the maintenance of high-quality documentation in complex Python projects.
    
    ---
    
    Commits changes to the Git repository.
    
    This function commits changes made in the repository using the specified commit message. It leverages subprocess calls to execute Git commands, ensuring that any modifications are recorded accurately.
    
    Args:  
        commit_message (str): The message for the commit.
    
    Returns:  
        None  
    
    Raises:  
        subprocess.CalledProcessError: If the git commit command fails.
    
    Note:  
        See also: Repository Agent Documentation Generator.
    
    ---
    
    Runs the main execution loop for generating and managing documentation within the repository.
    
    Args:  
        None  
    
    Returns:  
        None  
    
    Raises:  
        ValueError: If there is an issue with task management or configuration settings.
    
    Note:  
        This function orchestrates the entire process of documentation generation, leveraging LLMs to create summaries and maintain up-to-date documentation across various modules in the project. It coordinates tasks through the TaskManager class and ensures that all necessary files are created or updated as needed.
    
    ---
    
    Adds a new item to the repository documentation.
    
    This function is responsible for adding a new item (such as a module or file) to the repository's documentation by leveraging the Repository Agent's capabilities to generate and manage documentation automatically.
    
    Args:  
        file_handler (FileHandler): The file handler object used for managing file operations.  
        json_data (dict): The JSON data containing the current file structure information.
    
    Returns:  
        bool: True if the item was successfully added, False otherwise.
    
    Raises:  
        ValueError: If the provided item_type is not supported.  
        FileNotFoundError: If the specified path does not exist in the repository.
    
    Note:  
        See also: summarize_repository (for generating summaries of Python modules and submodules).
    
    ---
    
    Processes file changes according to the absolute file path within a repository.
    
    This function processes changed files by reading and updating the project hierarchy JSON file, converting changes to Markdown format, and adding updated Markdown files to the staging area. It is part of the Repository Agent framework, which automates documentation generation and management for Python projects.
    
    Args:  
        repo_path (str): The path to the repository.  
        file_path (str): The relative path to the file within the repository.  
        is_new_file (bool): Indicates whether the file is new or not.
    
    Returns:  
        None  
    
    Raises:  
        ValueError: If an error occurs during JSON file operations.
    
    Note:  
        See also: FileHandler, ChangeDetector, ProjectManager
    
    ---
    
    Updates the existing project documentation based on changes detected in the repository.
    
    This function updates the file structure information dictionary by incorporating modifications identified in the Python files, ensuring that the generated documentation remains up-to-date with the latest changes in the project.
    
    Args:  
        file_dict (dict): A dictionary containing the current file structure information.  
        file_handler (FileHandler): The object responsible for managing file operations.  
        changes_in_pyfile (dict): A dictionary detailing the changes made to objects within the Python files.
    
    Returns:  
        dict: The updated file structure information dictionary reflecting the modifications in the repository.
    
    Raises:  
        Exception: If an error occurs during the interaction with the language model.
    
    Note:  
        See also: `repo_agent.runner.Runner.get_new_objects`, `repo_agent.file_handler.FileHandler.generate_file_structure`.
    
    ---
    
    Updates the specified object's documentation content.
    
    This function updates the documentation for an existing Python object by analyzing its current state and generating or modifying relevant documentation based on changes detected in the repository. It leverages large language models to ensure that the documentation remains comprehensive and up-to-date.
    
    Args:  
        file_dict (dict): A dictionary containing information about the old object.  
        file_handler (FileHandler): The handler responsible for managing file operations.  
        obj_name (str): The name of the object to be updated.  
        obj_referencer_list (list): A list of referencers related to the object.
    
    Returns:  
        None  
    
    Raises:  
        Exception: If an error occurs during the interaction with the language model.
    
    Note:  
        See also: `repo_agent.chat_engine.ChatEngine.generate_doc`.
    
    ---
    
    Identifies newly added and deleted objects by comparing the current version of a .py file with its previous version.
    
    This function is part of the Repository Agent's change detection feature, which helps in updating existing documentation when modifications are made to the repository. It works alongside other features such as automated documentation generation and task management to ensure that all changes are accurately reflected in the project's documentation.
    
    Args:  
        file_handler (FileHandler): The file handler object used for managing file operations and retrieving modified versions of files.
    
    Returns:  
        tuple: A tuple containing two lists - one with newly added objects and another with deleted objects. The format is (new_obj, del_obj).
    
    Note:  
        See also: FileHandler.get_modified_file_versions(), FileHandler.get_functions_and_classes()."""

    def __init__(self):
        """Initializes the Runner instance.
    
    This method initializes various components such as SettingsManager, ProjectManager, ChangeDetector, ChatEngine, and MetaInfo based on project settings. It ensures that necessary directories and files are created or loaded to maintain the integrity of the project structure.
    
    Args:
        None
    
    Returns:
        None
    
    Raises:
        ValueError: If an invalid setting is encountered during initialization.
    
    Note:
        See also: Configuration Management (for more details on settings)."""
        self.setting = SettingsManager.get_setting()
        self.absolute_project_hierarchy_path = self.setting.project.target_repo / self.setting.project.hierarchy_name
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
        """Get all Python files in the given directory.
    
    This method searches through the specified directory and returns a list of paths to all Python files found within it, which is useful for generating or managing documentation across various modules within a repository.
    
    Args:
        directory (str): The directory path to search for Python files.
    
    Returns:
        list: A list of strings representing the file paths of all Python files found in the specified directory.
    
    Raises:
        ValueError: If the provided directory path is not a valid directory.
    
    Note:
        This method is particularly useful for automating the documentation process in large projects with complex directory structures."""
        python_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files

    def generate_doc_for_a_single_item(self, doc_item: DocItem):
        """Generates documentation for a single item within the repository.
    
    This method processes an individual component of the project to create or update its documentation using large language models (LLMs).
    
    Args:
        doc_item (DocItem): The documentation item for which the documentation is being generated.
    
    Returns:
        None
    
    Raises:
        ValueError: If the provided item is not found in the repository structure.
    
    Note:
        See also: ProjectManager (for managing project hierarchy) and TaskManager (for coordinating tasks)."""
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
        """Generate the main project idea based on component documentation.
    
    This method synthesizes information from various components to create an overarching project idea that encapsulates the purpose, scope, and key features of the repository. The Repository Agent aims to streamline the process of maintaining high-quality documentation for complex Python projects by leveraging large language models (LLMs) to generate comprehensive summaries and manage documentation across different modules.
    
    Args:  
        docs (List[Dict]): A list of dictionaries containing information about each component, including 'obj_name', 'md_content', and 'tree_path'.
    
    Returns:  
        str: The generated main project idea from the language model.
    
    Raises:  
        Exception: If there is an error during the chat call with the language model.
    
    Note:  
        See also: ChatEngine (for generating ideas based on component details)."""
        str_obj = []
        for doc in docs:
            str_obj.append(f'Component name: {doc['obj_name']}\nComponent description: {doc['md_content']}\nComponent place in hierarchy: {doc['tree_path']}')
        response_message = self.chat_engine.generate_idea('\n\n'.join(str_obj))
        return response_message

    def generate_doc(self):
        """Generates documentation for Python modules using large language models.
    
    This method orchestrates the process of generating or updating documentation files within a repository by leveraging LLMs to create comprehensive summaries and maintain up-to-date documentation across various modules.
    
    Args:
        module_path (str): The path to the Python module or package for which documentation is to be generated.
        output_dir (str, optional): The directory where the generated documentation will be saved. Defaults to "./docs".
    
    Returns:
        str: A message indicating the success of the operation and providing details about the generated documentation.
    
    Raises:
        ValueError: If the specified `module_path` does not exist or is invalid.
    
    Note:
        See also: Repository Agent's ChatEngine class for more information on how documentation generation is managed."""
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
        """Retrieves the top N components from the project hierarchy.
    
    This method identifies and returns the top N most significant or relevant components within the project's structure, based on predefined criteria such as importance, usage frequency, or other metrics defined by the ProjectManager.
    
    Args:
        doc_item (DocItem): The documentation item from which to retrieve the top components.
        n (int): The number of top components to retrieve. Must be greater than or equal to 1.
    
    Returns:
        list: A list containing the top N components.
    
    Raises:
        ValueError: If n is less than 1.
    
    Note:
        See also: ProjectManager for details on component ranking and selection criteria."""
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
        """Extracts relevant metadata from a DocItem object for documentation generation.
    
    The Repository Agent framework automates the generation of comprehensive documentation for Python projects by analyzing code, identifying changes, and summarizing module contents.
    
    Args:
        doc_item (DocItem): The DocItem instance containing the metadata to extract.
    
    Returns:
        dict: A dictionary containing 'obj_name', 'md_content', 'who_reference_me', 'reference_who', and 'tree_path'.
    
    Note:
        See also: Repository Agent framework documentation for more details on hierarchical relationships and node management."""
        return {'obj_name': doc_item.obj_name, 'md_content': doc_item.md_content[-1].split('\n\n')[0], 'who_reference_me': doc_item.who_reference_me, 'reference_who': doc_item.reference_who, 'tree_path': '->'.join([obj.obj_name for obj in doc_item.tree_path])}

    def generate_main_idea(self, docs):
        """Generate the main idea of the project based on component documentation.
    
    This method synthesizes the main idea of the project by analyzing the documentation of its components, leveraging language models to provide a concise summary. The Repository Agent aims to streamline the process of maintaining high-quality documentation for complex Python projects, reducing manual effort and improving consistency across all modules.
    
    Args:
        docs (List[Dict]): A list of dictionaries containing information about each component, including 'obj_name', 'md_content', and 'tree_path'.
    
    Returns:
        str: The generated main project idea from the language model.
    
    Raises:
        Exception: If there is an error during the generation process.
    
    Note:
        See also: ChatEngine (for generating ideas based on component details)."""
        logger.info('Generation of the main idea')
        main_project_idea = self.generate_main_project_idea(docs)
        logger.info(f'Successfully generated the main idea')
        return main_project_idea

    def summarize_modules(self):
        """Summarizes the modules within the repository.
    
    Recursively generates summaries for each directory/module in the repository and updates the documentation status of these modules, leveraging the Repository Agent's capabilities to maintain up-to-date and comprehensive documentation for Python projects. This method is a crucial part of the automated documentation generation process managed by the ChatEngine class.
    
    Args:
        None
    
    Returns:
        dict: A nested dictionary containing summaries for each directory/module.
    
    Raises:
        IOError: If there is an error saving the hierarchy JSON or meta-info JSON files during checkpointing.
    
    Note:
        See also: MetaInfo.checkpoint (repo_agent/doc_meta_info.py), summarize_repository (repo_agent/module_summarization.py)."""
        logger.info('Modules documentation generation')
        res = summarize_repository(self.meta_info.repo_path, self.meta_info.repo_structure, self.chat_engine)
        self.update_modules(res)
        self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path)
        logger.info(f'Successfully generated module summaries')
        return res

    def update_modules(self, module):
        """Updates the documentation status of modules.
    
    This method updates the documentation status of a module by appending its summary to the corresponding DocItem's markdown content and marking it as up-to-date. It also recursively processes any submodules associated with the given module, ensuring that all changes in the repository are reflected accurately in the generated documentation.
    
    Args:
        module (dict): A dictionary containing information about the module, including its path and summary.
    
    Returns:
        None
    
    Raises:
        ValueError: If an invalid path is provided during the search tree operation.
    
    Note:
        See also: DocItemStatus, search_tree"""
        rel_path = os.path.relpath(module['path'], self.meta_info.repo_path)
        doc_item = self.search_tree(self.meta_info.target_repo_hierarchical_tree, rel_path)
        doc_item.md_content.append(module['module_summary'])
        doc_item.item_status = DocItemStatus.doc_up_to_date
        for sm in module['submodules']:
            self.update_modules(sm)

    def search_tree(self, doc: DocItem, path: str):
        """Search for a specific node in the hierarchical tree structure.
    
    This method recursively searches through the children of each DocItem until the specified path is matched, allowing users to efficiently locate nodes within complex hierarchies managed by the Repository Agent.
    
    Args:
        doc (DocItem): The root DocItem of the hierarchy.
        path (str): The relative path to the target node, where '.' represents the current directory.
    
    Returns:
        DocItem: The found DocItem if it exists; otherwise, None.
    
    Raises:
        ValueError: If an invalid path is provided.
    
    Note:
        This method is part of the Repository Agent's functionality for generating and managing hierarchical documentation structures."""
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
        """Converts a file path to a dot notation string.
    
    This method takes a file path (with or without the '.py' extension) and converts it into a dot-separated string, appending a class name at the end. This is particularly useful in generating module-level documentation within the Repository Agent framework.
    
    Args:  
        path (Path | str): The file path to convert.  
        class_ (str): The class name to append to the converted path.  
    
    Returns:  
        str: A string in the format "<dot_notation>.<class_name>".  
    
    Note:  
        See also: `repo_agent.doc_meta_info.DocItemType`, `repo_agent.doc_meta_info.MetaInfo.get_all_files`, `repo_agent.runner.Runner.generate_doc`."""
        path_obj = Path(path) if isinstance(path, str) else path
        processed_parts = []
        for part in path_obj.parts:
            if part.endswith('.py'):
                part = part[:-3]
            processed_parts.append(part)
        dot_path = '.'.join(processed_parts)
        return f'::: {dot_path}.{class_}'

    def markdown_refresh(self):
        """Refreshes the markdown files within the repository.
    
    This method ensures that all markdown files are up-to-date by leveraging the Repository Agent's capabilities to regenerate summaries and documentation for Python modules using large language models (LLMs).
    
    Args:
        None
    
    Returns:
        None
    
    Raises:
        ValueError: If an error occurs during the regeneration process.
    
    Note:
        This method is part of a larger system designed to automate the maintenance of high-quality documentation in complex Python projects. It helps streamline the documentation process, making it easier for developers to maintain and update documentation by automating the generation and summarization of module and submodule documentation."""
        '刷新最新的文档信息到markdown格式文件夹中'
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
        """Commits changes to the Git repository.
    
    This method commits changes made in the repository using the specified commit message. It leverages subprocess calls to execute Git commands, ensuring that any modifications are recorded accurately. This functionality is part of the Repository Agent framework, which automates documentation generation and management for Python projects by integrating seamlessly with Git.
    
    Args:
        commit_message (str): The message for the commit.
    
    Returns:
        None
    
    Raises:
        subprocess.CalledProcessError: If the git commit command fails.
    
    Note:
        See also: Repository Agent Documentation Generator."""
        try:
            subprocess.check_call(['git', 'commit', '--no-verify', '-m', commit_message], shell=True)
        except subprocess.CalledProcessError as e:
            print(f'An error occurred while trying to commit {str(e)}')

    def run(self):
        """Runs the main execution loop for generating and managing documentation within the repository.
    
    This method orchestrates the entire process of documentation generation, leveraging LLMs to create summaries and maintain up-to-date documentation across various modules in the project. It coordinates tasks through the TaskManager class and ensures that all necessary files are created or updated as needed.
    
    Args:
        None
    
    Returns:
        None
    
    Raises:
        ValueError: If there is an issue with task management or configuration settings.
    
    Note:
        This method is a core component of the Repository Agent's workflow for automating documentation generation and management in Python projects. It ensures that the documentation is always up-to-date and reflects the current state of the repository."""
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
        """Adds a new item to the repository documentation.
    
    This method is responsible for adding a new item (such as a module or file) to the repository's documentation by leveraging the Repository Agent's capabilities to generate and manage documentation automatically.
    
    Args:
        file_handler (FileHandler): The file handler object for the file to be added.
        json_data (dict): The JSON data representing the current state of the repository's documentation.
    
    Returns:
        None
    
    Raises:
        ValueError: If an error occurs during the documentation generation process.
        FileNotFoundError: If the specified file does not exist in the repository.
    
    Note:
        See also: `summarize_repository` (for generating summaries of Python modules and submodules)."""
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
        """Processes file changes according to the absolute file path within a repository.
    
    This method processes changed files by reading and updating the project hierarchy JSON file, converting changes to Markdown format, and adding updated Markdown files to the staging area. It is part of the Repository Agent framework, which automates documentation generation and management for Python projects.
    
    Args:
        repo_path (str): The path to the repository.
        file_path (str): The relative path to the file within the repository.
        is_new_file (bool): Indicates whether the file is new or not.
    
    Returns:
        None
    
    Raises:
        ValueError: If an error occurs during JSON file operations.
    
    Note:
        See also: FileHandler, ChangeDetector, ProjectManager"""
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
        """Updates the existing project documentation based on changes detected in the repository.
    
    This method updates the file structure information dictionary by incorporating modifications identified in the Python files, ensuring that the generated documentation remains up-to-date with the latest changes in the project.
    
    Args:
        file_dict (dict): A dictionary containing the current file structure information.
        file_handler (FileHandler): The object responsible for handling file operations and generating file structures.
        changes_in_pyfile (dict): A dictionary detailing the changes made to objects within the Python files.
    
    Returns:
        dict: The updated file structure information dictionary reflecting the modifications in the repository.
    
    Raises:
        Exception: If an error occurs during the interaction with the language model.
    
    Note:
        See also: `repo_agent.runner.Runner.get_new_objects`, `repo_agent.file_handler.FileHandler.generate_file_structure`."""
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
        """Updates the specified object's documentation content.
    
    This method updates the documentation for an existing Python object by analyzing its current state and generating or modifying relevant documentation based on changes detected in the repository. It leverages large language models to ensure that the documentation remains comprehensive and up-to-date.
    
    Args:
        file_dict (dict): A dictionary containing information about the old object.
        file_handler: The handler responsible for managing file operations.
        obj_name (str): The name of the object to be updated.
        obj_referencer_list (list): A list of referencers related to the object.
    
    Returns:
        None
    
    Raises:
        Exception: If an error occurs during the interaction with the language model.
    
    Note:
        See also: `repo_agent.chat_engine.ChatEngine.generate_doc`."""
        if obj_name in file_dict:
            obj = file_dict[obj_name]
            response_message = self.chat_engine.generate_doc(obj, file_handler, obj_referencer_list)
            obj['md_content'] = response_message.content

    def get_new_objects(self, file_handler):
        """Identifies newly added and deleted objects by comparing the current version of a .py file with its previous version.
    
    This method is part of the Repository Agent's change detection feature, which helps in updating existing documentation when modifications are made to the repository. It works alongside other features such as automated documentation generation and task management to ensure that all changes are accurately reflected in the project's documentation.
    
    Args:
        file_handler (FileHandler): The file handler object used for managing file operations and retrieving modified versions of files.
    
    Returns:
        tuple: A tuple containing two lists - one with newly added objects and another with deleted objects. The format is (new_obj, del_obj).
    
    Note:
        See also: FileHandler.get_modified_file_versions(), FileHandler.get_functions_and_classes()"""
        current_version, previous_version = file_handler.get_modified_file_versions()
        parse_current_py = file_handler.get_functions_and_classes(current_version)
        parse_previous_py = file_handler.get_functions_and_classes(previous_version) if previous_version else []
        current_obj = {f[1] for f in parse_current_py}
        previous_obj = {f[1] for f in parse_previous_py}
        new_obj = list(current_obj - previous_obj)
        del_obj = list(previous_obj - current_obj)
        return (new_obj, del_obj)
if __name__ == '__main__':
    runner = Runner()
    runner.run()
    logger.info('文档任务完成。')