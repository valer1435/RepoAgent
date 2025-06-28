from importlib import metadata
import click
from pydantic import ValidationError
from repo_agent.doc_meta_info import DocItem, MetaInfo
from repo_agent.log import logger, set_logger_level_from_config
from repo_agent.runner import Runner, delete_fake_files
from repo_agent.settings import SettingsManager, LogLevel
from repo_agent.utils.meta_info_utils import delete_fake_files, make_fake_files

try:
    version_number = metadata.version("repoagent")
except metadata.PackageNotFoundError:
    version_number = "0.0.0"


@click.group()
@click.version_option(version_number)
def cli():
    """
    The main command-line interface for the application.

        Args:
            None

        Returns:
            None
    """
    pass


def handle_setting_error(e: ValidationError):
    """
    Handles a ValidationError by printing error messages to the console and raising a ClickException.

        Args:
            e: The ValidationError object containing validation errors.

        Returns:
            None: This method raises a click.ClickException upon completion.
    """
    for error in e.errors():
        field = error["loc"][-1]
        if error["type"] == "missing":
            message = click.style(
                f"Missing required field `{field}`. Please set the `{field}` environment variable.",
                fg="yellow",
            )
        else:
            message = click.style(error["msg"], fg="yellow")
        click.echo(message, err=True, color=True)
    raise click.ClickException(
        click.style(
            "Program terminated due to configuration errors.", fg="red", bold=True
        )
    )


@cli.command()
@click.option(
    "--model",
    "-m",
    default="gpt-4o-mini",
    show_default=True,
    help="Specifies the model to use for completion.",
    type=str,
)
@click.option(
    "--temperature",
    "-t",
    default=0.2,
    show_default=True,
    help="Sets the generation temperature for the model. Lower values make the model more deterministic.",
    type=float,
)
@click.option(
    "--request-timeout",
    "-r",
    default=60,
    show_default=True,
    help="Defines the timeout in seconds for the API request.",
    type=int,
)
@click.option(
    "--base-url",
    "-b",
    default="https://api.openai.com/v1",
    show_default=True,
    help="The base URL for the API calls.",
    type=str,
)
@click.option(
    "--target-repo-path",
    "-tp",
    default="",
    show_default=True,
    help="The file system path to the target repository. This path is used as the root for documentation generation.",
    type=click.Path(file_okay=False),
)
@click.option(
    "--hierarchy-path",
    "-hp",
    default=".project_doc_record",
    show_default=True,
    help="The name or path for the project hierarchy file, used to organize documentation structure.",
    type=str,
)
@click.option(
    "--markdown-docs-path",
    "-mdp",
    default="markdown_docs",
    show_default=True,
    help="The folder path where Markdown documentation will be stored or generated.",
    type=str,
)
@click.option(
    "--ignore-list",
    "-i",
    default="",
    help="A comma-separated list of files or directories to ignore during documentation generation.",
)
@click.option(
    "--language",
    "-l",
    default="English",
    show_default=True,
    help="The ISO 639 code or language name for the documentation. ",
    type=str,
)
@click.option("--max-thread-count", "-mtc", default=4, show_default=True)
@click.option(
    "--log-level",
    "-ll",
    default="INFO",
    show_default=True,
    help="Sets the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL) for the application. Default is INFO.",
    type=click.Choice([level.value for level in LogLevel], case_sensitive=False),
)
@click.option(
    "--print-hierarchy",
    "-pr",
    is_flag=True,
    show_default=True,
    default=False,
    help="If set, prints the hierarchy of the target repository when finished running the main task.",
)
def run(
    model,
    temperature,
    request_timeout,
    base_url,
    target_repo_path,
    hierarchy_path,
    markdown_docs_path,
    ignore_list,
    language,
    max_thread_count,
    log_level,
    print_hierarchy,
):
    """
    Runs the documentation generation process.

        Args:
            model: Specifies the model to use for completion.
            temperature: Sets the generation temperature for the model. Lower values make the model more deterministic.
            request_timeout: Defines the timeout in seconds for the API request.
            base_url: The base URL for the API calls.
            target_repo_path: The file system path to the target repository. This path is used as the root for documentation generation.
            hierarchy_path: The name or path for the project hierarchy file, used to organize documentation structure.
            markdown_docs_path: The folder path where Markdown documentation will be stored or generated.
            ignore_list: A comma-separated list of files or directories to ignore during documentation generation.
            language: The ISO 639 code or language name for the documentation.
            max_thread_count:  The maximum number of threads to use for processing.
            log_level: Sets the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL) for the application.
            print_hierarchy: If set, prints the hierarchy of the target repository when finished running the main task.

        Returns:
            None
    """
    try:
        setting = SettingsManager.initialize_with_params(
            target_repo=target_repo_path,
            hierarchy_name=hierarchy_path,
            markdown_docs_name=markdown_docs_path,
            ignore_list=[item.strip() for item in ignore_list.split(",") if item],
            language=language,
            log_level=log_level,
            model=model,
            temperature=temperature,
            request_timeout=request_timeout,
            openai_base_url=base_url,
            max_thread_count=max_thread_count,
        )
        set_logger_level_from_config(log_level=log_level)
    except ValidationError as e:
        handle_setting_error(e)
        return
    runner = Runner()
    runner.run()
    logger.success("Documentation task completed.")
    if print_hierarchy:
        runner.meta_info.target_repo_hierarchical_tree.print_recursive()
        logger.success("Hierarchy printed.")


def run_outside_cli(
    model,
    temperature,
    request_timeout,
    base_url,
    target_repo_path,
    hierarchy_path,
    markdown_docs_path,
    ignore_list,
    language,
    max_thread_count,
    log_level,
    print_hierarchy,
):
    """
    Runs the documentation generation process outside of the CLI.

        This method initializes settings, runs the documentation runner, and optionally prints the repository hierarchy.

        Args:
            model: The model to use for documentation generation.
            temperature: The temperature setting for the model.
            request_timeout: The request timeout in seconds.
            base_url: The base URL for the OpenAI API.
            target_repo_path: The path to the target repository.
            hierarchy_path: The name of the hierarchy file.
            markdown_docs_path: The path to store markdown documentation.
            ignore_list: A comma-separated list of files or directories to ignore.
            language: The programming language of the repository.
            max_thread_count: The maximum number of threads to use.
            log_level: The logging level.
            print_hierarchy: Whether to print the repository hierarchy.

        Returns:
            None.  The method either completes successfully or exits due to a settings validation error.
    """
    try:
        setting = SettingsManager.initialize_with_params(
            target_repo=target_repo_path,
            hierarchy_name=hierarchy_path,
            markdown_docs_name=markdown_docs_path,
            ignore_list=[item.strip() for item in ignore_list.split(",") if item],
            language=language,
            log_level=log_level,
            model=model,
            temperature=temperature,
            request_timeout=request_timeout,
            openai_base_url=base_url,
            max_thread_count=max_thread_count,
        )
        set_logger_level_from_config(log_level=log_level)
    except ValidationError as e:
        handle_setting_error(e)
        return
    runner = Runner()
    runner.run()
    logger.success("Documentation task completed.")
    if print_hierarchy:
        runner.meta_info.target_repo_hierarchical_tree.print_recursive()
        logger.success("Hierarchy printed.")


@cli.command()
def clean():
    """
    Cleans up fake files.

        This method calls the delete_fake_files function to remove any
        unnecessary or placeholder files and logs a success message.

        Returns:
            None
    """
    delete_fake_files()
    logger.success("Fake files have been cleaned up.")


@cli.command()
def diff():
    """
    Prints the documentation differences between the current state and the latest meta info.

        This command checks for changes in the source code that would require
        documentation updates, and displays a list of files that will be
        generated or updated. It does not support running during an active
        generation process.

        Args:
            None

        Returns:
            None
    """
    try:
        setting = SettingsManager.get_setting()
    except ValidationError as e:
        handle_setting_error(e)
        return
    runner = Runner()
    if runner.meta_info.in_generation_process:
        click.echo("This command only supports pre-check")
        raise click.Abort()
    file_path_reflections, jump_files = make_fake_files()
    new_meta_info = MetaInfo.init_meta_info(file_path_reflections, jump_files)
    new_meta_info.load_doc_from_older_meta(runner.meta_info)
    delete_fake_files()
    DocItem.check_has_task(
        new_meta_info.target_repo_hierarchical_tree,
        ignore_list=setting.project.ignore_list,
    )
    if new_meta_info.target_repo_hierarchical_tree.has_task:
        click.echo("The following docs will be generated/updated:")
        new_meta_info.target_repo_hierarchical_tree.print_recursive(
            diff_status=True, ignore_list=setting.project.ignore_list
        )
    else:
        click.echo("No docs will be generated/updated, check your source-code update")
