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
    allowing for easy and consistent categorization of log output.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProjectSettings(BaseSettings):
    """
    Project settings class to manage configuration for repository analysis.

    This class encapsulates all configurable parameters related to the project,
    such as repository details, documentation generation preferences, and logging options.
    """

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
        Ensures the provided input represents a recognized language, returning its standardized name.

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
        Converts a string to a `LogLevel` enum member, raising an error for invalid inputs.

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
    Represents settings for a chat completion request.

    This class encapsulates the configuration parameters needed to interact with
    a chat completion service, such as OpenAI's Chat Completions API. It provides
    attributes for specifying the model, temperature, timeout, base URL, and API key.
    """

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
            openai_base_url: The base URL for OpenAI.

        Returns:
            str: The string representation of the base URL.

        """

        return str(openai_base_url)


class Setting(BaseSettings):
    """
    Represents a configurable setting with a name, value, and description.

     This class is designed to hold configuration parameters for an application or system.
     It allows storing settings with associated descriptions for better maintainability and understanding.

    """

    project: ProjectSettings = {}
    chat_completion: ChatCompletionSettings = {}


class SettingsManager:
    """
    SettingsManager manages and provides access to application settings.

    This class acts as a central repository for configuration parameters,
    ensuring consistent access throughout the application. It utilizes a singleton
    pattern to maintain a single instance of the settings.

    Class Attributes:
    - _setting_instance

    Class Methods:
    - get_setting:
    """

    _setting_instance: Optional[Setting] = None

    @classmethod
    def get_setting(cls):
        """
        Provides access to the application’s configuration. Creates a new configuration object if one doesn't already exist, ensuring consistent settings throughout the application lifecycle.

                This method ensures that only one instance of the Setting class is created
                and returns it. If an instance doesn't exist, it creates one first.

                Parameters:
                    cls - The class itself.

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
        Configures the application with project-specific and OpenAI connection details.

        Args:
            target_repo: The path to the target repository.
            markdown_docs_name: The name of the markdown documentation file.
            hierarchy_name: The name used for hierarchy representation.
            ignore_list: A list of files or directories to ignore during processing.
            language: The programming language of the codebase.
            max_thread_count: The maximum number of threads to use for parallel processing.
            log_level: The logging level to be used.
            model: The name of the OpenAI model to use.
            temperature: The temperature setting for the OpenAI model.
            request_timeout: The request timeout in seconds for OpenAI API calls.
            openai_base_url: The base URL for the OpenAI API.
            parse_references: Whether to parse references within the documentation.

        Returns:
            None


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
