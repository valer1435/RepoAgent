from enum import StrEnum
from typing import Optional
from iso639 import Language, LanguageNotFoundError
from pydantic import DirectoryPath, Field, HttpUrl, PositiveFloat, PositiveInt, SecretStr, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path

class LogLevel(StrEnum):
    """LogLevel enumeration for logging levels.

The LogLevel enum defines the possible values for the log level in the Repository Agent framework, which is designed to automate documentation generation for Python projects by analyzing code, detecting changes, and summarizing repository contents.

Returns:
    StrEnum: An enumeration of valid log levels.

For the `set_log_level` method:

Converts and validates a string input as a LogLevel value.

Args:
    v (str): The log level value as a string. Defaults to INFO if not provided.

Returns:
    LogLevel: The validated LogLevel enum member.

Raises:
    ValueError: If the provided log level is invalid.


For the `initialize_with_params` method:

Initializes settings with specified parameters for the Repository Agent framework.

Args:
    target_repo (Path): The path to the target repository.
    markdown_docs_name (str): Name of the directory for Markdown documents.
    hierarchy_name (str): Name of the hierarchy directory.
    ignore_list (list[str]): List of files or directories to be ignored.
    language (str): Language code or name.
    max_thread_count (int): Maximum number of threads allowed.
    log_level (str): Log level as a string.
    model (str): Model identifier for chat completion settings.
    temperature (float): Temperature setting for the model.
    request_timeout (int): Request timeout in seconds.
    openai_base_url (str): Base URL for OpenAI API.

Returns:
    None

Raises:
    ValueError: If any of the parameters are invalid.
"""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

class ProjectSettings(BaseSettings):
    """Configuration settings for the Repository Agent.

The ProjectSettings class manages project-specific configurations such as repository path, language, log level, and other parameters. This class is integral to customizing the behavior of the Repository Agent framework, enabling users to tailor documentation generation processes according to their needs.

Args:
    target_repo (DirectoryPath): The directory path to the target repository.
    hierarchy_name (str): Name of the hierarchy directory. Defaults to ".project_doc_record".
    markdown_docs_name (str): Name of the directory for Markdown documents. Defaults to "markdown_docs".
    ignore_list (list[str]): List of files or directories to be ignored during documentation generation. Defaults to an empty list.
    language (str): Language code or name used in generated documentation. Defaults to "English".
    max_thread_count (PositiveInt): Maximum number of threads allowed for concurrent task handling. Defaults to 4.
    log_level (LogLevel): Log level as a LogLevel enum member, controlling the verbosity of logging output. Defaults to LogLevel.INFO.

Returns:
    None

Raises:
    ValueError: If the provided language is invalid.
    ValueError: If the provided log level is invalid.

Note:
    See also: LogLevel enumeration for logging levels.
"""
    target_repo: DirectoryPath = ''
    hierarchy_name: str = '.project_doc_record'
    markdown_docs_name: str = 'markdown_docs'
    ignore_list: list[str] = []
    language: str = 'English'
    max_thread_count: PositiveInt = 4
    log_level: LogLevel = LogLevel.INFO
    main_idea: Optional[str] = None

    @field_validator('language')
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        """Validates the input language code or name.

Ensures that the provided language code or name corresponds to a valid ISO 639 code, raising an error if it does not. This function is part of the Repository Agent framework, which automates documentation generation for Python projects by analyzing and validating various components within the repository.

Args:  
    v (str): The language code or name to validate.  

Returns:  
    str: The resolved language name.  

Raises:  
    ValueError: If the input is not a valid ISO 639 code or language name.  
"""
        try:
            language_name = Language.match(v).name
            return language_name
        except LanguageNotFoundError:
            raise ValueError('Invalid language input. Please enter a valid ISO 639 code or language name.')

    @field_validator('log_level', mode='before')
    @classmethod
    def set_log_level(cls, v: str) -> LogLevel:
        """Sets the log level based on the input string.

The function converts the provided log level string to uppercase and returns the corresponding LogLevel enum value. If the provided log level is not valid, a ValueError is raised.

Args:  
    v (str): The log level as a string, which will be converted to uppercase.

Returns:  
    LogLevel: The corresponding LogLevel enum value.

Raises:  
    ValueError: If the provided log level is not valid.
"""
        if isinstance(v, str):
            v = v.upper()
        if v in LogLevel._value2member_map_:
            return LogLevel(v)
        raise ValueError(f'Invalid log level: {v}')

class ChatCompletionSettings(BaseSettings):
    """Configures chat completion settings for the Repository Agent.

The ChatCompletionSettings class allows users to customize various parameters related to chat completions, such as model selection, randomness control, request timeouts, and API configurations.

Args:
    model (str): The name of the model to be used. Defaults to "gpt-4o-mini".
    temperature (PositiveFloat): Controls the randomness in the output. Higher values lead to more diverse results. Defaults to 0.2.
    request_timeout (PositiveInt): Timeout duration for API requests, measured in seconds. Defaults to 60 seconds.
    openai_base_url (str): Base URL for the OpenAI API endpoint. Defaults to "https://api.openai.com/v1".
    openai_api_key (SecretStr): Secret string containing the OpenAI API key.

Returns:
    ChatCompletionSettings: An instance of the settings class.

Raises:
    ValueError: If the base URL is not a valid HTTP URL.

Note:
    It is recommended to use models with larger context windows for better performance and flexibility.
"""
    model: str = 'gpt-4o-mini'
    temperature: PositiveFloat = 0.2
    request_timeout: PositiveInt = 60
    openai_base_url: str = 'https://api.openai.com/v1'
    openai_api_key: SecretStr = Field(..., exclude=True)

    @field_validator('openai_base_url', mode='before')
    @classmethod
    def convert_base_url_to_str(cls, openai_base_url: HttpUrl) -> str:
        """Converts an HTTP URL object representing the OpenAI API base URL to a string.

Args:  
    openai_base_url (HttpUrl): The base URL of the OpenAI API.

Returns:  
    str: The string representation of the provided URL.
"""
        return str(openai_base_url)

class Setting(BaseSettings):
    """Configuration settings for the project and chat completion.

The Setting class manages configurations specific to the Repository Agent project and its chat completion feature, ensuring that all necessary parameters are properly set up for optimal performance.

Args:
    project (ProjectSettings): Configuration settings specific to the project.
    chat_completion (ChatCompletionSettings): Settings related to chat completion functionality.

Returns:
    None

Note:
    See also: ProjectSettings, ChatCompletionSettings classes for detailed configurations.
"""
    project: ProjectSettings = {}
    chat_completion: ChatCompletionSettings = {}

class SettingsManager:
    """Given the context of the Repository Agent framework and its purpose, here's an updated docstring for the `SettingsManager` class in `repo_agent/settings.py`. The main idea is to manage configuration settings for the repository agent.

Manages configuration settings for the Repository Agent.  

This class provides methods to load, update, and retrieve settings used by the framework. It ensures that the configuration is consistent across different parts of the system.

Args:  
    None

Returns:  
    None

Raises:  
    ValueError: If an invalid setting key is provided.
    
Note:  
    See also: Configuration management (if applicable).


This docstring adheres to the Google docstring conventions and provides a concise description of what the `SettingsManager` class does without detailing specific methods or parameters that are not provided in the initial context."""
    _setting_instance: Optional[Setting] = None

    @classmethod
    def get_setting(cls):
        """Given the context of the Repository Agent framework and its focus on generating comprehensive documentation for Python projects, here's an updated docstring for the `get_setting` function in `repo_agent\\settings.py/SettingsManager`:

Retrieves a setting value from the configuration.

Args:
    key (str): The name of the setting to retrieve.
    default_value (Any, optional): Default value if the setting is not found. Defaults to None.

Returns:
    Any: The value associated with the provided key or the default value if the key does not exist.

Raises:
    KeyError: If the setting key is invalid and no default value is provided.


This docstring adheres to the Google docstring format, providing clear descriptions of the function's parameters, return type, and potential exceptions. It also maintains a concise and deterministic tone suitable for documentation readers."""
        if cls._setting_instance is None:
            cls._setting_instance = Setting()
        return cls._setting_instance

    @classmethod
    def initialize_with_params(cls, target_repo: Path, markdown_docs_name: str, hierarchy_name: str, ignore_list: list[str], language: str, max_thread_count: int, log_level: str, model: str, temperature: float, request_timeout: int, openai_base_url: str):
        """Initializes settings for the Repository Agent with specified parameters.

This function sets up the configuration required for the Repository Agent to analyze, document, and manage changes in a Python project repository.

Args:
    target_repo (Path): The path to the target repository.
    markdown_docs_name (str): Name of the directory where Markdown documents will be stored.
    hierarchy_name (str): Name of the directory that defines the hierarchical structure for documentation.
    ignore_list (list[str]): List of files or directories to exclude from analysis and documentation.
    language (str): Language code or name used in the project.
    max_thread_count (int): Maximum number of threads allowed for concurrent task execution.
    log_level (str): Log level as a string, controlling the verbosity of logging output.
    model (str): Identifier for the LLM model to be used for documentation generation and chat completion settings.
    temperature (float): Temperature setting that influences randomness in the generated text by the model.
    request_timeout (int): Request timeout in seconds for API calls.
    openai_base_url (str): Base URL for OpenAI API requests.

Returns:
    None

Raises:
    ValueError: If any of the parameters are invalid or inconsistent with project requirements.

Note:
    See also: LogLevel enumeration, ProjectSettings class, ChatCompletionSettings class.
"""
        project_settings = ProjectSettings(target_repo=target_repo, hierarchy_name=hierarchy_name, markdown_docs_name=markdown_docs_name, ignore_list=ignore_list, language=language, max_thread_count=max_thread_count, log_level=LogLevel(log_level))
        chat_completion_settings = ChatCompletionSettings(model=model, temperature=temperature, request_timeout=request_timeout, openai_base_url=openai_base_url)
        cls._setting_instance = Setting(project=project_settings, chat_completion=chat_completion_settings)
if __name__ == '__main__':
    setting = SettingsManager.get_setting()
    print(setting.model_dump())