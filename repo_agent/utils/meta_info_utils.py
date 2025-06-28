import itertools
import os
import git
from colorama import Fore, Style
from repo_agent.log import logger
from repo_agent.settings import SettingsManager

latest_verison_substring = "_latest_version.py"


def make_fake_files():
    """
    Creates fake files based on unstaged changes and untracked Python files.

        This method first deletes any existing fake files, then identifies
        untracked .py files and unstaged modifications to files (additions,
        modifications, deletions). It renames modified/deleted files to include a
        version substring and creates temporary files for deleted but not staged
        files.  It also skips untracked Python files.

        Args:
            None

        Returns:
            tuple: A tuple containing a dictionary of file path reflections (original
                path to latest version path) and a list of jump files (untracked .py
                files).
    """
    delete_fake_files()
    setting = SettingsManager.get_setting()
    repo = git.Repo(setting.project.target_repo)
    unstaged_changes = repo.index.diff(None)
    untracked_files = repo.untracked_files
    jump_files = []
    for file_name in untracked_files:
        if file_name.endswith(".py"):
            print(
                f"{Fore.LIGHTMAGENTA_EX}[SKIP untracked files]: {Style.RESET_ALL}{file_name}"
            )
            jump_files.append(file_name)
    for diff_file in unstaged_changes.iter_change_type("A"):
        if diff_file.a_path.endswith(latest_verison_substring):
            logger.error(
                "FAKE_FILE_IN_GIT_STATUS detected! suggest to use `delete_fake_files` and re-generate document"
            )
            exit()
        jump_files.append(diff_file.a_path)
    file_path_reflections = {}
    for diff_file in itertools.chain(
        unstaged_changes.iter_change_type("M"), unstaged_changes.iter_change_type("D")
    ):
        if diff_file.a_path.endswith(latest_verison_substring):
            logger.error(
                "FAKE_FILE_IN_GIT_STATUS detected! suggest to use `delete_fake_files` and re-generate document"
            )
            exit()
        now_file_path = diff_file.a_path
        if now_file_path.endswith(".py"):
            raw_file_content = diff_file.a_blob.data_stream.read().decode("utf-8")
            latest_file_path = now_file_path[:-3] + latest_verison_substring
            if os.path.exists(os.path.join(setting.project.target_repo, now_file_path)):
                os.rename(
                    os.path.join(setting.project.target_repo, now_file_path),
                    os.path.join(setting.project.target_repo, latest_file_path),
                )
                print(
                    f"{Fore.LIGHTMAGENTA_EX}[Save Latest Version of Code]: {Style.RESET_ALL}{now_file_path} -> {latest_file_path}"
                )
            else:
                print(
                    f"{Fore.LIGHTMAGENTA_EX}[Create Temp-File for Deleted(But not Staged) Files]: {Style.RESET_ALL}{now_file_path} -> {latest_file_path}"
                )
                try:
                    with open(
                        os.path.join(setting.project.target_repo, latest_file_path),
                        "w",
                        encoding="utf-8",
                    ) as writer:
                        pass
                except:
                    pass
            try:
                with open(
                    os.path.join(setting.project.target_repo, now_file_path),
                    "w",
                    encoding="utf-8",
                ) as writer:
                    writer.write(raw_file_content)
            except:
                pass
            file_path_reflections[now_file_path] = latest_file_path
    return (file_path_reflections, jump_files)


def delete_fake_files():
    """
    Deletes temporary or fake files created during the process.

        This method recursively searches through the target repository directory,
        identifies files ending with a specific substring (latest version indicator),
        and either deletes them if they are empty or renames them to their original
        names if they contain content. It also prints messages indicating which
        files are being deleted or recovered.

        Args:
            None

        Returns:
            None
    """
    setting = SettingsManager.get_setting()

    def gci(filepath):
        files = os.listdir(filepath)
        for fi in files:
            fi_d = os.path.join(filepath, fi)
            if os.path.isdir(fi_d):
                gci(fi_d)
            elif fi_d.endswith(latest_verison_substring):
                origin_name = fi_d.replace(latest_verison_substring, ".py")
                if os.path.exists(origin_name):
                    os.remove(origin_name)
                if os.path.getsize(fi_d) == 0:
                    print(
                        f"{Fore.LIGHTRED_EX}[Deleting Temp File]: {Style.RESET_ALL}{fi_d[len(str(setting.project.target_repo)):]}, {origin_name[len(str(setting.project.target_repo)):]}"
                    )
                    os.remove(fi_d)
                else:
                    print(
                        f"{Fore.LIGHTRED_EX}[Recovering Latest Version]: {Style.RESET_ALL}{origin_name[len(str(setting.project.target_repo)):]} <- {fi_d[len(str(setting.project.target_repo)):]}"
                    )
                    os.rename(fi_d, origin_name)

    gci(setting.project.target_repo)
