import os
from pathlib import Path
from typing import List, Dict, Any
from repo_agent.settings import SettingsManager

def summarize_repository(root_dir: str, repo_structure, chat_engine) -> Dict[str, Any]:
    """Recursively generates summaries for Python modules and submodules within a repository's directory structure.
    
    This method leverages the Repository Agent's capabilities to analyze and summarize Python projects at the repository level, ensuring comprehensive and up-to-date documentation by utilizing large language models (LLMs) through the `ChatEngine` class.
    
    Args:
        root_dir (str): Path to the root directory of the documentation repository.
        repo_structure (dict): Repository structure containing information about files and directories.
        chat_engine: Chat engine used for generating summaries.
    
    Returns:
        Dict[str, Any]: A nested dictionary structure containing summaries for each directory/module.
    
    Note:
        See also: SettingsManager.get_setting(), create_module_summary()
    
    Recursively summarizes the contents of a directory by analyzing Python files and subdirectories.
    
    Automates the process of generating comprehensive documentation for Python projects at the repository level, enhancing developer productivity and code maintainability.
    
    Args:
        directory (Path): The directory to be summarized.
        repo_structure (dict): The structure of the repository containing file paths and their components.
        chat_engine: The engine used for summarizing modules.
        root_dir (str): The root directory of the project.
    
    Returns:
        dict: A dictionary containing information about the directory, including summaries of files and subdirectories.
    
    Note:
        - Files with a .py extension are processed to extract relevant components such as classes and functions.
        - Subdirectories are recursively summarized if they are not in the ignored folders list."""

    def summarize_directory(directory: Path, repo_structure, chat_engine, root_dir) -> Dict[str, Any]:
        """Summarizes the contents of a directory by analyzing Python files and subdirectories.
    
    Automates the process of generating comprehensive documentation for Python projects at the repository level, enhancing developer productivity and code maintainability.
    
    Args:
        directory (Path): The directory to be summarized.
        repo_structure (dict): The structure of the repository containing file paths and their components.
        chat_engine: The engine used for summarizing modules.
        root_dir: The root directory of the project.
    
    Returns:
        dict: A dictionary containing information about the directory, including summaries of files and subdirectories.
    
    Note:
        - Files with a .py extension are processed to extract relevant components such as classes and functions.
        - Subdirectories are recursively summarized if they are not in the ignored folders list."""
        settings = SettingsManager().get_setting()
        ignored_folders = settings.project.ignore_list
        file_paths = []
        subdir_paths = []
        for item in directory.iterdir():
            if item.is_file() and item.suffix == '.py':
                file_paths.append(item)
            elif item.is_dir() and str(item) not in ignored_folders:
                subdir_paths.append(item)
        file_summaries = []
        for file_path in file_paths:
            if file_path.is_file() and file_path.suffix == '.py':
                stripped_file_path = os.path.relpath(file_path, start=root_path)
                desc = [f'File {file_path} has such components:']
                if stripped_file_path in repo_structure and repo_structure[stripped_file_path]:
                    for obj in list(filter(lambda x: x['type'] in ['ClassDef', 'FunctionDef'], repo_structure[stripped_file_path])):
                        if obj['md_content']:
                            desc.append(obj['md_content'][-1].split('\n\n')[0])
                    if len(desc) > 1:
                        file_summaries.append('\n'.join(desc))
        submodule_summaries = list(filter(lambda x: x['module_summary'], [summarize_directory(subdir, repo_structure, chat_engine, root_dir) for subdir in subdir_paths]))
        submodules_summaries_text = [submod['module_summary'] for submod in submodule_summaries]
        if not file_summaries and (not submodules_summaries_text):
            module_summary = ''
        else:
            module_summary = create_module_summary(directory.name, file_summaries, submodules_summaries_text, chat_engine)
        return {'name': directory.name, 'path': str(directory), 'file_summaries': file_summaries, 'submodules': submodule_summaries, 'module_summary': module_summary}
    root_path = Path(root_dir)
    return summarize_directory(root_path, repo_structure, chat_engine, root_dir)

def create_module_summary(name: str, file_summaries: List[str], submodule_summaries: List[str], chat_engine) -> str:
    """Generates a summary for a Python module by combining file and submodule summaries.
    
    This method utilizes the `ChatEngine` instance to create a comprehensive summary of a module, integrating details from both files and submodules within it. The Repository Agent tool automates documentation generation for complex Python projects, ensuring high-quality and consistent documentation across all modules.
    
    Args:
        name (str): The name of the module.
        file_summaries (List[str]): List of summaries for individual files within the module.
        submodule_summaries (List[str]): List of summaries for submodules within the module.
        chat_engine: An instance of `ChatEngine` used to generate the summary.
    
    Returns:
        str: A comprehensive summary of the module generated by the language model.
    
    Raises:
        Exception: If an error occurs during the summarization process with the language model.
    
    Note:
        Uses `SettingsManager.get_setting()` to retrieve project settings and configure chat messages."""
    summary_content = [f'Module: {name}', '\n## Files Summary:\n\n- ' + '\n- '.join(file_summaries).replace('#', '##'), '\n\n## Submodules Summary:\n\n- ' + '\n- '.join(submodule_summaries).replace('#', '##')]
    result = chat_engine.summarize_module('\n-----\n'.join(summary_content))
    return result