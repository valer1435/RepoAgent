import os
from pathlib import Path
from typing import List, Dict, Any

from repo_agent.settings import SettingsManager


def summarize_repository(root_dir: str, repo_structure, chat_engine) -> Dict[str, Any]:
    """
    Recursively summarizes documentation pages in a repository directory structure.

    Args:
        root_dir: Path to the root directory of the documentation repository

    Returns:
        A nested dictionary structure containing summaries for each directory/module
    """

    def summarize_directory(directory: Path, repo_structure, chat_engine, root_dir) -> Dict[str, Any]:

        settings = SettingsManager().get_setting()
        ignored_folders = settings.project.ignore_list
        # Get all files and subdirectories
        file_paths = []
        subdir_paths = []
        for item in directory.iterdir():
            if item.is_file() and item.suffix == '.py':
                file_paths.append(item)
            elif item.is_dir() and str(item) not in ignored_folders:
                subdir_paths.append(item)

        # Step 2: Summarize files
        file_summaries = []
        for file_path in file_paths:
            if file_path.is_file() and file_path.suffix == '.py':
                stripped_file_path = os.path.relpath(file_path, start=root_path)
                desc = [f"File {file_path} has such components:"]
                if stripped_file_path in repo_structure and repo_structure[stripped_file_path]:
                    for obj in list(filter(lambda x: x['type'] in ['ClassDef', 'FunctionDef'],
                                           repo_structure[stripped_file_path])):
                        if obj['md_content']:
                            desc.append(obj['md_content'][-1].split('\n\n')[0])
                    if len(desc) > 1:
                        file_summaries.append('\n'.join(desc))

        # Step 5: Recursively summarize subdirectories
        submodule_summaries = list(filter(lambda x: x["module_summary"],
                                          [summarize_directory(subdir, repo_structure, chat_engine, root_dir) for subdir
                                           in subdir_paths]))

        # Step 3: Create module summary
        submodules_summaries_text = [submod["module_summary"] for submod in submodule_summaries]
        if not file_summaries and not submodules_summaries_text:
            module_summary = ""
        else:
            module_summary = create_module_summary(
                directory.name,
                file_summaries,
                submodules_summaries_text,
                chat_engine
            )

        # Return structure with all information
        return {
            "name": directory.name,
            "path": str(directory),
            "file_summaries": file_summaries,
            "submodules": submodule_summaries,
            "module_summary": module_summary
        }

    root_path = Path(root_dir)
    return summarize_directory(root_path, repo_structure, chat_engine, root_dir)


def create_module_summary(
        name: str,
        file_summaries: List[str],
        submodule_summaries: List[str],
        chat_engine
) -> str:
    """
    Combine file and submodule summaries into a module summary
    """
    # Replace this with actual implementation
    summary_content = [
        f"Module: {name}",
        "\n## Files Summary:\n\n- " + "\n- ".join(file_summaries).replace('#', "##"),
        "\n\n## Submodules Summary:\n\n- " + "\n- ".join(submodule_summaries).replace('#', "##")
    ]
    result = chat_engine.summarize_module("\n-----\n".join(summary_content))
    return result
