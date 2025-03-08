from typing import List, Dict
from llama_index.llms.openai_like import OpenAILike
from repo_agent.doc_meta_info import DocItem
from repo_agent.log import logger
from repo_agent.prompt import chat_template, idea_chat_template, new_desc_chat_template, module_summary_template, docstring_update_templates, docstring_update_chat_templates
from repo_agent.settings import SettingsManager

class ChatEngine:
    '''ChatEngine:
    """
    ChatEngine facilitates the generation of documentation for functions or classes within a software project using an OpenAI-like model.

    It initializes with a ProjectManager instance, utilizing it to retrieve settings such as API keys, base URLs, timeouts, models, and temperatures for the OpenAI-like model.

    Args:
        project_manager (ProjectManager): An instance of ProjectManager used to fetch necessary settings.

    Attributes:
        api_key (str): The API key for accessing the OpenAI-like model.
        base_url (str): The base URL for the OpenAI-like model's endpoint.
        timeout (int): The request timeout in seconds.
        model (str): The name of the OpenAI-like model to use.
        temperature (float): A value controlling the randomness of predictions by the OpenAI-like model.

    Methods:
        build_prompt(doc_item: DocItem, main_idea="", context_length=20000):
            Constructs and returns system and user prompts based on a DocItem. It considers whether the code is referenced and generates prompts accordingly.

        generate_doc(doc_item: DocItem):
            Generates documentation for a given DocItem using the OpenAI-like model. If a main idea is provided in the project settings, it's used in the prompt; otherwise, an empty main idea is assumed.

        generate_idea(list_items: str):
            Generates ideas or summaries based on a list of components, using the OpenAI-like model. The language setting from the project is considered.

        summarize_module(module_desc: str):
            Summarizes a module description using the OpenAI-like model. It incorporates a main idea from the project settings if available.

    Returns:
        str: The generated documentation, idea, or summary.

    Raises:
        Exception: If there's an error in the OpenAI-like model chat call.

    Note:
        This class is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It leverages advanced techniques such as chat-based interaction and multi-task dispatching to streamline the generation of documentation pages, summaries, and metadata.
    """'''

    def __init__(self, project_manager):
        '''"""Initializes the ChatEngine instance within the Repository Documentation Generator project.

This method sets up the OpenAILike model for the ChatEngine, utilizing configurations from SettingsManager. It fetches settings such as API key, base URL, timeout, model type, temperature, and other attributes to initialize the ChatEngine instance.

Args:
    project_manager (ProjectManager): An instance of ProjectManager used for managing project-related tasks within the Repository Documentation Generator. This includes overseeing changes detected by ChangeDetector, handling metadata with MetaInfo, and coordinating task execution via TaskManager.

Returns:
    None

Raises:
    None

Note:
    This method does not return any value but initializes the ChatEngine instance with the provided settings. It's a crucial part of the Repository Documentation Generator's functionality, enabling interactive communication with the repository through ChatEngine.

    See also: SettingsManager for details on how settings are managed and retrieved within the Repository Documentation Generator.
"""'''
        setting = SettingsManager.get_setting()
        self.llm = OpenAILike(context_window=20000, api_key=setting.chat_completion.openai_api_key.get_secret_value(), api_base=setting.chat_completion.openai_base_url, timeout=setting.chat_completion.request_timeout, model=setting.chat_completion.model, temperature=setting.chat_completion.temperature, max_retries=1, is_chat_model=True)

    def build_prompt(self, doc_item: DocItem, main_idea='', context_length=20000):
        """
[Short one-line description]

The 'build_prompt' function constructs a prompt for the chat engine, facilitating natural language interaction with the repository to generate or update documentation.

[Longer description if needed.]

Args:
    repo_structure (dict): A dictionary representing the structure of the repository, including edges and doc items.
    current_task (Task): The current task object from the TaskManager, specifying the type of documentation to be generated.
    project_settings (ProjectSettings): The project settings object containing configuration details.

Returns:
    str: A formatted prompt string suitable for interaction with the chat engine.

Raises:
    None

Note:
    This function is part of the Repository Documentation Generator, a tool designed to automate and simplify the documentation process for software projects. It leverages a chat-based interface to interact with the repository, enabling users to request specific documentation through natural language queries. The 'build_prompt' function plays a crucial role in this process by constructing a prompt tailored to the current task and repository structure.
"""
        setting = SettingsManager.get_setting()
        code_info = doc_item.content
        referenced = len(doc_item.who_reference_me) > 0 and len(code_info) < 16000
        code_type = code_info['type']
        code_name = code_info['name']
        code_content = code_info['code_content']
        have_return = code_info['have_return']
        docstring = code_info['md_content'][-1] if code_info['md_content'] else 'Empty docstring'
        file_path = doc_item.get_full_name()

        def get_referenced_prompt(doc_item: DocItem) -> str:
            """# Repository Documentation Generator: `generate_doc` Function

The `generate_doc` function is a core component of the Repository Documentation Generator, an advanced tool designed to automate the documentation process for software projects. It employs sophisticated techniques such as chat-based interaction and multi-task dispatching to streamline the generation of documentation pages, summaries, and metadata.

## Description

The `generate_doc` function is responsible for creating detailed documentation based on user requests or detected changes in the repository. It interacts with various components of the system, including the ChatEngine for natural language queries, ChangeDetector for monitoring repository updates, and TaskManager for efficient task allocation.

## Args

- **request** (str): A string representing the user's documentation request or a change detected by the ChangeDetector. This could be a specific file path, a module name, or a general query about the project structure.
- **settings** (dict): A dictionary containing various settings for the documentation generation process. These may include logging levels, project-specific configurations, and chat interaction parameters. Defaults to the system's default settings.

## Returns

- **str**: A string containing the generated documentation. The format and content of this string depend on the nature of the `request` parameter. It could be a full file summary, a module overview, or a response to a natural language query about the project.

## Raises

- **ValueError**: If the `request` parameter is not properly formatted or if there's an issue with the provided settings.
- **RuntimeError**: In case of unexpected errors during the documentation generation process, such as issues with file access or system resource limitations.

## Notes

- This function is part of a larger system that includes components like ChangeDetector, ChatEngine, TaskManager, and others, all working together to provide a comprehensive documentation solution.
- The exact behavior of this function can vary based on the specifics of the `request` parameter and the current state of the repository. For detailed information about possible outputs, refer to the system's overall design and individual component docstrings."""
            if len(doc_item.reference_who) == 0:
                return ''
            prompt = ['As you can see, the code calls the following objects, their code and docs are as following:']
            for reference_item in doc_item.reference_who:
                instance_prompt = f'obj: {reference_item.get_full_name()}\nDocument: \n{(reference_item.md_content[-1] if len(reference_item.md_content) > 0 else 'None')}\nRaw code:```\n{(reference_item.content['code_content'] if 'code_content' in reference_item.content.keys() else '')}\n```' + '=' * 10
                prompt.append(instance_prompt)
            return '\n'.join(prompt)

        def get_referencer_prompt(doc_item: DocItem) -> str:
            """'''
Generates a project idea based on a list of items using the ChatEngine's language model.

This function creates a project idea by formatting a template with the provided list of items, then utilizing the language model to expand upon it. The generated idea is returned as a string. It leverages the SettingsManager for configuration settings, specifically the language setting, which are used to format messages before passing them to the language model.

Args:
    list_items (str): A string containing a newline-separated list of items that define the components for generating the project idea.

Returns:
    str: The generated project idea as a string.

Raises:
    Exception: If there is an error in the language model chat call.

Note:
    This function is part of the Repository Documentation Generator, a comprehensive tool designed to automate the documentation process for software projects. It employs advanced techniques such as chat-based interaction and multi-task dispatching to streamline the generation of documentation pages, summaries, and metadata.

    The SettingsManager retrieves configuration settings, specifically the language setting, which are used to format messages before passing them to the language model. For more details on how settings are managed, see repo_agent.settings.SettingsManager.

See also:
    repo_agent.settings.SettingsManager for managing settings.
'''"""
            if len(doc_item.who_reference_me) == 0:
                return ''
            prompt = ['Also, the code has been called by the following objects, their code and docs are as following:']
            for referencer_item in doc_item.who_reference_me:
                instance_prompt = f'obj: {referencer_item.get_full_name()}\nDocument: \n{(referencer_item.md_content[-1] if len(referencer_item.md_content) > 0 else 'None')}\nRaw code:```\n{(referencer_item.content['code_content'] if 'code_content' in referencer_item.content.keys() else 'None')}\n```' + '=' * 10
                prompt.append(instance_prompt)
            return '\n'.join(prompt)

        def get_relationship_description(referencer_content, reference_letter):
            """'''
Summarizes a module description into a concise summary using the language model within the context of the Repository Documentation Generator project.

This function, part of the ChatEngine component, takes a detailed module description as input. It formats this description along with relevant project settings to generate a succinct summary. The formatted messages incorporate the main idea of the project and the specified language, as defined by SettingsManager.get_setting().

Args:
    self (ChatEngine): An instance of ChatEngine, facilitating interaction with the repository and managing documentation tasks.
    module_desc (str): A detailed description of the module to be summarized. This includes information about the module's purpose, functionality, and other relevant details.

Returns:
    str: A concise summary of the module description, encapsulating its main ideas and functionalities.

Raises:
    Exception: If there is an error during the language model chat call, indicating a potential issue with the model or input data.

Note:
    The formatted messages for the language model include the main idea of the project and the specified language, as defined by SettingsManager.get_setting(). This ensures that the generated summary aligns with the overall documentation style and requirements of the Repository Documentation Generator project.

See also:
    For more information on the Repository Documentation Generator, refer to its comprehensive documentation detailing features like ChangeDetector, ChatEngine, EdgeType & DocItemType, MetaInfo & FileHandler, Task & TaskManager, and others. These components work in concert to automate and streamline the documentation process for software projects.
'''"""
            if referencer_content and reference_letter:
                return 'And please include the reference relationship with its callers and callees in the project from a functional perspective'
            elif referencer_content:
                return 'And please include the relationship with its callers in the project from a functional perspective.'
            elif reference_letter:
                return 'And please include the relationship with its callees in the project from a functional perspective.'
            else:
                return ''
        code_type_tell = 'Class' if code_type == 'ClassDef' else 'Function'
        if referenced:
            combine_ref_situation = 'and combine it with its calling situation in the project,'
            referencer_content = get_referencer_prompt(doc_item)
            reference_letter = get_referenced_prompt(doc_item)
            has_relationship = get_relationship_description(referencer_content, reference_letter)
        else:
            combine_ref_situation = ''
            referencer_content = ''
            reference_letter = ''
            has_relationship = ''
        if main_idea:
            return docstring_update_chat_templates.format_messages(combine_ref_situation=combine_ref_situation, file_path=file_path, code_type_tell=code_type_tell, code_name=code_name, main_idea=main_idea if not main_idea else f'You can use user-defined main idea of the project to enhance exist docstring\n{main_idea}', docstring=docstring, has_relationship=has_relationship, reference_letter=reference_letter, referencer_content=referencer_content, language=setting.project.language)
        else:
            return chat_template.format_messages(combine_ref_situation=combine_ref_situation, file_path=file_path, code_type_tell=code_type_tell, code_name=code_name, code_content=code_content, main_idea=main_idea if not main_idea else f'You can use user-defined main idea of the project to enhance exist docstring\n{main_idea}', docstring=docstring, has_relationship=has_relationship, reference_letter=reference_letter, referencer_content=referencer_content, language=setting.project.language)

    def generate_doc(self, doc_item: DocItem):
        """Generates documentation for a given DocItem."""
        settings = SettingsManager.get_setting()
        if settings.project.main_idea:
            messages = self.build_prompt(doc_item, main_idea=settings.project.main_idea)
        else:
            messages = self.build_prompt(doc_item)
        try:
            response = self.llm.chat(messages)
            answer = response.message.content
            return answer.replace('```python\n', '').replace('```', '')
        except Exception as e:
            logger.error(f'Error in llamaindex chat call: {e}')
            raise

    def generate_idea(self, list_items: str):
        settings = SettingsManager.get_setting()
        messages = idea_chat_template.format_messages(components=list_items, language=settings.project.language)
        try:
            response = self.llm.chat(messages)
            logger.debug(f'LLM Prompt Tokens: {response.raw.usage.prompt_tokens}')
            logger.debug(f'LLM Completion Tokens: {response.raw.usage.completion_tokens}')
            logger.debug(f'Total LLM Token Count: {response.raw.usage.total_tokens}')
            return response.message.content
        except Exception as e:
            logger.error(f'Error in llamaindex chat call: {e}')
            raise

    def summarize_module(self, module_desc: str):
        settings = SettingsManager.get_setting()
        messages = module_summary_template.format_messages(components=module_desc, main_idea=settings.project.main_idea, language=settings.project.language)
        try:
            response = self.llm.chat(messages)
            logger.debug(f'LLM Prompt Tokens: {response.raw.usage.prompt_tokens}')
            logger.debug(f'LLM Completion Tokens: {response.raw.usage.completion_tokens}')
            logger.debug(f'Total LLM Token Count: {response.raw.usage.total_tokens}')
            return response.message.content
        except Exception as e:
            logger.error(f'Error in llamaindex chat call: {e}')
            raise