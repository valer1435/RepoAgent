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
    '''"""Repository-level Code Documentation Generation Framework.

This function serves as the command line interface (CLI) for the repository-level code documentation generation framework. It orchestrates the documentation generation process by interacting with other components of the framework, leveraging advanced techniques such as change detection, interactive communication, and multi-task dispatching to automate the creation of comprehensive documentation for a given codebase.

Args:
    None

Returns:
    None

Raises:
    ValueError: If there's an issue with the repository structure or configuration settings.

Note:
    This function does not accept any arguments and does not return any value. Instead, it initiates the documentation generation process. It interacts with components like ChangeDetector for monitoring changes in the repository, ChatEngine for facilitating interactive communication, and various task managers for efficient resource allocation and task execution.

    For more details on how to use this function, refer to the project's README or the specific CLI usage instructions provided in the repository. The framework supports tasks such as generating documentation pages, summaries, and metadata, and it can be invoked through the 'cli' module using the 'run' method. Interactive chat sessions with the repository are enabled via the 'chat_with_repo' function, while external execution of the documentation generation process is facilitated by the 'run_outside_cli' method.

    The framework's configuration settings, including log levels and project-specific parameters, are managed by classes such as ProjectSettings and SettingsManager. Temporary file management during the documentation process is handled by GitignoreChecker and related utility functions.
"""'''
    pass

def handle_setting_error(e: ValidationError):
    """Handles configuration errors for settings within the Repository Documentation Generator project.

This function processes validation errors related to the program's settings, ensuring clear communication of issues to the user before terminating the program gracefully due to configuration problems. It is a crucial component of the multi-task dispatch system, managing logging and error handling for seamless operation.

Args:
    e (ValidationError): A validation error object containing details about the configuration issues encountered during settings validation. This could be triggered by various parts of the codebase such as `run`, `run_outside_cli`, `diff`, or `chat_with_repo`.

Returns:
    None

Raises:
    click.ClickException: An exception raised when terminating the program due to configuration errors, providing a red, bold message to indicate critical issues.

Note:
    This function is designed to handle any validation errors related to settings, distinguishing between missing fields and other types of errors. For missing fields, it provides a detailed message indicating which field is required and how to resolve the issue. For other errors, it displays the error message in yellow for user awareness. After displaying all errors, it raises a ClickException to terminate the program gracefully due to configuration issues. This function plays a pivotal role in maintaining the integrity of the Repository Documentation Generator project by ensuring that any configuration issues are reported clearly to the user before exiting the program."""
    for error in e.errors():
        field = error['loc'][-1]
        if error['type'] == 'missing':
            message = click.style(f'Missing required field `{field}`. Please set the `{field}` environment variable.', fg='yellow')
        else:
            message = click.style(error['msg'], fg='yellow')
        click.echo(message, err=True, color=True)
    raise click.ClickException(click.style('Program terminated due to configuration errors.', fg='red', bold=True))

@cli.command()
@click.option('--model', '-m', default='gpt-4o-mini', show_default=True, help='Specifies the model to use for completion.', type=str)
@click.option('--temperature', '-t', default=0.2, show_default=True, help='Sets the generation temperature for the model. Lower values make the model more deterministic.', type=float)
@click.option('--request-timeout', '-r', default=60, show_default=True, help='Defines the timeout in seconds for the API request.', type=int)
@click.option('--base-url', '-b', default='https://api.openai.com/v1', show_default=True, help='The base URL for the API calls.', type=str)
@click.option('--target-repo-path', '-tp', default='', show_default=True, help='The file system path to the target repository. This path is used as the root for documentation generation.', type=click.Path(file_okay=False))
@click.option('--hierarchy-path', '-hp', default='.project_doc_record', show_default=True, help='The name or path for the project hierarchy file, used to organize documentation structure.', type=str)
@click.option('--markdown-docs-path', '-mdp', default='markdown_docs', show_default=True, help='The folder path where Markdown documentation will be stored or generated.', type=str)
@click.option('--ignore-list', '-i', default='', help='A comma-separated list of files or directories to ignore during documentation generation.')
@click.option('--language', '-l', default='English', show_default=True, help='The ISO 639 code or language name for the documentation. ', type=str)
@click.option('--max-thread-count', '-mtc', default=4, show_default=True)
@click.option('--log-level', '-ll', default='INFO', show_default=True, help='Sets the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL) for the application. Default is INFO.', type=click.Choice([level.value for level in LogLevel], case_sensitive=False))
@click.option('--print-hierarchy', '-pr', is_flag=True, show_default=True, default=False, help='If set, prints the hierarchy of the target repository when finished running the main task.')
def run(model, temperature, request_timeout, base_url, target_repo_path, hierarchy_path, markdown_docs_path, ignore_list, language, max_thread_count, log_level, print_hierarchy):
    """'''
Runs the repository documentation generation process with specified parameters.

This function initializes settings using `SettingsManager`, validates them, and then orchestrates the documentation task. It leverages various components of the Repository Documentation Generator, including `ChangeDetector` for monitoring repository changes, `ChatEngine` for interactive communication, and multi-task dispatching via `TaskManager` and `worker`.

Args:
    model (str): The AI model to use for tasks. Defaults to 'default_model'.
    temperature (float): Controls randomness in the model's output. Ranges from 0 to 1.
    request_timeout (int): Timeout for API requests in seconds.
    base_url (str): Base URL for the AI service.
    target_repo_path (str): Path to the target repository.
    hierarchy_path (str): Path to the hierarchy file.
    markdown_docs_path (str): Path to the markdown documentation file.
    ignore_list (list of str): List of items to ignore during processing, separated by commas.
    language (str): The programming language of the codebase.
    max_thread_count (int): Maximum number of threads for concurrent tasks.
    log_level (str): Log level for the application ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
    print_hierarchy (bool): Whether to print the repository hierarchy after completion.

Returns:
    None

Raises:
    ValidationError: If any of the provided settings are invalid.

Note:
    This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It utilizes advanced techniques such as chat-based interaction and multi-task dispatching to streamline the generation of documentation pages, summaries, and metadata.

    See also: `SettingsManager` for details on setting initialization and validation.
'''"""
    try:
        setting = SettingsManager.initialize_with_params(target_repo=target_repo_path, hierarchy_name=hierarchy_path, markdown_docs_name=markdown_docs_path, ignore_list=[item.strip() for item in ignore_list.split(',') if item], language=language, log_level=log_level, model=model, temperature=temperature, request_timeout=request_timeout, openai_base_url=base_url, max_thread_count=max_thread_count)
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

def run_outside_cli(model, temperature, request_timeout, base_url, target_repo_path, hierarchy_path, markdown_docs_path, ignore_list, language, max_thread_count, log_level, print_hierarchy):
    '''"""Run the documentation generation task outside of CLI environment.

This function initiates the documentation generation process using specified parameters, bypassing the command-line interface. It leverages the Repository Documentation Generator's capabilities to automate the creation of documentation pages, summaries, and metadata for software projects. The process involves monitoring repository changes, facilitating interactive communication with the repository, managing various types of edges and documentation items, handling metadata and file management tasks, and implementing a multi-task dispatch system for efficient resource allocation.

Args:
    model (str): The AI model to be used for generating documentation. Defaults to 'text-davinci-003'.
    temperature (float): A parameter controlling randomness in the model's output. Ranges from 0 to 1, with lower values resulting in more deterministic and focused outputs.
    request_timeout (int): The maximum time to wait for a response from the API.
    base_url (str): The base URL of the OpenAI API. Defaults to 'https://api.openai.com/v1'.
    target_repo_path (str): The path to the target repository, which should be compatible with Git.
    hierarchy_path (str): The path to the hierarchy file defining the structure of the repository.
    markdown_docs_path (str): The path where generated markdown documentation files will be saved.
    ignore_list (list[str]): A list of items to be ignored during processing, such as specific directories or files.
    language (str): The programming language of the codebase, influencing the generation of accurate code-specific documentation.
    max_thread_count (int): The maximum number of threads to use for parallel processing tasks.
    log_level (str): The level of detail in logs, which can be set to 'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'.
    print_hierarchy (bool): Whether to print the hierarchical structure of the repository during execution. Defaults to False.

Returns:
    None

Raises:
    ValidationError: If any of the provided parameters are invalid, such as incorrect data types or out-of-range values.

Note:
    This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate documentation processes for software projects. It utilizes advanced techniques like chat-based interaction and multi-task dispatching to streamline documentation generation.

    See also: `SettingsManager` for details on setting initialization and validation.
"""'''
    try:
        setting = SettingsManager.initialize_with_params(target_repo=target_repo_path, hierarchy_name=hierarchy_path, markdown_docs_name=markdown_docs_path, ignore_list=[item.strip() for item in ignore_list.split(',') if item], language=language, log_level=log_level, model=model, temperature=temperature, request_timeout=request_timeout, openai_base_url=base_url, max_thread_count=max_thread_count)
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
    """[Short one-line description]: This function cleans up temporary files generated during the documentation process, ensuring only genuine project files remain.

[Longer description if needed]: The `clean` function is a critical component of the Repository Documentation Generator. It systematically removes artificial or transient files created during the documentation generation phase. By doing so, it maintains the integrity and relevance of the project directory, ensuring that only essential, accurate files persist. This function operates independently, without requiring any input parameters or producing any output values.

Args:  
    None: The `clean` function does not accept any arguments. It autonomously identifies and removes unnecessary files based on predefined criteria.

Returns:  
    None: Upon completion, this function does not return any value. Its purpose is to modify the project directory by deleting specified files.

Raises:  
    None: Under normal operation, the `clean` function does not raise exceptions. Any potential errors during execution are managed internally and may result in logging relevant messages.

Note:  
    See also: The `delete_fake_files` method (located in the same module) for detailed insights into how individual files are identified and deleted. This method forms a crucial part of the overall cleanup process, working in conjunction with the `clean` function to ensure comprehensive file management within the documentation generation workflow.
"""
    delete_fake_files()
    logger.success('Fake files have been cleaned up.')

@cli.command()
def diff():
    '''"""Check for changes and print which documents need updating or generation.

This function, part of the Repository Documentation Generator, is responsible for identifying documentation items that require updates or creation based on detected changes within the repository. It achieves this by comparing the current state of the project with its previous state, as stored in older metadata.

Args:
    None - This function does not accept any arguments.

Returns:
    None - Instead of returning a value, this function prints information to the console, detailing which documents need updating or generating.

Raises:
    ValidationError: If there is an issue fetching or validating settings using the SettingsManager. This exception is caught and handled within the function.

Note:
    This function is integral to the ChangeDetector component of the Repository Documentation Generator. It relies on several other components and methods, including `SettingsManager`, `Runner`, `MetaInfo`, and `DocItem`. The behavior of this function is influenced by configurations specified in the project's settings.

    See also:
        - `SettingsManager.get_setting()` for fetching project settings.
        - `Runner` class for managing execution processes.
        - `MetaInfo.init_meta_info()` and `MetaInfo.load_doc_from_older_meta()` for initializing and loading metadata respectively.
        - `DocItem.check_has_task()` for checking if documents have tasks associated with them.
"""'''
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
    DocItem.check_has_task(new_meta_info.target_repo_hierarchical_tree, ignore_list=setting.project.ignore_list)
    if new_meta_info.target_repo_hierarchical_tree.has_task:
        click.echo('The following docs will be generated/updated:')
        new_meta_info.target_repo_hierarchical_tree.print_recursive(diff_status=True, ignore_list=setting.project.ignore_list)
    else:
        click.echo('No docs will be generated/updated, check your source-code update')

@cli.command()
def chat_with_repo():
    """'''
Initiates an interactive chat session with the repository for documentation purposes.

This function establishes a conversational interface with the repository to facilitate the generation of documentation pages, summaries, and metadata. It leverages the `SettingsManager` to fetch and validate settings, ensuring that the documentation process is tailored to the specific project requirements.

Args:
    None

Returns:
    None

Raises:
    ValidationError: If the repository settings are invalid. This exception is caught and handled by the `handle_setting_error` function, ensuring the smooth operation of the chat session.

Note:
    This function is a part of the Repository Documentation Generator, an automated tool designed to simplify and streamline the documentation process for software projects. It utilizes advanced features such as the `ChatEngine` for interactive communication with the repository and the `ChangeDetector` for monitoring changes that necessitate updates or generation of new documentation items.

    The function relies on the `main()` function from `repo_agent.chat_with_repo` to establish the chat session, enabling users to request specific documentation through natural language queries. It is crucial to have valid settings in place for accurate and efficient operation.

See also:
    For a comprehensive overview of the Repository Documentation Generator's features and functionalities, refer to the project documentation.
'''"""
    try:
        setting = SettingsManager.get_setting()
    except ValidationError as e:
        handle_setting_error(e)
        return
    from repo_agent.chat_with_repo import main
    main()
if __name__ == '__main__':
    cli()