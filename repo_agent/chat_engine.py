from typing import List, Dict
from llama_index.llms.openai_like import OpenAILike
from repo_agent.doc_meta_info import DocItem
from repo_agent.log import logger
from repo_agent.prompt import chat_template, idea_chat_template, new_desc_chat_template, module_summary_template, docstring_update_templates, docstring_update_chat_templates
from repo_agent.settings import SettingsManager


class ChatEngine:
    """
    ChatEngine.  
    
    A class for generating and managing chat-based documentation using an OpenAI-like language model. This class integrates with the project manager to automate the creation and updating of documentation, ensuring it remains accurate and up-to-date. The `repo_agent` project is designed to automate the generation and management of documentation for a Git repository, leveraging Git to detect changes, manage file handling, and generate documentation items as needed. It includes a multi-threaded task management system and a settings manager to configure project and chat completion settings, ensuring a robust and maintainable documentation process.
    
    ---
    
    ### \\_\\_init\\_\\_
    
    Initializes the ChatEngine instance.
    
    Args:  
        project_manager (ProjectManager): The project manager instance used to manage the project.
    
    Returns:  
        None
    
    Raises:  
        ValueError: If the API key or base URL is not properly configured in the settings.
    
    Note:  
        The LLM is configured with a context window of 20000, and the settings are retrieved from the SettingsManager. This method is essential for initializing the chat engine, which automates the detection of changes, the generation of documentation, and the management of project settings, making it easier for developers to maintain accurate documentation without manual intervention.
    
    ---
    
    ### build_prompt
    
    Builds a prompt for generating documentation based on the provided `DocItem` and optional parameters.
    
    Args:  
        doc_item (DocItem): The documentation item for which the prompt is being built.  
        main_idea (str): A user-defined main idea to enhance the existing docstring. Defaults to an empty string.  
        context_length (int): The maximum length of the context to be included in the prompt. Defaults to 20000.
    
    Returns:  
        str: The constructed prompt for the chat engine.
    
    Raises:  
        None
    
    Note:  
        See also: `get_referenced_prompt` and `get_referencer_prompt` methods for handling referenced and referencer items.
    
    ---
    
    ### generate_doc
    
    Generates documentation for a code item using a chat engine.
    
    Args:  
        doc_item (DocItem): The documentation item for which the documentation is being generated.
    
    Returns:  
        str: The generated documentation for the code item.
    
    Raises:  
        Exception: If there is an error in the chat engine call.
    
    Note:  
        See also: `build_prompt` method for constructing the prompt.
    
    ---
    
    ### generate_idea
    
    Generates an idea based on a list of items.
    
    Args:  
        list_items (str): A string containing the list of items to be used for generating the idea.
    
    Returns:  
        str: The generated idea from the language model.
    
    Raises:  
        Exception: If there is an error in the language model chat call.
    
    Note:  
        The `SettingsManager` class is used to manage and initialize project and chat completion settings. The `idea_chat_template` is a predefined template for formatting the list of items into a message.
    
    ---
    
    ### summarize_module
    
    Summarizes a module description using a language model.
    
    Args:  
        module_desc (str): The description of the module to be summarized.
    
    Returns:  
        str: The summarized content of the module.
    
    Raises:  
        Exception: If an error occurs during the chat call with the language model.
    
    Note:  
        The `SettingsManager` class is used to manage and initialize project and chat completion settings. The `module_summary_template` is used to format the module description into messages.
    """

    def __init__(self, project_manager):
        """
    Initializes the ChatEngine instance.
    
    Sets up the language model (LLM) using the provided project manager and settings from the SettingsManager. This method ensures that the LLM is configured with a context window of 20000 and retrieves the necessary settings to function properly within the project. The ChatEngine is a crucial component of the `repo_agent` project, which automates the generation and management of documentation for a Git repository. It integrates Git to detect changes, manage file handling, and generate documentation items as needed, reducing the manual effort required to keep documentation current.
    
    Args:
        project_manager (ProjectManager): The project manager instance used to manage the project.
    
    Returns:
        None
    
    Raises:
        ValueError: If the API key or base URL is not properly configured in the settings.
    
    Note:
        The LLM is configured with a context window of 20000, and the settings are retrieved from the SettingsManager. This method is essential for initializing the chat engine, which automates the detection of changes, the generation of documentation, and the management of project settings, making it easier for developers to maintain accurate documentation without manual intervention.
    """
        setting = SettingsManager.get_setting()
        self.llm = OpenAILike(context_window=20000, api_key=setting.
            chat_completion.openai_api_key.get_secret_value(), api_base=
            setting.chat_completion.openai_base_url, timeout=setting.
            chat_completion.request_timeout, model=setting.chat_completion.
            model, temperature=setting.chat_completion.temperature,
            max_retries=1, is_chat_model=True)

    def build_prompt(self, doc_item: DocItem, main_idea='', context_length=
        20000):
        """
    Builds a prompt for generating documentation based on the provided `DocItem` and optional parameters.
    
    This method constructs a detailed prompt for a chat engine to generate or update documentation for a code item. The prompt includes information about the code item, its references, and any user-defined main ideas. It also considers the context length and the relationship between the code item and other items in the project. This tool is part of a comprehensive system designed to automate the generation and management of documentation for a Git repository, ensuring that documentation is up-to-date and accurate.
    
    Args:
        doc_item (DocItem): The documentation item for which the prompt is being built.
        main_idea (str): A user-defined main idea to enhance the existing docstring. Defaults to an empty string.
        context_length (int): The maximum length of the context to be included in the prompt. Defaults to 20000.
    
    Returns:
        str: The constructed prompt for the chat engine.
    
    Raises:
        None
    
    Note:
        See also: `get_referenced_prompt` and `get_referencer_prompt` methods for handling referenced and referencer items.
    """
        setting = SettingsManager.get_setting()
        code_info = doc_item.content
        referenced = len(doc_item.who_reference_me) > 0 and len(code_info
            ) < 16000
        code_type = code_info['type']
        code_name = code_info['name']
        code_content = code_info['code_content']
        have_return = code_info['have_return']
        docstring = code_info['md_content'][-1] if code_info['md_content'
            ] else 'Empty docstring'
        file_path = doc_item.get_full_name()

        def get_referenced_prompt(doc_item: DocItem) ->str:
            if len(doc_item.reference_who) == 0:
                return ''
            prompt = [
                'As you can see, the code calls the following objects, their code and docs are as following:'
                ]
            for reference_item in doc_item.reference_who:
                instance_prompt = (
                    f"""obj: {reference_item.get_full_name()}
Document: 
{reference_item.md_content[-1] if len(reference_item.md_content) > 0 else 'None'}
Raw code:```
{reference_item.content['code_content'] if 'code_content' in reference_item.content.keys() else ''}
```"""
                     + '=' * 10)
                prompt.append(instance_prompt)
            return '\n'.join(prompt)

        def get_referencer_prompt(doc_item: DocItem) ->str:
            if len(doc_item.who_reference_me) == 0:
                return ''
            prompt = [
                'Also, the code has been called by the following objects, their code and docs are as following:'
                ]
            for referencer_item in doc_item.who_reference_me:
                instance_prompt = (
                    f"""obj: {referencer_item.get_full_name()}
Document: 
{referencer_item.md_content[-1] if len(referencer_item.md_content) > 0 else 'None'}
Raw code:```
{referencer_item.content['code_content'] if 'code_content' in referencer_item.content.keys() else 'None'}
```"""
                     + '=' * 10)
                prompt.append(instance_prompt)
            return '\n'.join(prompt)

        def get_relationship_description(referencer_content, reference_letter):
            if referencer_content and reference_letter:
                return (
                    'And please include the reference relationship with its callers and callees in the project from a functional perspective'
                    )
            elif referencer_content:
                return (
                    'And please include the relationship with its callers in the project from a functional perspective.'
                    )
            elif reference_letter:
                return (
                    'And please include the relationship with its callees in the project from a functional perspective.'
                    )
            else:
                return ''
        code_type_tell = 'Class' if code_type == 'ClassDef' else 'Function'
        if referenced:
            combine_ref_situation = (
                'and combine it with its calling situation in the project,')
            referencer_content = get_referencer_prompt(doc_item)
            reference_letter = get_referenced_prompt(doc_item)
            has_relationship = get_relationship_description(referencer_content,
                reference_letter)
        else:
            combine_ref_situation = ''
            referencer_content = ''
            reference_letter = ''
            has_relationship = ''
        if main_idea:
            return docstring_update_chat_templates.format_messages(
                combine_ref_situation=combine_ref_situation, file_path=
                file_path, code_type_tell=code_type_tell, code_name=
                code_name, main_idea=main_idea if not main_idea else
                f"""You can use user-defined main idea of the project to enhance exist docstring
{main_idea}"""
                , docstring=docstring, has_relationship=has_relationship,
                reference_letter=reference_letter, referencer_content=
                referencer_content, language=setting.project.language)
        else:
            return chat_template.format_messages(combine_ref_situation=
                combine_ref_situation, file_path=file_path, code_type_tell=
                code_type_tell, code_name=code_name, code_content=
                code_content, main_idea=main_idea if not main_idea else
                f"""You can use user-defined main idea of the project to enhance exist docstring
{main_idea}"""
                , docstring=docstring, has_relationship=has_relationship,
                reference_letter=reference_letter, referencer_content=
                referencer_content, language=setting.project.language)

    def generate_doc(self, doc_item: DocItem):
        """
    Generates documentation for a code item using a chat engine.
    
    This method constructs a detailed prompt for a chat engine to generate or update documentation for a code item. The prompt includes information about the code item, its references, and any user-defined main ideas. It then sends the prompt to the chat engine and returns the generated documentation.
    
    Args:
        doc_item (DocItem): The documentation item for which the documentation is being generated.
    
    Returns:
        str: The generated documentation for the code item.
    
    Raises:
        Exception: If there is an error in the chat engine call.
    
    Note:
        See also: `build_prompt` method for constructing the prompt.
    """
        settings = SettingsManager.get_setting()
        if settings.project.main_idea:
            messages = self.build_prompt(doc_item, main_idea=settings.
                project.main_idea)
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
        """
    Generates an idea based on a list of items.
    
    This method retrieves the project settings, formats the list of items into a message template, and sends the message to a language model for generating an idea. It logs the token usage of the language model and returns the generated idea. If an error occurs during the chat call, it logs the error and re-raises the exception.
    
    Args:
        list_items (str): A string containing the list of items to be used for generating the idea.
    
    Returns:
        str: The generated idea from the language model.
    
    Raises:
        Exception: If there is an error in the language model chat call.
    
    Note:
        The `SettingsManager` class is used to manage and initialize project and chat completion settings. The `idea_chat_template` is a predefined template for formatting the list of items into a message. This method is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository, enhancing user interaction through a chat engine. The `repo_agent` project integrates various functionalities to ensure that the documentation remains up-to-date and accurately reflects the current state of the codebase. It leverages Git to detect changes, manage file handling, and generate documentation items as needed. The tool also includes a multi-task dispatch system to efficiently process documentation tasks in a multi-threaded environment, ensuring that the documentation generation process is both scalable and robust.
    """
        settings = SettingsManager.get_setting()
        messages = idea_chat_template.format_messages(components=list_items,
            language=settings.project.language)
        try:
            response = self.llm.chat(messages)
            logger.debug(
                f'LLM Prompt Tokens: {response.raw.usage.prompt_tokens}')
            logger.debug(
                f'LLM Completion Tokens: {response.raw.usage.completion_tokens}'
                )
            logger.debug(
                f'Total LLM Token Count: {response.raw.usage.total_tokens}')
            return response.message.content
        except Exception as e:
            logger.error(f'Error in llamaindex chat call: {e}')
            raise

    def summarize_module(self, module_desc: str):
        """
    Summarizes a module description using a language model.
    
    This method retrieves the project settings, formats the module description into messages, and sends the messages to a language model for summarization. It logs the token usage and returns the summarized content. If an error occurs during the chat call, it logs the error and re-raises the exception.
    
    Args:
        module_desc (str): The description of the module to be summarized.
    
    Returns:
        str: The summarized content of the module.
    
    Raises:
        Exception: If an error occurs during the chat call with the language model.
    
    Note:
        The `SettingsManager` class is used to manage and initialize project and chat completion settings. The `module_summary_template` is used to format the module description into messages. This method is part of a comprehensive tool designed to automate the generation and management of documentation for a Git repository, ensuring that documentation is up-to-date and accurately reflects the current state of the codebase. The tool integrates various functionalities to detect changes, handle file operations, manage tasks, and configure settings, all while ensuring efficient and accurate documentation updates.
    """
        settings = SettingsManager.get_setting()
        messages = module_summary_template.format_messages(components=
            module_desc, main_idea=settings.project.main_idea, language=
            settings.project.language)
        try:
            response = self.llm.chat(messages)
            logger.debug(
                f'LLM Prompt Tokens: {response.raw.usage.prompt_tokens}')
            logger.debug(
                f'LLM Completion Tokens: {response.raw.usage.completion_tokens}'
                )
            logger.debug(
                f'Total LLM Token Count: {response.raw.usage.total_tokens}')
            return response.message.content
        except Exception as e:
            logger.error(f'Error in llamaindex chat call: {e}')
            raise
