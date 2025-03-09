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
    """Automates the generation of repository-level documentation using LLMs.

The Repository Agent framework leverages large language models (LLMs) to automatically document Python projects at the repository level, including code analysis, change detection, interactive chat sessions for querying specific parts of the codebase, and task management for efficient concurrent operations.

Args:
    None

Returns:
    None

Raises:
    None

Examples:
    To generate documentation for a project, run the following command from the root directory of your repository:
    
    
    repo_agent cli --generate
    

Notes:
    See also: The implementation details can be found in the `repo_agent/main.py` file.
"""
    pass

def handle_setting_error(e: ValidationError):
    """Handle configuration errors for settings during the initialization process.

This function processes validation errors related to settings and terminates the program by raising a ClickException with a colored message indicating the nature of the error, such as missing fields or other types of validation issues. This ensures that users are promptly informed about any misconfigurations in their setup.

Args:
    e (ValidationError): The validation error raised during setting initialization.

Raises:
    click.ClickException: Raised to terminate the program due to configuration errors, displaying a colored message.

Notes:
    Utilizes Click's styling functions to output colored messages for better visibility and user experience.
"""
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
    """Run the program with the specified parameters.

The Repository Agent framework generates comprehensive documentation for Python projects by analyzing code, detecting changes, and summarizing repository contents using LLMs.

Args:
    model (str): The name of the language model to use.
    temperature (float): The temperature value for the model's output. Higher values increase randomness.
    request_timeout (int): Timeout duration in seconds for API requests.
    base_url (str): Base URL for API requests.
    target_repo_path (str): Path to the target repository.
    hierarchy_path (str): Path to the hierarchy file that defines the structure of the documentation.
    markdown_docs_path (str): Path to the directory containing Markdown documentation files.
    ignore_list (str): A comma-separated list of items to be ignored during processing, with optional whitespace around commas.
    language (str): The programming language used in the repository.
    max_thread_count (int): Maximum number of threads allowed for concurrent operations.
    log_level (str): Logging level for output verbosity.
    print_hierarchy (bool): Whether to print the hierarchy after completion. Defaults to False.

Returns:
    None

Raises:
    ValidationError: If there is an issue with settings validation.

Note:
    See also: SettingsManager.initialize_with_params, set_logger_level_from_config
"""
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
    """Run the program with specified parameters.

The Repository Agent is an LLM-Powered framework designed to generate comprehensive documentation for Python projects at the repository level. It automates the process of creating and updating documentation by analyzing code, identifying changes, and summarizing module contents.

Args:
    model (str): The name of the language model.
    temperature (float): The sampling temperature for the model.
    request_timeout (int): Timeout in seconds for API requests.
    base_url (str): Base URL for the API endpoint.
    target_repo_path (str): Path to the target repository.
    hierarchy_path (str): Path to the hierarchy file.
    markdown_docs_path (str): Path to the Markdown documentation file.
    ignore_list (str): Comma-separated list of items to ignore, e.g., "item1,item2".
    language (str): The programming language used in the repository.
    max_thread_count (int): Maximum number of threads for concurrent operations.
    log_level (str): Logging level for the application.
    print_hierarchy (bool): Whether to print the hierarchy after completion.

Returns:
    None

Raises:
    ValidationError: If settings validation fails.

Note:
    See also: SettingsManager.initialize_with_params, set_logger_level_from_config
"""
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
    """Clean up fake files generated during the documentation process.

This function removes temporary files created by the Repository Agent's documentation generation process and logs the cleanup action to ensure that the repository remains free of unnecessary artifacts.

Args:
    None

Returns:
    None

Raises:
    None

Examples:
    >>> clean()
    [Logs: "Fake files have been cleaned up."]

Note:
    See also: delete_fake_files() (if applicable).
"""
    delete_fake_files()
    logger.success('Fake files have been cleaned up.')

@cli.command()
def diff():
    """Check for changes and determine which documents need to be updated or generated.

This function evaluates the current state of the repository against previous metadata to identify tasks that require generating or updating documentation. It leverages settings from a `SettingsManager` and processes hierarchical tree information to pinpoint necessary actions.

Args:  
    None

Returns:  
    None  

Raises:  
    click.Abort: If the command is not in generation process mode.
    ValidationError: If there is an issue with fetching or validating settings.

Notes:  
    See also: MetaInfo, DocItem, Runner
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
    DocItem.check_has_task(new_meta_info.target_repo_hierarchical_tree, ignore_list=setting.project.ignore_list)
    if new_meta_info.target_repo_hierarchical_tree.has_task:
        click.echo('The following docs will be generated/updated:')
        new_meta_info.target_repo_hierarchical_tree.print_recursive(diff_status=True, ignore_list=setting.project.ignore_list)
    else:
        click.echo('No docs will be generated/updated, check your source-code update')

@cli.command()
def chat_with_repo():
    """Start an interactive chat session with the repository.

This function initializes an interactive session where users can query and generate documentation for specific parts of the codebase using a language model-powered framework. It fetches and validates settings using the SettingsManager, handling any validation errors that occur during this process.

Args:
    None

Returns:
    None

Raises:
    ValidationError: If the settings are invalid.

Note:
    See also: handle_setting_error (for handling configuration errors).
"""
    try:
        setting = SettingsManager.get_setting()
    except ValidationError as e:
        handle_setting_error(e)
        return
    from repo_agent.chat_with_repo import main
    main()
if __name__ == '__main__':
    cli()