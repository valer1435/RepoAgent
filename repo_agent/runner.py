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
from repo_agent.doc_meta_info import (
    DocItem,
    DocItemStatus,
    MetaInfo,
    need_to_generate,
    DocItemType,
)
from repo_agent.file_handler import FileHandler
from repo_agent.log import logger
from repo_agent.module_summarization import summarize_repository
from repo_agent.multi_task_dispatch import worker
from repo_agent.project_manager import ProjectManager
from repo_agent.settings import SettingsManager
from repo_agent.utils.docstring_updater import update_doc
from repo_agent.utils.meta_info_utils import delete_fake_files, make_fake_files


class Runner:
    """
    A class for generating and managing documentation for a project.

    This class provides methods to recursively find Python files, generate
    documentation using a chat engine, manage tasks with threading, and update
    the documentation in the repository. It also includes functionalities for
    summarizing modules, searching the document tree, and committing changes
    to Git."""

    def __init__(self):
        """
        Initializes the documentation generator."""

        self.setting = SettingsManager.get_setting()
        self.absolute_project_hierarchy_path = (
            self.setting.project.target_repo / self.setting.project.hierarchy_name
        )
        shutil.copy("mkdocs.yml", Path(self.setting.project.target_repo, "mkdocs.yml"))
        self.project_manager = ProjectManager(
            repo_path=self.setting.project.target_repo,
            project_hierarchy=self.setting.project.hierarchy_name,
        )
        self.change_detector = ChangeDetector(
            repo_path=self.setting.project.target_repo
        )
        self.chat_engine = ChatEngine(project_manager=self.project_manager)
        file_path_reflections, jump_files = make_fake_files()
        setting = SettingsManager.get_setting()
        if not self.absolute_project_hierarchy_path.exists():
            self.meta_info = MetaInfo.init_meta_info(file_path_reflections, jump_files)
            self.meta_info.checkpoint(
                target_dir_path=self.absolute_project_hierarchy_path
            )

        else:
            project_abs_path = setting.project.target_repo
            file_handler = FileHandler(project_abs_path, None)
            repo_structure = file_handler.generate_overall_structure(
                file_path_reflections, jump_files
            )
            self.meta_info = MetaInfo.from_checkpoint_path(
                self.absolute_project_hierarchy_path, repo_structure
            )
            SettingsManager.get_setting().project.main_idea = self.meta_info.main_idea
        self.runner_lock = threading.Lock()

    def get_all_pys(self, directory):
        """
        Recursively identifies and returns a list of all Python files within the specified directory.

            Args:
                directory: The path to the directory to search.

            Returns:
                list: A list of strings, where each string is the absolute path to a
                    Python file (.py) found in the directory and its subdirectories.
        """

        python_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        return python_files

    def generate_doc_for_a_single_item(self, doc_item: DocItem):
        """
        Generates documentation for a code item, potentially skipping it if ignored or if generation fails. Updates the item's status and checkpoints progress during successful completion.

            This method attempts to generate documentation for the given DocItem using a chat engine.
            It checks if the item should be ignored based on project settings and updates its status accordingly.
            Handles potential exceptions during document generation and logs errors.

            Args:
                doc_item: The DocItem object for which to generate documentation.

            Returns:
                None
        """

        settings = SettingsManager.get_setting()
        try:
            if not need_to_generate(doc_item, self.setting.project.ignore_list):
                print(
                    f"Content ignored/Document generated, skipping: {doc_item.get_full_name()}"
                )
            else:
                print(
                    f" -- Generating document  {Fore.LIGHTYELLOW_EX}{doc_item.item_type.name}: {doc_item.get_full_name()}{Style.RESET_ALL}"
                )
                response_message = self.chat_engine.generate_doc(doc_item=doc_item)
                doc_item.md_content.append(response_message)
                if settings.project.main_idea:
                    doc_item.item_status = DocItemStatus.doc_up_to_date
                self.meta_info.checkpoint(
                    target_dir_path=self.absolute_project_hierarchy_path
                )
        except Exception:
            logger.exception(
                f"Document generation failed after multiple attempts, skipping: {doc_item.get_full_name()}"
            )
            doc_item.md_content.append("")
            if settings.project.main_idea:
                doc_item.item_status = DocItemStatus.doc_up_to_date

    def generate_main_project_idea(self, docs: List[Dict]):
        """
        Combines component details – name, description, and location within the project – into a cohesive prompt for generating an overall project summary.

            Args:
                docs: A list of dictionaries, where each dictionary represents a
                    component and contains its name, description, and hierarchy path.

            Returns:
                str: The generated project idea as a string.
        """

        str_obj = []
        for doc in docs:
            str_obj.append(
                f"Component name: {doc['obj_name']}\nComponent description: {doc['md_content']}\nComponent place in hierarchy: {doc['tree_path']}"
            )
        response_message = self.chat_engine.generate_idea("\n\n".join(str_obj))
        return response_message

    def generate_doc(self):
        """
        Generates documentation by analyzing the project's code, creating a task list for processing, and utilizing multi-threading to produce summaries. It manages an existing or new task list and checkpoints progress while handling potential errors during generation.

            This method manages a task list, spawns threads to process documentation tasks,
            and handles potential errors during generation. It also updates metadata and
            checkpoints the generated documents.

            Args:
                None

            Returns:
                None
        """

        logger.info("Starting to generate documentation")
        check_task_available_func = partial(
            need_to_generate, ignore_list=self.setting.project.ignore_list
        )
        task_manager = self.meta_info.get_topology(check_task_available_func)
        before_task_len = len(task_manager.task_dict)
        if not self.meta_info.in_generation_process:
            self.meta_info.in_generation_process = True
            logger.info("Init a new task-list")
        else:
            logger.info("Load from an existing task-list")
        self.meta_info.print_task_list(task_manager.task_dict)
        try:
            threads = [
                threading.Thread(
                    target=worker,
                    args=(
                        task_manager,
                        process_id,
                        self.generate_doc_for_a_single_item,
                    ),
                )
                for process_id in range(self.setting.project.max_thread_count)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.markdown_refresh()
            if self.setting.project.main_idea:
                self.meta_info.document_version = (
                    self.change_detector.repo.head.commit.hexsha
                )
                self.meta_info.in_generation_process = False
                self.meta_info.checkpoint(
                    target_dir_path=self.absolute_project_hierarchy_path
                )
            logger.info(
                f"Successfully generated {before_task_len - len(task_manager.task_dict)} documents."
            )
        except BaseException as e:
            logger.error(
                f"An error occurred: {e}. {before_task_len - len(task_manager.task_dict)} docs are generated at this time"
            )

    def get_top_n_components(self, doc_item: DocItem):
        """
        Extracts documented components from a project file structure, respecting specified ignore patterns.

            Iterates through files within the provided DocItem, skipping those matching
            entries in the ignore list.  For each remaining file, it extracts and appends
            Markdown content and links for each class found within that file.

            Args:
                doc_item: The DocItem object to extract components from.

            Returns:
                list: A list of strings, where each string represents the Markdown
                      content and links for a top-level component (class).
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
        """
        Extracts key information from a documentation item, including its name, initial content snippet, references to and from other items, and hierarchical path within the repository.

            Args:
                doc_item: The DocItem object to extract data from.

            Returns:
                dict: A dictionary containing the following keys:
                    - 'obj_name': The name of the object.
                    - 'md_content': The first paragraph of the markdown content.
                    - 'who_reference_me':  Objects that reference this object.
                    - 'reference_who': Objects referenced by this object.
                    - 'tree_path': A string representing the path to the object in the documentation tree.
        """

        return {
            "obj_name": doc_item.obj_name,
            "md_content": doc_item.md_content[-1].split("\n\n")[0],
            "who_reference_me": doc_item.who_reference_me,
            "reference_who": doc_item.reference_who,
            "tree_path": "->".join([obj.obj_name for obj in doc_item.tree_path]),
        }

    def generate_main_idea(self, docs):
        """
        Extracts a concise summary of the project's core purpose from its source code.

            Args:
                docs: The input documents used to generate the main idea.

            Returns:
                The generated main project idea.
        """

        logger.info("Generation of the main idea")
        main_project_idea = self.generate_main_project_idea(docs)
        logger.info(f"Successfully generated the main idea")
        return main_project_idea

    def summarize_modules(self):
        """
        Generates documentation summaries for each module within the repository by recursively analyzing its directory structure and code components.

            This method orchestrates the process of summarizing each module within the
            repository, leveraging a chat engine to create concise and informative
            descriptions. It updates the internal module information and persists the
            changes to disk.

            Parameters:
                None

            Returns:
                Dict[str, Any]: A dictionary containing the summary of the repository,
                    including the name, path, file summaries, submodules, and module
                    summary for each directory. This is the result of calling
                    `summarize_repository`. See `summarize_repository` documentation
                    for details on the structure of this dictionary.

            Raises:
                ValueError: If the root directory does not exist or is not a valid
                    directory (raised by summarize_repository).
        """

        logger.info("Modules documentation generation")
        res = summarize_repository(
            self.meta_info.repo_path, self.meta_info.repo_structure, self.chat_engine
        )
        self.update_modules(res)
        self.meta_info.checkpoint(target_dir_path=self.absolute_project_hierarchy_path)
        logger.info(f"Successfully generated module summaries")
        return res

    def update_modules(self, module):
        """
        Recursively updates documentation content for a module and its submodules by appending summaries to the corresponding entries in the repository's documentation tree. It also marks the module’s documentation as current.

            Args:
                module: A dictionary containing information about the module,
                    including its path and summary.  It also contains a list of
                    submodules under the 'submodules' key.

            Returns:
                None
        """

        rel_path = os.path.relpath(module["path"], self.meta_info.repo_path)
        doc_item = self.search_tree(
            self.meta_info.target_repo_hierarchical_tree, rel_path
        )
        doc_item.md_content.append(module["module_summary"])
        doc_item.item_status = DocItemStatus.doc_up_to_date
        for sm in module["submodules"]:
            self.update_modules(sm)

    def search_tree(self, doc: DocItem, path: str):
        """
        Recursively descends the document tree to locate a specific path.

            Args:
                doc: The root of the document tree to search.
                path: The path to search for within the tree.

            Returns:
                DocItem: The document item at the specified path, or None if not found.
        """

        if path == ".":
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
        """
        Transforms a file system path into a dot-separated identifier, suitable for referencing code components within documentation. It handles Python files and excludes `__init__.py` when constructing the identifier.

            Args:
                path: The path to the file or module. Can be a string or a Path object.
                class_: The name of the class within the module.

            Returns:
                str: A string representing the dot notation path to the class,
                     formatted as '::: <dot_path>.<class_>'.
        """

        path_obj = Path(path) if isinstance(path, str) else path
        processed_parts = []
        for part in path_obj.parts:
            if part.endswith(".py"):
                part = part[:-3]
            if part == "__init__":
                continue
            processed_parts.append(part)
        dot_path = ".".join(processed_parts)
        return f"::: {dot_path}.{class_}"

    def markdown_refresh(self):
        """
        Generates markdown documentation for the project by analyzing code structure and content, then writing it to designated files. It handles directories, repositories, and individual Python files, ensuring documentation is up-to-date and reflects the codebase.

            This method rebuilds the markdown files in the designated documentation folder,
            iterating through all files and directories to generate or update their content.
            It handles different item types (file, directory, repository) and ensures that
            markdown content is written to the correct file paths with retry logic for write operations.

            Parameters:
                None

            Returns:
                None
        """

        with self.runner_lock:
            markdown_folder = (
                Path(self.setting.project.target_repo)
                / self.setting.project.markdown_docs_name
            )
            if markdown_folder.exists():
                logger.debug(f"Deleting existing contents of {markdown_folder}")
                shutil.rmtree(markdown_folder)
            markdown_folder.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created markdown folder at {markdown_folder}")
        file_item_list = self.meta_info.get_all_files(count_repo=True)
        logger.debug(f"Found {len(file_item_list)} files to process.")
        for file_item in tqdm(file_item_list):

            def recursive_check(doc_item) -> bool:
                if doc_item.md_content:
                    return True
                for child in doc_item.children.values():
                    if recursive_check(child):
                        return True
                return False

            if (
                not recursive_check(file_item)
                and file_item.item_type == DocItemType._file
            ):
                logger.debug(
                    f"No documentation content for: {file_item.get_full_name()}, skipping."
                )
                continue
            markdown = ""
            if file_item.item_type == DocItemType._dir:
                if file_item.md_content:
                    markdown = file_item.md_content[-1]
            elif file_item.item_type == DocItemType._repo:
                markdown += SettingsManager.get_setting().project.main_idea
            else:
                markdown += f"# {Path(file_item.obj_name).name.strip('.py').replace('_', ' ').title()}\n\n"
                for child in file_item.children.values():
                    update_doc(child.source_node, child.md_content[-1])
                    markdown += f"## {child.obj_name}\n{self.convert_path_to_dot_notation(Path(file_item.obj_name), child.obj_name)}\n\n"
                    for n_child in child.children.values():
                        update_doc(n_child.source_node, n_child.md_content[-1])
                children_names = list(file_item.children.keys())
                if children_names:
                    with open(
                        Path(self.setting.project.target_repo, file_item.obj_name),
                        "w+",
                        encoding="utf-8",
                    ) as f:
                        value = ast.unparse(
                            file_item.children[children_names[0]].source_node.parent
                        )
                        f.write(value)
            if not markdown:
                logger.warning(
                    f"No markdown content generated for: {file_item.get_full_name()}"
                )
                continue
            if file_item.item_type == DocItemType._dir:
                file_path = (
                    Path(self.setting.project.markdown_docs_name)
                    / Path(file_item.obj_name)
                    / "index.md"
                )
            elif file_item.item_type == DocItemType._repo:
                file_path = Path(self.setting.project.markdown_docs_name) / "index.md"
            else:
                file_path = Path(
                    self.setting.project.markdown_docs_name
                ) / file_item.get_file_name().replace(".py", ".md")
            abs_file_path = self.setting.project.target_repo / file_path
            logger.debug(f"Writing markdown to: {abs_file_path}")
            abs_file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {abs_file_path.parent}")
            with self.runner_lock:
                for attempt in range(3):
                    try:
                        with open(abs_file_path, "w", encoding="utf-8") as file:
                            file.write(markdown)
                        logger.debug(f"Successfully wrote to {abs_file_path}")
                        break
                    except IOError as e:
                        logger.error(
                            f"Failed to write {abs_file_path} on attempt {attempt + 1}: {e}"
                        )
                        time.sleep(1)
        logger.info(
            f"Markdown documents have been refreshed at {self.setting.project.markdown_docs_name}"
        )

    def git_commit(self, commit_message):
        """
        Records changes to the repository with a given message. Handles potential errors during the commit process and reports them to the console.

            Args:
                commit_message: The message for the commit.

            Returns:
                None
        """

        try:
            subprocess.check_call(
                ["git", "commit", "--no-verify", "-m", commit_message], shell=True
            )
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while trying to commit {str(e)}")

    def run(self):
        """
        Runs the documentation process, detecting changes in the repository and generating or updating documentation for modified or new code components. It manages a task queue to parallelize documentation generation and ensures documentation stays synchronized with the latest codebase version.

            This method orchestrates the entire documentation workflow, including initial
            generation, change detection, task management, document updates, and version control.
            It handles cases where a main idea is missing, detects changes in the repository,
            and utilizes multi-threading to efficiently generate documentation for multiple items.

            Parameters:
                None

            Returns:
                None
        """

        if self.meta_info.document_version == "":
            settings = SettingsManager.get_setting()
            if settings.project.main_idea:
                self.generate_doc()
                self.summarize_modules()
                self.markdown_refresh()
            else:
                self.generate_doc()
                settings.project.main_idea = self.generate_main_idea(
                    self.get_top_n_components(
                        self.meta_info.target_repo_hierarchical_tree
                    )
                )
                self.generate_doc()
                self.summarize_modules()
                self.markdown_refresh()
            self.meta_info.checkpoint(
                target_dir_path=self.absolute_project_hierarchy_path,
                flash_reference_relation=True,
            )
            return
        if not self.meta_info.in_generation_process:
            logger.info("Starting to detect changes.")
            "采用新的办法\n            1.新建一个project-hierachy\n            2.和老的hierarchy做merge,处理以下情况：\n            - 创建一个新文件：需要生成对应的doc\n            - 文件、对象被删除：对应的doc也删除(按照目前的实现，文件重命名算是删除再添加)\n            - 引用关系变了：对应的obj-doc需要重新生成\n            \n            merge后的new_meta_info中：\n            1.新建的文件没有文档，因此metainfo merge后还是没有文档\n            2.被删除的文件和obj，本来就不在新的meta里面，相当于文档被自动删除了\n            3.只需要观察被修改的文件，以及引用关系需要被通知的文件去重新生成文档"
            file_path_reflections, jump_files = make_fake_files()
            new_meta_info = MetaInfo.init_meta_info(file_path_reflections, jump_files)
            new_meta_info.load_doc_from_older_meta(self.meta_info)
            self.meta_info = new_meta_info
            self.meta_info.in_generation_process = True
        check_task_available_func = partial(
            need_to_generate, ignore_list=self.setting.project.ignore_list
        )
        task_manager = self.meta_info.get_task_manager(
            self.meta_info.target_repo_hierarchical_tree,
            task_available_func=check_task_available_func,
        )
        for item_name, item_type in self.meta_info.deleted_items_from_older_meta:
            print(
                f"{Fore.LIGHTMAGENTA_EX}[Dir/File/Obj Delete Dected]: {Style.RESET_ALL} {item_type} {item_name}"
            )
        self.meta_info.print_task_list(task_manager.task_dict)
        if task_manager.all_success:
            logger.info(
                "No tasks in the queue, all documents are completed and up to date."
            )
        threads = [
            threading.Thread(
                target=worker,
                args=(task_manager, process_id, self.generate_doc_for_a_single_item),
            )
            for process_id in range(self.setting.project.max_thread_count)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.meta_info.in_generation_process = False
        self.meta_info.document_version = self.change_detector.repo.head.commit.hexsha
        self.meta_info.checkpoint(
            target_dir_path=self.absolute_project_hierarchy_path,
            flash_reference_relation=True,
        )
        logger.info(f"Doc has been forwarded to the latest version")
        self.markdown_refresh()
        delete_fake_files()
        logger.info(f"Starting to git-add DocMetaInfo and newly generated Docs")
        time.sleep(1)
        git_add_result = self.change_detector.add_unstaged_files()
        if len(git_add_result) > 0:
            logger.info(
                f"Added {[file for file in git_add_result]} to the staging area."
            )
