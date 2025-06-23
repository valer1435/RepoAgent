from importlib import metadata
import click
from pydantic import ValidationError
from repo_agent.doc_meta_info import DocItem, MetaInfo
from repo_agent.log import logger, set_logger_level_from_config
from repo_agent.runner import Runner, delete_fake_files
from repo_agent.settings import SettingsManager, LogLevel
from repo_agent.utils.meta_info_utils import delete_fake_files, make_fake_files
try:
    version_number = metadata.version('repoagent')
except metadata.PackageNotFoundError:
    version_number = '0.0.0'


@click.group()
@click.version_option(version_number)
def cli():
    """
    CLI function for the repo_agent module.
    
    This function serves as the entry point for the command-line interface of the repo_agent module. It automates the generation and management of documentation for a Git repository by integrating functionalities to detect changes, handle file operations, manage tasks, and configure settings. The tool ensures efficient and accurate documentation updates, streamlining the process for developers to maintain their documentation without manual intervention. It leverages Git to detect changes and includes a multi-task dispatch system to process documentation tasks in a multi-threaded environment, ensuring scalability and robustness.
    
    Args:
        None
    
    Returns:
        None
    
    Raises:
        None
    
    Note:
        See also: repo_agent\\__main__.py (if applicable).
    """
    pass


def handle_setting_error(e: ValidationError):
    """
    Handles and displays configuration errors from a ValidationError.
    
    This method iterates over the errors in a ValidationError, formats them into user-friendly messages, and prints them to the console. If any required field is missing, it instructs the user to set the corresponding environment variable. After displaying all errors, it raises a ClickException to terminate the program.
    
    Args:
        e (ValidationError): The ValidationError object containing the configuration errors.
    
    Returns:
        None: This method does not return any value.
    
    Raises:
        click.ClickException: If there are configuration errors, this exception is raised to terminate the program.
    
    Note:
        This method is used to handle and display errors during the initialization of settings in the `run`, `run_outside_cli`, and `diff` methods. It ensures that the user is informed about any missing or incorrect configuration settings, helping to maintain the integrity and functionality of the documentation generation process. The `repo_agent` project automates the generation and management of documentation for a Git repository, and this method plays a crucial role in ensuring that the settings are correctly configured for the automated processes.
    """
    for error in e.errors():
        field = error['loc'][-1]
        if error['type'] == 'missing':
            message = click.style(
                f'Missing required field `{field}`. Please set the `{field}` environment variable.'
                , fg='yellow')
        else:
            message = click.style(error['msg'], fg='yellow')
        click.echo(message, err=True, color=True)
    raise click.ClickException(click.style(
        'Program terminated due to configuration errors.', fg='red', bold=True)
        )


@cli.command()
@click.option('--model', '-m', default='gpt-4o-mini', show_default=True,
    help='Specifies the model to use for completion.', type=str)
@click.option('--temperature', '-t', default=0.2, show_default=True, help=
    'Sets the generation temperature for the model. Lower values make the model more deterministic.'
    , type=float)
@click.option('--request-timeout', '-r', default=60, show_default=True,
    help='Defines the timeout in seconds for the API request.', type=int)
@click.option('--base-url', '-b', default='https://api.openai.com/v1',
    show_default=True, help='The base URL for the API calls.', type=str)
@click.option('--target-repo-path', '-tp', default='', show_default=True,
    help=
    'The file system path to the target repository. This path is used as the root for documentation generation.'
    , type=click.Path(file_okay=False))
@click.option('--hierarchy-path', '-hp', default='.project_doc_record',
    show_default=True, help=
    'The name or path for the project hierarchy file, used to organize documentation structure.'
    , type=str)
@click.option('--markdown-docs-path', '-mdp', default='markdown_docs',
    show_default=True, help=
    'The folder path where Markdown documentation will be stored or generated.'
    , type=str)
@click.option('--ignore-list', '-i', default='', help=
    'A comma-separated list of files or directories to ignore during documentation generation.'
    )
@click.option('--language', '-l', default='English', show_default=True,
    help='The ISO 639 code or language name for the documentation. ', type=str)
@click.option('--max-thread-count', '-mtc', default=4, show_default=True)
@click.option('--log-level', '-ll', default='INFO', show_default=True, help
    =
    'Sets the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL) for the application. Default is INFO.'
    , type=click.Choice([level.value for level in LogLevel], case_sensitive
    =False))
@click.option('--print-hierarchy', '-pr', is_flag=True, show_default=True,
    default=False, help=
    'If set, prints the hierarchy of the target repository when finished running the main task.'
    )
def run(model, temperature, request_timeout, base_url, target_repo_path,
    hierarchy_path, markdown_docs_path, ignore_list, language,
    max_thread_count, log_level, print_hierarchy):
    """
    Runs the documentation generation process with specified settings.
    
    This method initializes the settings, sets the logger level, and runs the documentation generation process. If the `print_hierarchy` flag is set, it prints the hierarchical tree of the target repository. The `repo_agent` project automates the generation and management of documentation for a Git repository, integrating functionalities to detect changes, handle file operations, manage project settings, and generate summaries for modules and directories. This automation helps maintain high-quality, accurate, and consistent documentation, which is essential for project collaboration, maintenance, and understanding.
    
    Args:
        model (str): The model to use for documentation generation.
        temperature (float): The temperature setting for the model.
        request_timeout (int): The timeout for API requests in seconds.
        base_url (str): The base URL for the API.
        target_repo_path (str): The path to the target repository.
        hierarchy_path (str): The path to the hierarchy file.
        markdown_docs_path (str): The path to the markdown documents directory.
        ignore_list (str): A comma-separated list of items to ignore.
        language (str): The language for the documentation.
        max_thread_count (int): The maximum number of threads to use.
        log_level (str): The log level for the application.
        print_hierarchy (bool): Whether to print the hierarchical tree of the target repository.
    
    Returns:
        None
    
    Raises:
        ValidationError: If the settings initialization fails due to invalid parameters.
    
    Note:
        This method is the entry point for the documentation generation process and handles initialization, execution, and logging. It is particularly useful for large repositories where manual tracking and updating of documentation can be time-consuming and error-prone. The tool leverages Git's capabilities to track changes and manage files, ensuring efficient and accurate documentation updates. The multi-task dispatch system allows for scalable and robust processing of documentation tasks in a multi-threaded environment.
    """
    try:
        setting = SettingsManager.initialize_with_params(target_repo=
            target_repo_path, hierarchy_name=hierarchy_path,
            markdown_docs_name=markdown_docs_path, ignore_list=[item.strip(
            ) for item in ignore_list.split(',') if item], language=
            language, log_level=log_level, model=model, temperature=
            temperature, request_timeout=request_timeout, openai_base_url=
            base_url, max_thread_count=max_thread_count)
        set_logger_level_from_config(log_level=log_level)
    except ValidationError as e:
        handle_setting_error(e)
        return
    runner = Runner()
    runner.run()
    logger.success('Documentation task completed.')
    if print_hierarchy:
        runner.meta_info.target_repo_hierarchical_tree.print_recursive()
        logger.success('Hierarchy printed.')


def run_outside_cli(model, temperature, request_timeout, base_url,
    target_repo_path, hierarchy_path, markdown_docs_path, ignore_list,
    language, max_thread_count, log_level, print_hierarchy):
    """
    Runs the documentation generation process outside of the command-line interface (CLI).
    
    This method initializes the project settings, sets the logger level, and runs the documentation generation process. If the `print_hierarchy` flag is set, it prints the hierarchical structure of the documentation items.
    
    Args:
        model (str): The OpenAI model to use for chat completion.
        temperature (float): The sampling temperature for the model.
        request_timeout (int): The timeout for API requests in seconds.
        base_url (str): The base URL for the OpenAI API.
        target_repo_path (Path): The path to the target repository.
        hierarchy_path (str): The name of the hierarchy directory.
        markdown_docs_path (str): The name of the markdown documents directory.
        ignore_list (str): A comma-separated list of files or directories to ignore.
        language (str): The language to use. Must be a valid ISO 639 code or language name.
        max_thread_count (int): The maximum number of threads to use.
        log_level (str): The log level for the application. Must be one of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
        print_hierarchy (bool): Whether to print the hierarchical structure of the documentation items.
    
    Returns:
        None
    
    Raises:
        ValidationError: If the provided settings are invalid.
        ValueError: If the log level input is invalid. The input must be one of the valid log levels: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
        ValueError: If the language input is invalid. The input must be a valid ISO 639 code or language name.
    
    Note:
        - The method uses the `SettingsManager` to initialize project settings.
        - It uses the `set_logger_level_from_config` function to set the logger level.
        - It uses the `Runner` class to manage and generate the documentation.
        - If `print_hierarchy` is set, it prints the hierarchical structure of the documentation items using the `print_recursive` method.
    """
    try:
        setting = SettingsManager.initialize_with_params(target_repo=
            target_repo_path, hierarchy_name=hierarchy_path,
            markdown_docs_name=markdown_docs_path, ignore_list=[item.strip(
            ) for item in ignore_list.split(',') if item], language=
            language, log_level=log_level, model=model, temperature=
            temperature, request_timeout=request_timeout, openai_base_url=
            base_url, max_thread_count=max_thread_count)
        set_logger_level_from_config(log_level=log_level)
    except ValidationError as e:
        handle_setting_error(e)
        return
    runner = Runner()
    runner.run()
    logger.success('Documentation task completed.')
    if print_hierarchy:
        runner.meta_info.target_repo_hierarchical_tree.print_recursive()
        logger.success('Hierarchy printed.')


@cli.command()
def clean():
    """
    Cleans up fake files.
    
    This method deletes fake files and logs a success message. It is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository. The tool integrates various functionalities to detect changes, handle file operations, manage tasks, and configure settings, all while ensuring efficient and accurate documentation updates. The method is particularly useful for managing untracked and modified content in the repository, helping to keep the repository clean and organized.
    
    Args:
        None
    
    Returns:
        None
    
    Raises:
        None
    
    Note:
        This method leverages Git's capabilities to track changes and manage files, ensuring that the repository remains clean and organized. It is an essential part of the `repo_agent` project, which aims to streamline the documentation process for software repositories by automating the detection of changes, generation of documentation, and management of documentation items. The project includes a multi-task dispatch system to efficiently process documentation tasks in a multi-threaded environment, ensuring that the documentation generation process is both scalable and robust.
    """
    delete_fake_files()
    logger.success('Fake files have been cleaned up.')


@cli.command()
def diff():
    """
    Compares the current state of the repository with a previous state to identify changes in documentation.
    
    This method checks the settings, ensures the command is not run during the generation process, and then creates a fake file structure to generate new meta information. It compares this new meta information with the existing one to determine which documentation items need to be generated or updated. Finally, it prints the changes and deletes the fake files.
    
    Args:
        None
    
    Returns:
        None
    
    Raises:
        ValidationError: If the settings are invalid.
        click.Abort: If the command is run during the generation process.
    
    Note:
        This method is designed to be used as a pre-check before the actual documentation generation process. It integrates with the project's functionalities to detect changes, handle file operations, and manage project settings, ensuring that the documentation is up-to-date and accurate. The `repo_agent` project automates the generation and management of documentation for a Git repository, streamlining the documentation process and reducing manual effort. It leverages Git's capabilities to track changes and manage files, and includes a multi-task dispatch system to efficiently process documentation tasks in a multi-threaded environment.
    """
    try:
        setting = SettingsManager.get_setting()
    except ValidationError as e:
        handle_setting_error(e)
        return
    runner = Runner()
    if runner.meta_info.in_generation_process:
        click.echo('This command only supports pre-check')
        raise click.Abort()
    file_path_reflections, jump_files = make_fake_files()
    new_meta_info = MetaInfo.init_meta_info(file_path_reflections, jump_files)
    new_meta_info.load_doc_from_older_meta(runner.meta_info)
    delete_fake_files()
    DocItem.check_has_task(new_meta_info.target_repo_hierarchical_tree,
        ignore_list=setting.project.ignore_list)
    if new_meta_info.target_repo_hierarchical_tree.has_task:
        click.echo('The following docs will be generated/updated:')
        new_meta_info.target_repo_hierarchical_tree.print_recursive(diff_status
            =True, ignore_list=setting.project.ignore_list)
    else:
        click.echo(
            'No docs will be generated/updated, check your source-code update')
