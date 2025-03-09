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
  
set_log_level(v='INFO')

Converts and validates a string input as a LogLevel value.

Args:
    v (str): The log level value as a string. Defaults to INFO if not provided.

Returns:
    LogLevel: The validated LogLevel enum member.

Raises:
    ValueError: If the provided log level is invalid.
  
initialize_with_params(target_repo, markdown_docs_name, hierarchy_name, ignore_list, language, max_thread_count, log_level, model, temperature, request_timeout, openai_base_url)

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

Ensures that the provided language code or name corresponds to a valid ISO 639 code, raising an error if it does not. This function is part of the Repository Agent's configuration settings management, ensuring consistent language specifications across project documentation and summaries.

Args:  
    v (str): The language code or name to validate.  

Returns:  
    str: The resolved language name.  

Raises:  
    ValueError: If the input is not a valid ISO 639 code or language name.  

Note:  
    This function is used within the Repository Agent's settings management to ensure that all language-related configurations adhere to standardized codes and names.
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

This function converts the provided log level string to uppercase and returns the corresponding LogLevel enum value. If the provided log level is not valid, a ValueError is raised.

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

The ChatCompletionSettings class allows users to customize various parameters related to chat completions, such as model selection, randomness control, request timeouts, and API configurations. This is particularly useful in automating documentation generation and management within Python projects.

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

This function is part of the Repository Agent's configuration settings management, specifically within the `ChatCompletionSettings` class. It ensures that URLs used in the project are consistently represented as strings for further processing and documentation generation.

Args:  
    openai_base_url (HttpUrl): The base URL of the OpenAI API.

Returns:  
    str: The string representation of the provided URL.
"""
        return str(openai_base_url)

class Setting(BaseSettings):
    """Manages configuration settings for the Repository Agent project and chat completion.

The Setting class ensures that all necessary parameters are properly set up for optimal performance in automating documentation generation and management using large language models (LLMs).

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
    """Manages configuration settings for the Repository Agent.

The SettingsManager class provides a flexible configuration system to tailor documentation generation according to specific project needs. It allows users to define various settings such as log levels, chat completion configurations, and project-specific parameters.

Args:  
    None

Returns:  
    None

Raises:  
    ValueError: If an invalid setting is provided.
    
Note:  
    See also: ProjectSettings, LogLevel, ChatCompletionSettings (for related configuration options).
"""
    _setting_instance: Optional[Setting] = None

    @classmethod
    def get_setting(cls):
        """Retrieves a configuration setting from the settings manager.

Args:
    key (str): The name of the setting to retrieve.
    default_value (Any, optional): The value to return if the setting does not exist. Defaults to None.

Returns:
    Any: The value of the requested setting or the default value if the setting is not found.

Raises:
    KeyError: If the specified key is not found and no default value is provided.

Note:
    See also: SettingsManager (for managing configuration settings).
"""
        if cls._setting_instance is None:
            cls._setting_instance = Setting()
        return cls._setting_instance

    @classmethod
    def initialize_with_params(cls, target_repo: Path, markdown_docs_name: str, hierarchy_name: str, ignore_list: list[str], language: str, max_thread_count: int, log_level: str, model: str, temperature: float, request_timeout: int, openai_base_url: str):
        """Initializes the settings manager with specified parameters.

Args:
    params (dict): Configuration parameters for initializing the settings manager.

Returns:
    None

Raises:
    ValueError: If required configuration parameters are missing or invalid.
    
Note:
    See also: SettingsManager class documentation for more information on available configuration options.
"""
        project_settings = ProjectSettings(target_repo=target_repo, hierarchy_name=hierarchy_name, markdown_docs_name=markdown_docs_name, ignore_list=ignore_list, language=language, max_thread_count=max_thread_count, log_level=LogLevel(log_level))
        chat_completion_settings = ChatCompletionSettings(model=model, temperature=temperature, request_timeout=request_timeout, openai_base_url=openai_base_url)
        cls._setting_instance = Setting(project=project_settings, chat_completion=chat_completion_settings)
if __name__ == '__main__':
    setting = SettingsManager.get_setting()
    print(setting.model_dump())