from enum import StrEnum
from typing import Optional
from iso639 import Language, LanguageNotFoundError
from pydantic import DirectoryPath, Field, HttpUrl, PositiveFloat, PositiveInt, SecretStr, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path

class LogLevel(StrEnum):
    """[LogLevel]

An enumeration representing different logging levels within the Repository Documentation Generator project. This class is instrumental in defining, validating, and managing logging levels across the application, ensuring efficient communication and error tracking.

Args:
    level_str (str): A string representation of a log level. Accepted values are 'DEBUG', 'INFO', 'WARNING', 'ERROR', and 'CRITICAL'. Defaults to None.

Returns:
    LogLevel: An instance of the LogLevel enum corresponding to the provided log level string.

Raises:
    ValueError: If an invalid log level string is provided.

Note:
    This class is used to define and validate logging levels in the application. It aids in categorizing messages based on their severity, facilitating effective management of logs during the documentation generation process.

    See also: ProjectSettings.log_level (for usage in a project settings context within the Repository Documentation Generator).

Examples:
    >>> from repo_agent.settings import LogLevel
    >>> log_level = LogLevel('INFO')
    >>> print(log_level)  # Output: LogLevel.INFO

The Repository Documentation Generator is a comprehensive tool designed to automate the documentation process for software projects. It leverages advanced techniques such as chat-based interaction and multi-task dispatching to streamline the generation of documentation pages, summaries, and metadata. The LogLevel class plays a crucial role in this process by defining and validating logging levels, thereby enabling efficient communication and error tracking within the application."""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

class ProjectSettings(BaseSettings):
    """[ProjectSettings]

A class representing project settings for the Repository Documentation Generator application.

This class encapsulates various configuration parameters crucial for the operation of the tool, including repository details, language preferences, logging levels, and more. It utilizes type hints and custom validation methods to ensure the integrity of the set values.

Args:
    target_repo (DirectoryPath): The path to the target repository directory where documentation generation will occur. Defaults to an empty string.
    hierarchy_name (str): The name of the project hierarchy within the repository. Defaults to ".project_doc_record".
    markdown_docs_name (str): The name of the markdown documentation directory in the repository. Defaults to "markdown_docs".
    ignore_list (list[str]): A list of strings representing files or directories within the repository to be ignored during processing. Defaults to an empty list.
    language (str): The language setting for the project, following ISO 639 standards. This influences the generation of documentation in different languages. Defaults to "English".
    max_thread_count (PositiveInt): The maximum number of threads to use in concurrent operations during documentation generation. Defaults to 4.
    log_level (LogLevel): The logging level for the application, controlling the verbosity of logs generated during operation. Defaults to LogLevel.INFO.
    main_idea (Optional[str]): An optional main idea or focus of the project, guiding the structure and content of the generated documentation. Defaults to None.

Returns:
    ProjectSettings: An instance of this class with the provided settings, ready for use in the Repository Documentation Generator workflow.

Raises:
    ValueError: If an invalid language code or log level string is provided.

Note:
    This class utilizes custom validation methods (`validate_language_code` and `set_log_level`) to ensure that the 'language' and 'log_level' parameters are set correctly.

    The 'target_repo', 'hierarchy_name', 'markdown_docs_name', and 'ignore_list' parameters directly influence the repository-specific aspects of documentation generation, while 'language', 'max_thread_count', and 'log_level' control the operational settings. The 'main_idea' parameter allows tailoring of the generated documentation to a specific project focus.

    See also: repo_agent.settings.LogLevel (for valid logging levels), repo_agent.settings.Setting (for usage in a project settings context)."""
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
        '''"""Converts the given base URL to its string representation.

This function takes an instance of HttpUrl as input, which represents a base URL used for communication with external services (like OpenAI), and returns its string representation. This process ensures uniformity in how URLs are handled across the framework, facilitating consistent processing and interaction.

Args:
    openai_base_url (HttpUrl): The base URL to be converted into a string. This could represent a connection point to an external service like OpenAI for tasks such as chat completions or code execution.

Returns:
    str: The string representation of the provided base URL. This formatted string can then be used in various parts of the framework where a uniform string type is required, ensuring seamless integration and interaction with external services.

Raises:
    None: This function does not raise any exceptions. It gracefully handles the conversion process without disrupting the workflow.

Note:
    This function serves as a utility within the Repository Documentation Generator project. Its purpose is to standardize URL representation, thereby enhancing the framework's ability to interact with external services reliably and consistently. It contributes to the overall goal of automating and simplifying the documentation generation process for software projects.
"""'''
        try:
            language_name = Language.match(v).name
            return language_name
        except LanguageNotFoundError:
            raise ValueError('Invalid language input. Please enter a valid ISO 639 code or language name.')

    @field_validator('log_level', mode='before')
    @classmethod
    def set_log_level(cls, v: str) -> LogLevel:
        """[Setting]

A function aggregating project-specific configurations and chat completion parameters for the Repository Documentation Generator application.

This function combines two distinct setting classes: `ProjectSettings` and `ChatCompletionSettings`. The former encapsulates various configuration parameters for a project, including repository details, language preferences, logging levels, and more. The latter configures the chat completion feature, detailing aspects such as the model to use, temperature control, request timeout, base URL for OpenAI API, and API key (set separately for security reasons).

Args:
    project_settings (ProjectSettings): An instance of ProjectSettings class representing project-specific configurations.  
    chat_completion_settings (ChatCompletionSettings): An instance of ChatCompletionSettings class detailing chat completion parameters.  

Returns:
    None

Raises:
    None

Note:
    This function serves as a container for both project and chat completion settings, facilitating their unified management within the Repository Documentation Generator application. It leverages the ChangeDetector, ChatEngine, EdgeType & DocItemType, DocItemStatus & need_to_generate, MetaInfo & FileHandler, InterceptHandler & set_logger_level_from_config, cli & run, diff, clean, summarize_repository, create_module_summary, chat_with_repo & run_outside_cli, Task, TaskManager, worker, some_function, ProjectManager & Runner, LogLevel, ProjectSettings, ChatCompletionSettings, Setting, SettingsManager, GitignoreChecker & make_fake_files, delete_fake_files components to ensure comprehensive documentation generation.

    See also: repo_agent.settings.ProjectSettings (for project-specific configurations), repo_agent.settings.ChatCompletionSettings (for chat completion parameters), repo_agent.settings.Setting (for usage in a project settings context)."""
        if isinstance(v, str):
            v = v.upper()
        if v in LogLevel._value2member_map_:
            return LogLevel(v)
        raise ValueError(f'Invalid log level: {v}')

class ChatCompletionSettings(BaseSettings):
    '''"""Validates the language code input within the Repository Documentation Generator project.

This function, part of the ProjectSettings module, takes a string input representing a language code or name and attempts to resolve it into an ISO 639 language code. It is designed to support the automated documentation generation process by ensuring accurate language representation. If successful, it returns the resolved language name. If the input is not a valid language code or name, it raises a ValueError with an appropriate error message.

Args:
    v (str): The string representation of a language code or name. This could be used in various documentation items across the repository, ensuring consistent language formatting.

Returns:
    str: The ISO 639 language code corresponding to the input. This resolved code will be utilized in generating accurate and standardized documentation.

Raises:
    ValueError: If the input is not a valid language code or name. This ensures that only correct language representations are used in the documentation process, maintaining consistency and accuracy.

Note:
    This function uses the `Language.match()` method from the `repo_agent.settings.ProjectSettings` module to validate and resolve the language code or name. It aligns with the ChangeDetector feature of the Repository Documentation Generator, which monitors changes in the repository to determine which documentation items need updating or generating.
"""'''
    model: str = 'gpt-4o-mini'
    temperature: PositiveFloat = 0.2
    request_timeout: PositiveInt = 60
    openai_base_url: str = 'https://api.openai.com/v1'
    openai_api_key: SecretStr = Field(..., exclude=True)

    @field_validator('openai_base_url', mode='before')
    @classmethod
    def convert_base_url_to_str(cls, openai_base_url: HttpUrl) -> str:
        """
SettingsManager: Manages project settings for the Repository Documentation Generator.

This class centralizes and orchestrates various configuration aspects of the documentation generation process. It handles project-specific settings, logging configurations, and interaction with other components of the system.

Args:
    project_settings (dict): A dictionary containing all project-related settings. Defaults to an empty dictionary.
    chat_completion_settings (dict): A dictionary holding settings for the chat engine. Defaults to an empty dictionary.

Returns:
    None

Raises:
    TypeError: If either `project_settings` or `chat_completion_settings` is not a dictionary.

Note:
    This class is integral to the overall operation of the Repository Documentation Generator, ensuring that all components function cohesively according to project-specific configurations.
"""
        return str(openai_base_url)

class Setting(BaseSettings):
    '''"""Sets the log level for the project within the Repository Documentation Generator framework.

This function configures the logging behavior of the Repository Documentation Generator by setting the log level based on the input string. The input string is converted to uppercase to ensure case insensitivity. If the input string matches one of the valid log levels (as defined in LogLevel enum), it returns the corresponding LogLevel object. Otherwise, it raises a ValueError.

This method plays a crucial role in managing and customizing the logging behavior of the Repository Documentation Generator, ensuring that only valid configurations are accepted. This prevents potential runtime errors due to invalid log level settings.

Args:
    cls (type): The class instance. This parameter is not used in this function but is included for consistency with other methods in the class.
    v (str): The log level to be set. It should be a string and can be one of 'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'.

Returns:
    LogLevel: The log level object corresponding to the input string.

Raises:
    ValueError: If the input string does not match any valid log levels.

Note:
    This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It leverages advanced techniques such as chat-based interaction and multi-task dispatching to streamline the generation of documentation pages, summaries, and metadata. The set_log_level method specifically contributes to configuring the logging behavior of the project, ensuring that only valid log levels are accepted, thereby preventing potential runtime errors due to invalid configurations.
"""'''
    project: ProjectSettings = {}
    chat_completion: ChatCompletionSettings = {}

class SettingsManager:
    '''"""Settings for chat completion functionality within the Repository Documentation Generator project.

This class encapsulates the configuration parameters for the chat completion feature, which is utilized to facilitate interactive communication with the repository. It includes settings for the language model to be used, temperature control for randomness in predictions, request timeout, base URL for OpenAI API, and API key (stored as a secret).

Args:
    model (str): The name of the language model to be used for chat completion. Defaults to "gpt-4o-mini". This setting influences the type of responses generated during interactions with the repository.
    temperature (PositiveFloat): A float value controlling the randomness of predictions by the language model.
        Values closer to 0 discourage randomness and are more deterministic, while values closer to 1 encourage randomness. This parameter is crucial for managing the conversational style of the AI assistant.
    request_timeout (PositiveInt): The number of seconds to wait for a response from the OpenAI API before timing out. This setting ensures efficient use of resources and prevents prolonged waiting periods.
    openai_base_url (HttpUrl): The base URL for the OpenAI API. This is automatically converted to a string by the `convert_base_url_to_str` class method. It specifies the endpoint for all API requests related to chat completion.

Returns:
    None

Raises:
    None

Note:
    The `openai_api_key` is set as a secret and not included in this class's parameters for security reasons. It should be provided separately when initializing the settings.

    See also: `Setting` class in repo_agent/settings.py, which includes both `ProjectSettings` and `ChatCompletionSettings`. This class is part of a broader configuration system that manages various aspects of the Repository Documentation Generator project, including project-wide settings, chat completion configurations, and more.
"""'''
    _setting_instance: Optional[Setting] = None

    @classmethod
    def get_setting(cls):
        """
Retrieves a setting from the SettingsManager.

This function fetches a specific setting from the SettingsManager instance. It is designed to provide quick access to configuration values within the Repository Documentation Generator project, which automates the documentation process for software projects using advanced techniques like chat-based interaction and multi-task dispatching.

Args:
    settings_manager (SettingsManager): An instance of the SettingsManager class, which holds all the project's settings.
    setting_name (str): The name of the setting to retrieve.

Returns:
    Any: The value of the requested setting.

Raises:
    KeyError: If the specified setting does not exist in the SettingsManager.

Note:
    This function is part of the SettingsManager class, which is responsible for managing various settings within the Repository Documentation Generator project. It ensures that developers can easily access and modify configuration values without manually editing files or remembering specific locations.
"""
        if cls._setting_instance is None:
            cls._setting_instance = Setting()
        return cls._setting_instance

    @classmethod
    def initialize_with_params(cls, target_repo: Path, markdown_docs_name: str, hierarchy_name: str, ignore_list: list[str], language: str, max_thread_count: int, log_level: str, model: str, temperature: float, request_timeout: int, openai_base_url: str):
        """[initialize_with_params]

Initializes the application settings using provided parameters within the Repository Documentation Generator project.

This function configures various aspects of the application, including project-specific configurations (`ProjectSettings`) and chat completion parameters (`ChatCompletionSettings`), to ensure seamless operation of the documentation generation process. It combines these settings into a single `Setting` instance for unified management.

Args:
    cls (type): The class to which the setting instance will be assigned.
    target_repo (Path): The path to the target repository directory, where documentation generation takes place.
    markdown_docs_name (str): The name of the markdown documentation directory within the repository.
    hierarchy_name (str): The name of the project hierarchy, defining the structure of the generated documentation.
    ignore_list (list[str]): A list of strings representing files or directories to be ignored during the documentation generation process.
    language (str): The language setting for the project, following ISO 639 standards, which influences the generated content's linguistic characteristics.
    max_thread_count (int): The maximum number of threads to use in concurrent operations, optimizing resource utilization during documentation generation.
    log_level (str): The logging level for the application, controlling the verbosity of logs produced during operation.
    model (str): The name of the language model to be used for chat completion within the documentation process, affecting the quality and style of generated content.
    temperature (float): A float value controlling the randomness of predictions by the language model, influencing the creativity and diversity of generated text.
    request_timeout (int): The number of seconds to wait for a response from external APIs (like OpenAI) before timing out, ensuring efficient interaction with remote services.
    openai_base_url (str): The base URL for the OpenAI API or similar services, specifying the endpoint for external language model interactions.

Returns:
    None

Raises:
    ValueError: If an invalid log level string or language code is provided, preventing misconfigurations that could disrupt documentation generation.

Note:
    This function employs custom validation methods (`validate_language_code` and `set_log_level`) to ensure the 'language' and 'log_level' parameters are correctly set, maintaining consistent operation across diverse project contexts.

    See also: repo_agent.settings.ProjectSettings (for detailed project-specific configurations), repo_agent.settings.ChatCompletionSettings (for comprehensive chat completion parameters), repo_agent.settings.Setting (for unified management of settings within the application)."""
        project_settings = ProjectSettings(target_repo=target_repo, hierarchy_name=hierarchy_name, markdown_docs_name=markdown_docs_name, ignore_list=ignore_list, language=language, max_thread_count=max_thread_count, log_level=LogLevel(log_level))
        chat_completion_settings = ChatCompletionSettings(model=model, temperature=temperature, request_timeout=request_timeout, openai_base_url=openai_base_url)
        cls._setting_instance = Setting(project=project_settings, chat_completion=chat_completion_settings)
if __name__ == '__main__':
    setting = SettingsManager.get_setting()
    print(setting.model_dump())