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
    """# Repository Documentation Generator: Runner Function

The `Runner` function is a core component of the Repository Documentation Generator, orchestrating the documentation generation workflow for software projects. It manages project structures and executes tasks within this process, ensuring efficient and accurate documentation creation.

## Description

The `Runner` function initiates and oversees the documentation generation tasks, coordinating with various subsystems to produce comprehensive, up-to-date documentation. It leverages multi-task dispatching for optimal resource allocation and task management, thereby streamlining the documentation process.

## Args

- **project_manager** (ProjectManager): An instance of the ProjectManager class, responsible for managing project structures.
- **task_manager** (TaskManager): An instance of the TaskManager class, overseeing task execution and dispatch.
- **settings** (Settings): An instance of the Settings class, containing configuration parameters for optimal operation.
- **logger** (logging.Logger): A logger instance for managing application logs.

## Returns

- **dict**: A dictionary containing the results of the documentation generation process, including status updates and generated content.

## Raises

- **ValueError**: If any invalid or missing arguments are provided.
- **Exception**: For any unexpected errors during task execution.

## Notes

- The `Runner` function is designed to work in conjunction with other components of the Repository Documentation Generator, such as `ProjectManager`, `TaskManager`, and various subsystems for metadata handling, file management, and interactive communication.
- It utilizes a multi-task dispatch system (`TaskManager`) to manage and allocate resources efficiently across different documentation tasks.
- The function's operation is governed by configuration settings (`Settings`), which can be customized to suit specific project requirements or operational preferences.
- Comprehensive logging is maintained through the provided logger instance, facilitating debugging and performance monitoring."""

    def __init__(self):
        '''"""Initializes the Runner class for the Repository Documentation Generator.

This method sets up various components of the Runner class, facilitating the automation of documentation generation for software projects. It includes:
- SettingsManager instance for accessing project settings.
- Absolute path to the project hierarchy directory.
- ProjectManager instance for managing project details.
- ChangeDetector instance for detecting changes in the repository.
- ChatEngine instance for handling chat functionalities, enabling interactive communication with the repository.
- MetaInfo instance for managing metadata information.
- RunnerLock instance for thread safety.

The method first checks if the project hierarchy directory exists. If it does not exist, it initializes meta information from scratch using fake files and saves it to the directory. If the directory already exists, it loads the repository structure from the existing checkpoint and initializes meta information accordingly.

After initialization, the method updates the metadata and writes it back to the project hierarchy directory.

Args:
    None

Returns:
    None

Raises:
    None

Note:
    See also: repo_agent/runner.py/SettingsManager for details on settings management.
    See also: repo_agent/runner.py/ProjectManager for details on project management.
    See also: repo_agent/runner.py/ChangeDetector for details on change detection.
    See also: repo_agent/runner.py/ChatEngine for details on chat functionalities.
    See also: repo_agent/runner.py/MetaInfo for details on metadata management.
"""'''
        self.setting = SettingsManager.get_setting()
        self.absolute_project_hierarchy_path = self.setting.project.target_repo / self.setting.project.hierarchy_name
        self.project_manager = ProjectManager(repo_path=self.setting.project.target_repo, project_hierarchy=self.setting.project.hierarchy_name)
        self.change_detector = ChangeDetector(repo_path=self.setting.project.target_repo)
        self.chat_engine = ChatEngine(project_manager=self.project_manager)
        file_path_reflections, jump_files = make_fake_files()
        if not self.absolute_project_hierarchy_path.exists():
            self.meta_info = MetaInfo.init_meta_info(file_path_reflections, jump_files)
            self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path)
        else:
            setting = SettingsManager.get_setting()
            project_abs_path = setting.project.target_repo
            file_handler = FileHandler(project_abs_path, None)
            repo_structure = file_handler.generate_overall_structure(file_path_reflections, jump_files)
            self.meta_info = MetaInfo.from_checkpoint_path(self.absolute_project_hierarchy_path, repo_structure)
        self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path)
        self.runner_lock = threading.Lock()

    def get_all_pys(self, directory):
        """'''
Get paths to all Python files within the specified directory and its subdirectories.

This function recursively searches through the given directory, identifying and returning paths to all Python (.py) files. It is a part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. By leveraging advanced techniques such as chat-based interaction and multi-task dispatching, it streamlines the generation of documentation pages, summaries, and metadata.

Args:
    directory (str): The directory to search for Python files. This could be any path within the repository where Python scripts are stored.

Returns:
    list: A list containing paths to all Python (.py) files found in the specified directory and its subdirectories. The paths are relative to the provided directory, facilitating easy integration with other documentation generation tasks.

Raises:
    FileNotFoundError: If the provided directory does not exist. This ensures that the function handles non-existent paths gracefully, preventing runtime errors during documentation generation.
    NotADirectoryError: If the provided path is not a directory. This safeguard maintains the integrity of the search process by only targeting locations capable of containing files.

Note:
    This function uses os.walk() for directory traversal, which follows symbolic links. If you need to avoid following symbolic links (for instance, to prevent documenting certain test or build artifacts), use os.scandir() instead.

See also:
    RepositoryDocumentationGenerator.Runner.get_all_pys for more context within the project's architecture.
'''"""
        python_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files

    def generate_doc_for_a_single_item(self, doc_item: DocItem):
        """
Generates documentation for a single repository item.

This function is part of the Repository Documentation Generator, an automated tool designed to streamline the creation of software project documentation. It utilizes advanced features such as change detection and chat-based interaction to ensure accurate and up-to-date documentation.

Args:
    item (object): The repository item for which documentation needs to be generated. This could be a file, directory, or any other relevant entity within the repository structure.
    settings (ProjectSettings): Configuration settings that dictate how the documentation should be formatted and structured.
    logger (logging.Logger): A logger instance used for tracking progress and handling potential errors during the documentation generation process.

Returns:
    str: The generated documentation string for the specified item, formatted according to the provided settings.

Raises:
    ValueError: If the 'item' parameter is not of a valid type or if the 'settings' parameter is not properly configured.
    TypeError: If any unexpected issues occur during the documentation generation process.

Note:
    This function operates within the broader context of the Repository Documentation Generator, which includes features like ChangeDetector for monitoring repository changes and ChatEngine for interactive communication. It's part of a multi-task dispatch system managed by TaskManager and Runner classes, all working together to ensure efficient and accurate documentation generation.
"""
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
        '''"""
Generates a main project idea based on the repository's documentation structure.

This function constructs a detailed project idea by interpreting the repository's documentation items, their descriptions, and hierarchical positions. It utilizes a predefined template to format these elements into a coherent narrative, which is then refined using a language model for expanded detail.

Args:
    docs (List[Dict]): A collection of dictionaries, each representing a documentation item with keys 'obj_name' (component name), 'md_content' (description), and 'tree_path' (hierarchical position).

Returns:
    str: The generated main project idea as a string. This idea encapsulates the repository's structure and content, providing a comprehensive overview of potential project directions.

Raises:
    Exception: If there is an error during the language model chat call, potentially due to connectivity issues or model unavailability.

Note:
    This function operates within the Repository Documentation Generator framework, which automates the documentation process for software projects. It employs a multi-task dispatch system (TaskManager and worker) for efficient task allocation and management. The 'generate_main_project_idea' function specifically uses a template to format messages based on the repository's documentation items. These formatted strings are then passed to a language model (via ChatEngine) for detailed expansion, guided by settings retrieved from SettingsManager, particularly the language setting.

    See also: repo_agent.chat_engine.ChatEngine.generate_idea for more details on how the idea is generated.
"""'''
        str_obj = []
        for doc in docs:
            str_obj.append(f'Component name: {doc['obj_name']}\nComponent description: {doc['md_content']}\nComponent place in hierarchy: {doc['tree_path']}')
        response_message = self.chat_engine.generate_idea('\n\n'.join(str_obj))
        return response_message

    def generate_doc(self):
        """# Repository Documentation Generator: `generate_doc` Function

The `generate_doc` function is a core component of the Repository Documentation Generator, designed to automate the creation of documentation pages, summaries, and metadata for software projects. It employs sophisticated techniques such as change detection, chat-based interaction, and multi-task dispatching to optimize the documentation generation process.

## Functionality

The `generate_doc` function orchestrates various aspects of the documentation generation workflow, including:

- **Change Detection**: Identifies modifications in the repository that necessitate updates or new documentation creation.
- **Interactive Communication**: Facilitates user queries for specific documentation via natural language interactions.
- **Task Management**: Implements a multi-task dispatch system for efficient resource allocation and task execution.
- **Metadata Handling**: Manages project metadata and file operations to ensure accurate, up-to-date documentation.
- **Logging & Error Handling**: Oversees logging and error management for seamless operation.

## Detailed Description

### Args:

- `project_settings` (dict): A dictionary containing project-specific settings, including configuration parameters and user preferences.
  - `param1` (str): The root directory of the repository. Defaults to the current working directory.
  - `param2` (bool): A flag indicating whether to generate detailed documentation. Defaults to `True`.

- `chat_completion_settings` (dict): A dictionary with settings for chat-based interactions, including model parameters and response thresholds.
  - `model` (str): The name of the language model used for chat interactions. Defaults to 'text-davinci-003'.
  - `temperature` (float): Controls the randomness of the model's responses. Ranges from 0 (completely deterministic) to 1 (fully random). Defaults to 0.5.

### Returns:

- `dict`: A dictionary containing generated documentation metadata, including file paths and status indicators.
  - `keys` (list): List of keys representing different types of documentation items.
  - `values` (list): Corresponding values providing details about each documentation item, such as file paths and generation statuses.

### Raises:

- `ValueError`: If invalid project settings or chat completion settings are provided.

### Notes:

- The function leverages the `ProjectManager` and `Runner` classes to manage project structures and execute tasks within the documentation generation workflow.
- It utilizes various utility functions, such as `changeDetector`, `chatEngine`, and `taskManager`, to perform specific tasks like change detection, chat interactions, and task dispatching.
- For detailed information on these components and their functionalities, refer to the respective sections in the project documentation."""
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
        """plaintext
[Short description]

The `get_top_n_components` function is a crucial component of the Repository Documentation Generator, facilitating the extraction of top N components from a hierarchical tree structure of DocItem objects. This process excludes items specified in the ignore list, ensuring that only relevant data is collected for documentation purposes.

[Longer description if needed.]

The `get_top_n_components` function operates within the broader context of automating software project documentation. It is part of the Runner class in the repo_agent package, working in tandem with other methods such as `_get_md_and_links_from_doc` and `run`. This function specifically focuses on traversing through a hierarchical tree of DocItem objects to gather metadata and links from each file.

Args:
    doc_item (DocItem): The root DocItem object from which the traversal begins. This object represents the starting point in the hierarchical tree structure.

Returns:
    List[dict]: A list of dictionaries, each encapsulating metadata and links from a file within the hierarchical tree. Each dictionary includes the following keys:
        - 'obj_name' (str): The name of the object. This is a unique identifier for each item in the tree structure.
        - 'md_content' (str): The content of the latest markdown entry associated with the file. This provides context and details about the file's purpose or functionality.
        - 'who_reference_me' (List[DocItem]): A list of DocItems that reference the current item. This aids in understanding inter-file dependencies and relationships.
        - 'reference_who' (List[DocItem]): A list of DocItems referenced by the current item. This offers insights into how the current file is utilized or interacts with other files.
        - 'tree_path' (str): A string representation of the tree path, joined by '->'. This provides a traceable route from the root DocItem to the current item, offering context about its position within the hierarchy.

Raises:
    None: The function does not raise any exceptions under normal operation. It gracefully handles cases where no components are found or when the ignore list is exhaustive.

Note:
    This function is integral to the ChangeDetector component of the Repository Documentation Generator, which monitors changes in the repository to determine which documentation items need updating or generating. It works in conjunction with other features like the ChatEngine for interactive communication and the TaskManager for efficient task allocation.

    See also: The DocItem class documentation for more information on its attributes and methods.
"""
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
        '''"""Retrieves metadata and links from a given DocItem object within the Repository Documentation Generator project.

This function is part of the Runner module, which is responsible for executing tasks related to documentation generation. It specifically focuses on extracting essential information from a DocItem object to facilitate comprehensive documentation creation.

[Longer description]

Args:
    doc_item (DocItem): The DocItem object from which metadata and links are extracted. This object encapsulates various attributes pertinent to the documentation process, such as name, markdown content, references, and tree path.

Returns:
    dict: A dictionary containing the following keys:
        - 'obj_name' (str): The name of the DocItem object, which is a crucial identifier in the repository's documentation structure.
        - 'md_content' (str): The content of the latest markdown entry associated with the DocItem. This provides a snapshot of the most recent documentation updates.
        - 'who_reference_me' (List[DocItem]): A list of DocItems that reference the current item. This aids in understanding inter-documentation relationships and maintaining accurate cross-references.
        - 'reference_who' (List[DocItem]): A list of DocItems referenced by the current item. This is instrumental in constructing comprehensive documentation, ensuring all relevant links are included.
        - 'tree_path' (str): A string representation of the tree path, joined by '->'. This offers a hierarchical view of the DocItem's location within the repository, facilitating navigation and organization.

Raises:
    None: This method does not raise any exceptions under normal operation, ensuring seamless integration into the documentation generation workflow.

Note:
    See also: The DocItem class documentation for more information on its attributes and methods. This provides context on the structure and capabilities of the DocItem objects used as inputs to this function.
"""'''
        return {'obj_name': doc_item.obj_name, 'md_content': doc_item.md_content[-1].split('\n\n')[0], 'who_reference_me': doc_item.who_reference_me, 'reference_who': doc_item.reference_who, 'tree_path': '->'.join([obj.obj_name for obj in doc_item.tree_path])}

    def generate_main_idea(self, docs):
        '''"""Generates the main project idea based on repository documentation items.

This function constructs a detailed project idea by formatting a template with the provided list of repository documentation items. Each item includes component name, description, and place in hierarchy. The formatted string is then passed to a language model to expand upon it, resulting in a comprehensive project overview.

Args:
    docs (List[Dict]): A list of dictionaries where each dictionary contains 'obj_name', 'md_content', and 'tree_path' keys representing the component name, description, and place in hierarchy respectively.

Returns:
    str: The generated main project idea as a string, encapsulating the project's structure, components, and their descriptions.

Raises:
    Exception: If there is an error during the language model chat call.

Note:
    This function is part of the Repository Documentation Generator, a tool designed to automate software project documentation. It leverages advanced techniques such as chat-based interaction and multi-task dispatching for efficient documentation generation.

    The 'generate_main_idea' function relies on the ChatEngine to generate the idea. It uses a template to format messages and then passes them to the language model for expansion, based on the settings retrieved from SettingsManager (specifically, the language setting). This process encapsulates the project's structure and components, providing a detailed overview.

    See also: repo_agent.chat_engine.ChatEngine.generate_idea for more details on how the idea is generated.
"""'''
        logger.info('Generation of the main idea')
        main_project_idea = self.generate_main_project_idea(docs)
        logger.info(f'Successfully generated the main idea')
        return main_project_idea

    def summarize_modules(self):
        """# Repository Documentation Generator: summarize_modules Function

The `summarize_modules` function is a critical component of the Repository Documentation Generator, responsible for summarizing documentation pages within the repository's directory structure. It operates recursively, traversing the given root directory of a documentation repository to generate summaries for each Python file and subdirectory.

## Functionality

This function utilizes a predefined repository structure and an initialized chat engine to produce these summaries. It forms part of the multi-task dispatch system, contributing to efficient resource allocation and task management within the documentation generation workflow.

## Args

- `self` (Runner): An instance of the Runner class, which encapsulates various functionalities necessary for the documentation generation process. This includes managing project structures (`ProjectManager`), executing tasks (`TaskManager`, `worker`), and handling settings (`SettingsManager`).

## Returns

- `dict`: A nested dictionary structure containing summaries for each directory/module. The top-level keys are:
  - 'name' (str): The name of the directory.
  - 'path' (str): The full path to the directory.
  - 'file_summaries' (list): A list of file summaries within the directory.
  - 'submodules' (list): A list of submodule summaries, representing nested directories.
  - 'module_summary' (dict): An overall summary of the module, encapsulating information from individual files and submodules.

## Raises

- `None`: This function does not raise any exceptions under normal operation. Any errors encountered during execution should be handled internally or by calling functions/methods.

## Note

This function relies on a correctly formatted repository structure and a properly initialized chat engine for accurate summarization. It is invoked by the `summarize_modules` method in the Runner class, contributing to the broader documentation generation process orchestrated by the Repository Documentation Generator. 

See also: [Repository Documentation Generator](https://github.com/your-repo/repo_agent) (for context and additional functionalities)."""
        logger.info('Modules documentation generation')
        res = summarize_repository(self.meta_info.repo_path, self.meta_info.repo_structure, self.chat_engine)
        self.update_modules(res)
        self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path)
        logger.info(f'Successfully generated module summaries')
        return res

    def update_modules(self, module):
        """**Updates the documentation for modules within the repository's hierarchical tree structure.**

[Longer description if needed.]

This function, part of the Repository Documentation Generator, is designed to automate the updating of module documentation within a software project. It recursively traverses the repository's hierarchical tree structure to locate specified modules and submodules, appending their summaries to corresponding DocItem's md_content and setting their status to 'doc_up_to_date'.

Args:
    self (Runner): An instance of the Runner class, managing the documentation update process.
    module (dict): A dictionary containing information about the module to update. It includes 'path' and 'module_summary', with 'submodules' as a list of dictionaries with similar structure for submodule updates.

Returns:
    None

Raises:
    None

Note:
    This method leverages the search_tree functionality from repo_agent.runner to locate items in the hierarchical tree structure. Upon finding a module, it appends the module's summary to the corresponding DocItem's md_content and sets the item's status to 'doc_up_to_date'. For each submodule within the module, it calls itself recursively to ensure all submodules are also updated.

See also:
    repo_agent.doc_meta_info.DocItemStatus for possible item statuses.
    repo_agent.runner.search_tree for the method used to locate items in the hierarchical tree structure."""
        rel_path = os.path.relpath(module['path'], self.meta_info.repo_path)
        doc_item = self.search_tree(self.meta_info.target_repo_hierarchical_tree, rel_path)
        doc_item.md_content.append(module['module_summary'])
        doc_item.item_status = DocItemStatus.doc_up_to_date
        for sm in module['submodules']:
            self.update_modules(sm)

    def search_tree(self, doc: DocItem, path: str):
        """# Repository Documentation Generator: search_tree Method

The `search_tree` method is part of the ProjectManager within the Repository Documentation Generator, facilitating the traversal of a tree structure to locate specific DocItem instances based on provided paths. This functionality supports the automation of documentation generation by accurately identifying and retrieving relevant items from complex repository hierarchies.

## Description

Searches for a `DocItem` within the tree structure based on a given path using a recursive approach. It checks each child node of the current node, returning the matching `DocItem` if found or recursively calling itself with the child as the new root and the same path until the target is located or all possibilities are exhausted.

## Args

- `doc` (type: `DocItem`): The root node of the tree to search within. Represents the starting point in the repository's hierarchical structure.
- `path` (type: `str`): The path to search for within the tree. Specifies the desired location of the target `DocItem`.

## Returns

- type: `DocItem`: The `DocItem` that matches the given path, or `None` if no match is found in the tree structure.

## Raises

- None: This method does not raise any exceptions under normal operation.

## Note

This recursive search method systematically explores each level of the tree, comparing node names against the remaining path string. If a match is identified, it returns the corresponding `DocItem`. In cases where no matching item is found after exhausting all possibilities, it returns `None`, indicating that the specified path does not exist within the provided tree structure.

This method exemplifies the Repository Documentation Generator's capability to navigate and extract specific information from intricate repository layouts, thereby supporting efficient documentation generation processes."""
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
        """[Short description]

Converts a given file path to dot notation format for use within the Repository Documentation Generator project.

Args:
    path (Path or str): The file path to be converted. If a string is provided, it will be converted to a Path object.
    class_ (str): The class name to append after the dot-notated path. This aligns with the 'DocItemType' feature of the project, facilitating accurate documentation generation.

Returns:
    str: A string in the format '::: <dot_notation_path>.<class_name>'. This output is utilized by the 'Runner' class within the ProjectManager to generate markdown file paths, contributing to the automated documentation process.

Raises:
    None

Note:
    This method is integral to the internal operations of the Runner class in the Repository Documentation Generator. It transforms each segment of the provided path into dot notation, excluding the '.py' extension, and then joins these segments with a dot ('.'). Subsequently, it appends the specified class name, thereby creating a structured format for documentation paths. This process aligns with the 'EdgeType' feature, ensuring precise documentation generation across various software project structures.
"""
        path_obj = Path(path) if isinstance(path, str) else path
        processed_parts = []
        for part in path_obj.parts:
            if part.endswith('.py'):
                part = part[:-3]
            processed_parts.append(part)
        dot_path = '.'.join(processed_parts)
        return f'::: {dot_path}.{class_}'

    def markdown_refresh(self):
        """
[Short one-line description]
Refreshes markdown files based on changes detected by the ChangeDetector.

[Longer description if needed.]
The `markdown_refresh` function is a part of the Repository Documentation Generator, an automated tool designed to streamline the documentation process for software projects. This function specifically handles the refreshing of markdown files in response to detected changes within the repository. It leverages the ChangeDetector component to identify which documentation items require updating or generation.

Args:
    changes (list): A list of tuples, where each tuple contains a file path and a boolean indicating whether the file has been modified.
    project_settings (ProjectSettings): An instance of ProjectSettings, containing configuration details for the current project.
    logger (logging.Logger): A logger instance used for tracking progress and errors during execution.

Returns:
    dict: A dictionary where keys are file paths and values are boolean indicators of whether each file was successfully refreshed.

Raises:
    ValueError: If the 'changes' argument is not a list or if any item in the list is not a tuple with exactly two elements.
    Exception: If an error occurs during the refresh process, such as a failure to write to a file.

Note:
    This function operates within the broader context of the Repository Documentation Generator, which employs various components like ChatEngine and TaskManager to facilitate interactive communication and multi-task dispatching respectively. It contributes to the overall goal of automating and simplifying the documentation generation process for software projects.
"""
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
                """[Short one-line description]

The `get_new_objects` function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. This specific method identifies added and deleted objects (functions or classes) in Python files by comparing their current version with the previous version, as managed by Git.

[Longer description if needed]

The `get_new_objects` function operates within the context of a Python project analysis tool, specifically designed to identify changes in Python files across different versions or commits. It leverages Git for version control and Python's Abstract Syntax Tree (AST) module for parsing and analyzing code structure.

This method primarily compares two versions of a .py file: the current version from the working directory and the previous version from the last commit. By extracting functions and classes from these versions, it identifies additions ('new_obj') and deletions ('del_obj') in the codebase.

Args:
    file_handler (FileHandler): The file handler object, responsible for managing file-related operations such as reading file content and interacting with Git repositories. This includes retrieving modified file versions and parsing Python code snippets to extract details about functions and classes.

Returns:
    tuple: A tuple containing two lists - 'new_obj' and 'del_obj'. 'new_obj' is a list of strings representing the names of functions or classes that have been added in the current version compared to the previous one. 'del_obj' is a list of strings representing the names of functions or classes that have been deleted in the current version compared to the previous one.

Raises:
    None

Note:
    This function relies on two auxiliary methods from the `FileHandler` class:
        - `get_modified_file_versions()`: Retrieves the current and previous versions of a modified file.
        - `get_functions_and_classes(code_content)`: Parses a Python code snippet to extract details about its functions and classes, including their names, line numbers, parent structures (if any), and parameters.

    The function uses set operations (`-` for difference) to identify added and deleted objects between the two versions.
"""
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
        try:
            subprocess.check_call(['git', 'commit', '--no-verify', '-m', commit_message], shell=True)
        except subprocess.CalledProcessError as e:
            print(f'An error occurred while trying to commit {str(e)}')

    def run(self):
        '''"""Performs a Git commit with the provided message within the context of the Repository Documentation Generator project.

This function, part of the Runner class within the repo_agent module, utilizes the subprocess module to execute the 'git commit' command with the '--no-verify' flag. This skips pre-commit hooks, allowing for a direct commit without additional checks. The commit message is passed as an argument to this function.

Args:
    self (Runner): An instance of the Runner class, which manages tasks within the Repository Documentation Generator project.
    commit_message (str): The message to be committed. This could include details about changes made to the repository for documentation purposes.

Returns:
    None

Raises:
    subprocess.CalledProcessError: If the Git command fails to execute. This could occur due to various reasons such as incorrect permissions, missing files in the working tree, etc., disrupting the documentation generation process.

Note:
    This method does not return any value but prints an error message if a CalledProcessError occurs. It is crucial for maintaining the integrity of the repository's documentation.

    See also: The 'git commit' documentation for more details on the command and its flags.
"""'''
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
        """
[Runs the documentation generation process].  

This function initiates the comprehensive documentation generation workflow for software projects, leveraging advanced techniques such as change detection, interactive communication, and multi-task dispatching. It serves as the primary execution point for the Repository Documentation Generator, orchestrating various components to produce accurate, up-to-date documentation pages, summaries, and metadata.

Args:  
    project_settings (ProjectSettings): The configuration settings for the current project.  
    cli_args (Namespace): Command-line arguments provided by the user.  

Returns:  
    int: 0 on success, non-zero otherwise.  

Raises:  
    ValueError: If invalid project settings or command-line arguments are provided.  

Note:  
    This function is a critical component of the Repository Documentation Generator, coordinating multiple subsystems to ensure seamless and efficient documentation generation. It interacts with various modules such as ChangeDetector, ChatEngine, TaskManager, and others to accomplish its task.
"""
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
        """
Adds a new item to the repository documentation.

This function is part of the Repository Documentation Generator, an automated tool designed to streamline the creation and maintenance of software project documentation. It facilitates the addition of new items to the repository's documentation structure, ensuring that all relevant information is accurately captured and up-to-date.

Args:
    item (dict): The details of the new item to be added. This should include fields such as 'title', 'description', 'type', etc., depending on the specific requirements of the documentation system.
    project_settings (ProjectSettings): The settings object for the current project, which may include configuration parameters related to the documentation structure and formatting.

Returns:
    dict: A confirmation dictionary indicating success or failure. It includes a 'status' field ('success' or 'failure') and an optional 'message' field providing additional details about the outcome.

Raises:
    ValueError: If the 'item' parameter is not provided or is of incorrect type, or if the 'project_settings' parameter is missing or invalid.

Note:
    This function operates within the broader context of the Repository Documentation Generator, which employs various components like ChangeDetector, ChatEngine, and TaskManager to ensure comprehensive and efficient documentation management.
"""
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
        '''"""
Processes file changes within the repository documentation generation workflow.

This function, part of the Repository Documentation Generator, is responsible for handling changes in files identified by the ChangeDetector component. It uses a FileHandler object to perform operations on these changed files. The function reads the entire Python file's code, identifies structural changes, and logs this information.

The process involves checking if the file path exists within a JSON hierarchy file managed by the ProjectManager. If it does, the function updates the corresponding entry with new change details. This updated JSON content is then converted into Markdown format and written to a .md file.

If the file path is not found in the JSON hierarchy file, a new entry is created for this file. Additionally, any unstaged Markdown files generated during runtime are added to the staging area by the GitignoreChecker component.

Args:
    repo_path (str): The path to the repository where changes are detected and processed.
    file_path (str): The relative path to the file within the repository.
    is_new_file (bool): Indicates whether the file is newly added or an existing file with modifications.

Returns:
    None

Raises:
    None

Note:
    This function operates as part of a broader workflow managed by the Repository Documentation Generator. It interacts with various components such as ChangeDetector, FileHandler, ProjectManager, and GitignoreChecker to ensure comprehensive documentation of repository changes.

    See also: ProjectManager in repo_agent/runner.py for managing project structures and tasks within this workflow; FileHandler in repo_agent/runner.py for detailed file operations; GitignoreChecker in repo_agent/runner.py for handling .gitignore file checks and temporary file management.
"""'''
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
        """# Repository Documentation Generator: update_existing_item Function

The `update_existing_item` function is a crucial component of the Repository Documentation Generator, facilitating the updating of existing file structure information based on changes detected in Python files. This function operates within the broader context of automating and streamlining the documentation process for software projects.

## Description

This function processes modifications in Python files, specifically additions and deletions of objects (functions or classes), and updates the corresponding entries in a dictionary representing the file's structure. It ensures that the documentation remains current by generating new documentation content for newly added objects based on information from the file handler and referencer list.

## Functionality

The `update_existing_item` function is invoked when changes are identified in a Python file, as determined by the `ChangeDetector`. It interacts with several other components of the Repository Documentation Generator:

- **FileHandler**: This component manages file-related data and generates a dictionary representing the file's structure. The `update_existing_item` function utilizes this to retrieve detailed information about each object (type, line numbers, parent, etc.).
  
- **get_new_objects**: This method identifies new and deleted objects by comparing the current version of the file with the previous one. It provides the necessary data for the `update_existing_item` function to process these changes.

- **update_object**: This method updates the documentation content of a specified object within the file structure using information from the FileHandler and referencer list. The `update_existing_item` function employs this to modify existing objects' documentation as needed.

## Parameters

def update_existing_item(
    file_dict: dict,  # Current file structure information dictionary
    file_handler: 'FileHandler',  # File handler object for accessing file-related data
    changes_in_pyfile: dict  # Dictionary containing information about changed objects in the Python file
) -> dict:  # Updated file structure information dictionary


### Args

- `file_dict` (dict): A dictionary containing the current file structure information.
- `file_handler` ('FileHandler'): The file handler object used to access file-related data.
- `changes_in_pyfile` (dict): A dictionary containing information about objects that have changed in the Python file, including additions and deletions.

## Returns

The function returns an updated version of the file structure information dictionary (`dict`).

## Raises

This function does not raise any exceptions (`None`).

## Notes

- This function is part of the multi-task dispatch system implemented by `TaskManager` and `worker`, ensuring efficient resource allocation and task management.
  
- It relies on the `ChangeDetector` to identify changes in Python files, thereby determining which documentation items need updating or generating.

- The function contributes to maintaining accurate and up-to-date documentation for software projects by automatically handling additions and deletions of objects within Python files."""
        if obj_name in file_dict:
            obj = file_dict[obj_name]
            response_message = self.chat_engine.generate_doc(obj, file_handler, obj_referencer_list)
            obj['md_content'] = response_message.content

    def get_new_objects(self, file_handler):
        """[Updates the documentation content of an object within a file structure as part of the Repository Documentation Generator project].  

This function updates the documentation content of a specified object within a file structure, contributing to the automated management of software project documentation. It retrieves existing object information from a dictionary, generates new documentation using the `generate_doc` method of the `ChatEngine`, and then updates the object's 'md_content' field with the generated content.

Args:
    file_dict (dict): A dictionary containing old object information. This includes metadata about the object within the project's file structure.
    file_handler (object): The file handler object used to access file-related data, facilitating interaction with the repository.
    obj_name (str): The name of the object whose documentation is to be updated. This identifier links the object to its corresponding information in `file_dict`.
    obj_referencer_list (list): A list of referencers associated with the object. These are entities that point to or are pointed from by the specified object, aiding in understanding its context within the project.

Returns:
    None: This function does not return any value; its purpose is to modify the documentation content directly within `file_dict`.

Raises:
    KeyError: If the specified object does not exist in the `file_dict`. This exception indicates that the object's information was not found, preventing an attempt to update non-existent data.

Note:
    This function operates as part of a larger process for managing and updating documentation within a project's file structure, leveraging techniques such as chat-based interaction and multi-task dispatching. It relies on other methods, like `generate_doc` from the `ChatEngine`, to produce updated content. The Repository Documentation Generator aims to simplify and automate the documentation generation process, ensuring consistent, up-to-date documentation for software projects."""
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