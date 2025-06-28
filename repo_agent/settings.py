from enum import StrEnum
from typing import Optional
from iso639 import Language, LanguageNotFoundError
from pydantic import (
    DirectoryPath,
    Field,
    HttpUrl,
    PositiveFloat,
    PositiveInt,
    SecretStr,
    field_validator,
)
from pydantic_settings import BaseSettings
from pathlib import Path


class LogLevel(StrEnum):
    """
    Represents different log levels for categorizing log messages.

        This class provides a set of constants representing standard log levels,
        allowing for consistent and organized logging in applications.

        Attributes:
            DEBUG:  The most detailed level, typically used during development.
            INFO:   General information about the application's operation.
            WARNING: Indicates potential issues or problems.
            ERROR:   Signals an error condition that has occurred.
            CRITICAL: Represents a severe error that may lead to application failure.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProjectSettings(BaseSettings):
    """
    Stores and validates settings for a project analysis."""

    target_repo: DirectoryPath = ""
    hierarchy_name: str = ".project_doc_record"
    markdown_docs_name: str = "markdown_docs"
    ignore_list: list[str] = []
    language: str = "English"
    max_thread_count: PositiveInt = 4
    log_level: LogLevel = LogLevel.INFO
    main_idea: Optional[str] = None
    parse_references: bool = True

    @field_validator("language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        """
        Ensures the provided language code is valid, returning the corresponding language name or raising an error for invalid inputs.

            Args:
                v: The language code or name to validate.

            Returns:
                str: The validated language name.

            Raises:
                ValueError: If the input is not a valid ISO 639 code or language name.
        """

        try:
            language_name = Language.match(v).name
            return language_name
        except LanguageNotFoundError:
            raise ValueError(
                "Invalid language input. Please enter a valid ISO 639 code or language name."
            )

    @field_validator("log_level", mode="before")
    @classmethod
    def set_log_level(cls, v: str) -> LogLevel:
        """
        Ensures the log level is a valid value, converting string inputs to uppercase for case-insensitive matching. Raises an error if an invalid log level is provided.

            Args:
                v: The log level string to set.

            Returns:
                LogLevel: The LogLevel enum member corresponding to the input string.

            Raises:
                ValueError: If the provided log level string is invalid.
        """

        if isinstance(v, str):
            v = v.upper()
        if v in LogLevel._value2member_map_:
            return LogLevel(v)
        raise ValueError(f"Invalid log level: {v}")


class ChatCompletionSettings(BaseSettings):
    """
    Settings for configuring chat completion requests."""

    model: str = "gpt-4o-mini"
    temperature: PositiveFloat = 0.2
    request_timeout: PositiveInt = 180
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: SecretStr = Field(..., exclude=True)

    @field_validator("openai_base_url", mode="before")
    @classmethod
    def convert_base_url_to_str(cls, openai_base_url: HttpUrl) -> str:
        """
        Ensures the OpenAI base URL is handled as a string.

            Args:
                openai_base_url: The OpenAI base URL to convert.

            Returns:
                str: The string representation of the OpenAI base URL.
        """

        return str(openai_base_url)


class Setting(BaseSettings):
    """
    Represents a configuration setting with project and chat completion details.

        Attributes:
            project: The name of the project associated with this setting.
            chat_completion:  A flag indicating whether chat completion is enabled for this setting.
    """

    project: ProjectSettings = {}
    chat_completion: ChatCompletionSettings = {}


class SettingsManager:
    """
    Manages singleton instance of settings for repository analysis."""

    _setting_instance: Optional[Setting] = None

    @classmethod
    def get_setting(cls):
        """
        Provides access to a single, shared instance of the configuration object.

            This method ensures that only one instance of the Setting class is created,
            returning the existing instance if it already exists.

            Args:
                cls: The class itself.

            Returns:
                Setting: The singleton instance of the Setting class.
        """

        if cls._setting_instance is None:
            cls._setting_instance = Setting()
        return cls._setting_instance

    @classmethod
    def initialize_with_params(
        cls,
        target_repo: Path,
        markdown_docs_name: str,
        hierarchy_name: str,
        ignore_list: list[str],
        language: str,
        max_thread_count: int,
        log_level: str,
        model: str,
        temperature: float,
        request_timeout: int,
        openai_base_url: str,
        parse_references: bool = True,
    ):
        """
        Configures the agent with project-specific details like repository path, documentation file names, and code analysis parameters, alongside chat engine settings for generating summaries.

            Args:
                target_repo: The path to the target repository.
                markdown_docs_name: The name of the markdown documentation file.
                hierarchy_name: The name used for hierarchy representation.
                ignore_list: A list of files or directories to ignore during processing.
                language: The programming language of the repository.
                max_thread_count: The maximum number of threads to use for parallel processing.
                log_level: The logging level to be used.
                model: The name of the OpenAI model to use.
                temperature: The temperature setting for the OpenAI model.
                request_timeout: The request timeout in seconds for OpenAI API calls.
                openai_base_url: The base URL for the OpenAI API.
                parse_references: Whether to parse references within the documentation.

            Returns:
                None: This method modifies class-level state and does not return a value.
        """

        project_settings = ProjectSettings(
            target_repo=target_repo,
            hierarchy_name=hierarchy_name,
            markdown_docs_name=markdown_docs_name,
            ignore_list=ignore_list,
            language=language,
            max_thread_count=max_thread_count,
            log_level=LogLevel(log_level),
            parse_references=parse_references,
        )
        chat_completion_settings = ChatCompletionSettings(
            model=model,
            temperature=temperature,
            request_timeout=request_timeout,
            openai_base_url=openai_base_url,
        )
        cls._setting_instance = Setting(
            project=project_settings, chat_completion=chat_completion_settings
        )


if __name__ == "__main__":
    setting = SettingsManager.get_setting()
    print(setting.model_dump())
