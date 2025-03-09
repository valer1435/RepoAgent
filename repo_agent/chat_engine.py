from typing import List, Dict
from llama_index.llms.openai_like import OpenAILike
from repo_agent.doc_meta_info import DocItem
from repo_agent.log import logger
from repo_agent.prompt import chat_template, idea_chat_template, new_desc_chat_template, module_summary_template, docstring_update_templates, docstring_update_chat_templates
from repo_agent.settings import SettingsManager

class ChatEngine:
    """ChatEngine is used to manage the generation of documentation for Python projects.

Args:  
    project_manager (ProjectManager): The project manager instance.

build_prompt(doc_item, main_idea="", context_length=20000) -> str:
Builds and returns the system and user prompts based on the DocItem. Uses the provided main idea to enhance the existing docstring.

Args:  
    doc_item (DocItem): The document item to build a prompt for.  
    main_idea (str, optional): Main idea of the project to enhance the existing docstring. Defaults to "".  
    context_length (int, optional): Length of the context window. Defaults to 20000.

Returns:  
    str: The generated prompt.

Raises:  
    Exception: If an error occurs during the chat call.

generate_doc(doc_item) -> str:
Generates documentation for a given DocItem.

Args:  
    doc_item (DocItem): The document item to generate documentation for.

Returns:  
    str: The generated documentation.

Raises:  
    Exception: If an error occurs during the chat call.

generate_idea(list_items) -> str:
Generates an idea based on a list of items.

Args:  
    list_items (str): A string containing a list of items.

Returns:  
    str: The generated idea.

Raises:  
    Exception: If an error occurs during the chat call.

summarize_module(module_desc) -> str:
Summarizes a module description.

Args:  
    module_desc (str): The module description to summarize.

Returns:  
    str: The summarized module description.

Raises:  
    Exception: If an error occurs during the chat call.
"""

    def __init__(self, project_manager):
        """Initialize the ChatEngine instance.

Sets up the language model (LLM) using configuration settings from the project manager, ensuring that the necessary configurations are in place for the Repository Agent to function effectively.

Args:  
    project_manager (ProjectManager): The project manager that provides necessary configurations and settings.  

Returns:  
    None  

Raises:  
    ValueError: If required API key or base URL is missing.  

Note:  
    See also: SettingsManager.get_setting() for more details on how settings are retrieved.
"""
        setting = SettingsManager.get_setting()
        self.llm = OpenAILike(context_window=20000, api_key=setting.chat_completion.openai_api_key.get_secret_value(), api_base=setting.chat_completion.openai_base_url, timeout=setting.chat_completion.request_timeout, model=setting.chat_completion.model, temperature=setting.chat_completion.temperature, max_retries=1, is_chat_model=True)

    def build_prompt(self, doc_item: DocItem, main_idea='', context_length=20000):
        """Generates system and user prompts based on the provided DocItem.

Enhances existing documentation by incorporating the main idea of the project.

Args:
    doc_item (DocItem): The document item containing metadata about a class or function.
    main_idea (str, optional): Main idea of the project to enhance existing documentation. Defaults to "".
    context_length (int, optional): Length of context for prompt generation. Defaults to 20000.

Returns:
    str: The generated system and user prompts based on the provided DocItem.

Note:
    See also: `repo_agent.chat_engine.ChatEngine.build_prompt`, `repo_agent.doc_meta_info.DocItem.get_full_name`.
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
            if len(doc_item.reference_who) == 0:
                return ''
            prompt = ['As you can see, the code calls the following objects, their code and docs are as following:']
            for reference_item in doc_item.reference_who:
                instance_prompt = f'obj: {reference_item.get_full_name()}\nDocument: \n{(reference_item.md_content[-1] if len(reference_item.md_content) > 0 else 'None')}\nRaw code:```\n{(reference_item.content['code_content'] if 'code_content' in reference_item.content.keys() else '')}\n```' + '=' * 10
                prompt.append(instance_prompt)
            return '\n'.join(prompt)

        def get_referencer_prompt(doc_item: DocItem) -> str:
            if len(doc_item.who_reference_me) == 0:
                return ''
            prompt = ['Also, the code has been called by the following objects, their code and docs are as following:']
            for referencer_item in doc_item.who_reference_me:
                instance_prompt = f'obj: {referencer_item.get_full_name()}\nDocument: \n{(referencer_item.md_content[-1] if len(referencer_item.md_content) > 0 else 'None')}\nRaw code:```\n{(referencer_item.content['code_content'] if 'code_content' in referencer_item.content.keys() else 'None')}\n```' + '=' * 10
                prompt.append(instance_prompt)
            return '\n'.join(prompt)

        def get_relationship_description(referencer_content, reference_letter):
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
        """Generates documentation for a given DocItem using an LLM.

Args:
    doc_item (DocItem): The document item containing metadata about a class or function.

Returns:
    str: The generated documentation content.

Raises:
    Exception: If an error occurs during the chat call with LLM.

Note:
    See also: `repo_agent.chat_engine.ChatEngine.build_prompt`, `repo_agent.doc_meta_info.DocItem.get_full_name`.
"""
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
        """Generate an idea based on the provided list of items.

This function leverages language models to generate creative ideas from a given list of components, each containing details such as name, description, and hierarchical placement.

Args:
    list_items (str): A string containing a detailed list of components, including their names, descriptions, and hierarchy positions.

Returns:
    str: The generated idea from the language model.

Raises:
    Exception: If there is an error during the chat call with the language model.
"""
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
        """Summarizes the given module description using language model interactions.

The Repository Agent framework leverages large language models to automatically generate comprehensive documentation for Python projects, including summarizing module contents.

Args:
    module_desc (str): The description of the module to be summarized.

Returns:
    str: The summary generated by the language model.

Raises:
    Exception: If an error occurs during the chat call with the language model.
    
Note:
    Uses `SettingsManager.get_setting()` to retrieve project settings and configure the chat messages.
"""
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