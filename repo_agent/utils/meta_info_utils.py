import itertools
import os
import git
from colorama import Fore, Style
from repo_agent.log import logger
from repo_agent.settings import SettingsManager
latest_verison_substring = '_latest_version.py'

def make_fake_files():
    """Generate fake files for testing purposes.

This function creates placeholder files within specified directories to simulate the project structure for testing documentation generation processes.

Args:  
    directory_path (str): The path of the directory where fake files should be created.  
    num_files (int, optional): The number of fake files to create in each subdirectory. Defaults to 10.  

Returns:  
    None

Raises:  
    ValueError: If `num_files` is less than or equal to zero.

Note:  
    This function does not return any value but creates a specified number of placeholder files within the given directory and its subdirectories.
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
    """Deletes fake files created for testing purposes.

This function removes temporary or placeholder files that were generated during the testing phase of the documentation generation process.

Args:  
    None  

Returns:  
    None  

Raises:  
    OSError: If an error occurs while deleting the files.  

Note:  
    This function is typically used in conjunction with `make_fake_files` to clean up after tests or demonstrations.
"""
    setting = SettingsManager.get_setting()

    def gci(filepath):
        """Removes fake files from the specified directory.

This function recursively traverses the given filepath and processes each file or subdirectory. If a file ends with `latest_version_substring`, it checks for an original Python file without this substring. It either deletes or renames the file based on its size and existence of the original file.

Args:
    filepath (str): The directory path to traverse and process files from.

Returns:
    None

Raises:
    ValueError: If `latest_version_substring` is not defined in the settings.
    
Note:
    See also: `setting.project.target_repo` for context on relative paths.
"""
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