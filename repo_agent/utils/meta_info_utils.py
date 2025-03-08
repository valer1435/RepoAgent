import itertools
import os
import git
from colorama import Fore, Style
from repo_agent.log import logger
from repo_agent.settings import SettingsManager
latest_verison_substring = '_latest_version.py'

def make_fake_files():
    """
[Short one-line description]
Creates fake files for testing purposes within the repository.

[Longer description if needed]
The 'make_fake_files' function is designed to generate artificial files that mimic real data structures, aiding in the development and testing of the Repository Documentation Generator. These files are temporary and do not persist beyond their creation, ensuring they do not interfere with actual repository content.

Args:
    file_paths (List[str]): A list of paths where the fake files will be created. Each path should include the directory structure leading to the desired file location.
    file_contents (Dict[str, Any]): A dictionary where keys are file paths and values are the contents that will be written to each respective file.

Returns:
    None

Raises:
    ValueError: If 'file_paths' or 'file_contents' is not provided as input.

Note:
    This function is primarily used for testing and development purposes within the Repository Documentation Generator project. It does not affect actual repository data unless explicitly designed to do so.
"""
    delete_fake_files()
    setting = SettingsManager.get_setting()
    repo = git.Repo(setting.project.target_repo)
    unstaged_changes = repo.index.diff(None)
    untracked_files = repo.untracked_files
    jump_files = []
    for file_name in untracked_files:
        if file_name.endswith('.py'):
            print(f'{Fore.LIGHTMAGENTA_EX}[SKIP untracked files]: {Style.RESET_ALL}{file_name}')
            jump_files.append(file_name)
    for diff_file in unstaged_changes.iter_change_type('A'):
        if diff_file.a_path.endswith(latest_verison_substring):
            logger.error('FAKE_FILE_IN_GIT_STATUS detected! suggest to use `delete_fake_files` and re-generate document')
            exit()
        jump_files.append(diff_file.a_path)
    file_path_reflections = {}
    for diff_file in itertools.chain(unstaged_changes.iter_change_type('M'), unstaged_changes.iter_change_type('D')):
        if diff_file.a_path.endswith(latest_verison_substring):
            logger.error('FAKE_FILE_IN_GIT_STATUS detected! suggest to use `delete_fake_files` and re-generate document')
            exit()
        now_file_path = diff_file.a_path
        if now_file_path.endswith('.py'):
            raw_file_content = diff_file.a_blob.data_stream.read().decode('utf-8')
            latest_file_path = now_file_path[:-3] + latest_verison_substring
            if os.path.exists(os.path.join(setting.project.target_repo, now_file_path)):
                os.rename(os.path.join(setting.project.target_repo, now_file_path), os.path.join(setting.project.target_repo, latest_file_path))
                print(f'{Fore.LIGHTMAGENTA_EX}[Save Latest Version of Code]: {Style.RESET_ALL}{now_file_path} -> {latest_file_path}')
            else:
                print(f'{Fore.LIGHTMAGENTA_EX}[Create Temp-File for Deleted(But not Staged) Files]: {Style.RESET_ALL}{now_file_path} -> {latest_file_path}')
                try:
                    with open(os.path.join(setting.project.target_repo, latest_file_path), 'w', encoding='utf-8') as writer:
                        pass
                except:
                    pass
            try:
                with open(os.path.join(setting.project.target_repo, now_file_path), 'w', encoding='utf-8') as writer:
                    writer.write(raw_file_content)
            except:
                pass
            file_path_reflections[now_file_path] = latest_file_path
    return (file_path_reflections, jump_files)

def delete_fake_files():
    """**Deletes Fake Files from Target Repository**

This function recursively traverses the target repository, identified by `repo_agent.settings.SettingsManager.get_setting('project.target_repo')`, and removes any file that ends with `latest_version_substring`. If a file with the same name (without the suffix) already exists in the repository, it is renamed back to its original name. Empty files are also deleted.

Args:  
    None

Returns:  
    None

Raises:  
    None

Note:  
    This function is part of the Repository Documentation Generator's cleanup process, ensuring no temporary or fake files remain in the repository post-documentation generation. It leverages the `repo_agent.utils.meta_info_utils.make_fake_files` function to create these temporary files during the documentation process.

    See also: `repo_agent.settings.SettingsManager.get_setting()`, which retrieves the project settings including the target repository path.

Examples:  
    No specific examples are provided as this function operates on file system level and its behavior is deterministic based on the input (i.e., the state of the repository). However, consider a scenario where the repository contains files like `file_1_latest_version_substring` and `file_2`. After execution, these files would be renamed to `file_1` and `file_2`, respectively, if they existed, while any empty files would be removed."""
    setting = SettingsManager.get_setting()

    def gci(filepath):
        '''"""
Deletes fake files and recovers the latest version based on a specific substring pattern within the Repository Documentation Generator project.

This function recursively traverses through all subdirectories within the given filepath, identifying and handling files that match a predefined version pattern. It performs the following actions:

1. If a directory is found, it calls itself (gci) to process the subdirectory.
2. If a file ends with a specific substring (latest_version_substring), it checks for an existing file without this substring.
   - If such a file exists and the current file is empty, it deletes the current file.
   - If the current file is not empty, it renames the current file to the expected filename (without the version substring) and overwrites its content.

This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It leverages advanced techniques such as chat-based interaction and multi-task dispatching to streamline the generation of documentation pages, summaries, and metadata.

Args:
    filepath (str): The path to the directory containing files to be processed.

Returns:
    None

Raises:
    None

Note:
    This function uses os.listdir, os.path.join, os.path.isdir, os.remove, os.getsize, and os.rename from the os module. It also relies on the latest_version_substring variable for identifying files to process.

    See also: GitignoreChecker & make_fake_files, delete_fake_files for handling .gitignore file checks and temporary file management during the documentation process.
"""'''
        files = os.listdir(filepath)
        for fi in files:
            fi_d = os.path.join(filepath, fi)
            if os.path.isdir(fi_d):
                gci(fi_d)
            elif fi_d.endswith(latest_verison_substring):
                origin_name = fi_d.replace(latest_verison_substring, '.py')
                if os.path.exists(origin_name):
                    os.remove(origin_name)
                if os.path.getsize(fi_d) == 0:
                    print(f'{Fore.LIGHTRED_EX}[Deleting Temp File]: {Style.RESET_ALL}{fi_d[len(str(setting.project.target_repo)):]}, {origin_name[len(str(setting.project.target_repo)):]}')
                    os.remove(fi_d)
                else:
                    print(f'{Fore.LIGHTRED_EX}[Recovering Latest Version]: {Style.RESET_ALL}{origin_name[len(str(setting.project.target_repo)):]} <- {fi_d[len(str(setting.project.target_repo)):]}')
                    os.rename(fi_d, origin_name)
    gci(setting.project.target_repo)