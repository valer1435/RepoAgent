from typing import List, Dict
from llama_index.llms.openai_like import OpenAILike
from repo_agent.doc_meta_info import DocItem
from repo_agent.log import logger
from repo_agent.prompt import (
    chat_template,
    idea_chat_template,
    new_desc_chat_template,
    module_summary_template,
    docstring_update_templates,
    docstring_update_chat_templates,
)
from repo_agent.settings import SettingsManager


class ChatEngine:
    """
    ChatEngine class for generating documentation and ideas using an LLM.

    This class provides methods to build prompts, generate documentation,
    generate ideas, and summarize module descriptions leveraging a language model."""

    def __init__(self, project_manager):
        """
        Initializes the chat engine with language model parameters retrieved from settings. These parameters include the API key, base URL, timeout, model name, and temperature.

        Args:
            project_manager: The project manager instance. This is used to access settings.

        Returns:
            None"""

        setting = SettingsManager.get_setting()
        self.llm = OpenAILike(
            context_window=20000,
            api_key=setting.chat_completion.openai_api_key.get_secret_value(),
            api_base=setting.chat_completion.openai_base_url,
            timeout=setting.chat_completion.request_timeout,
            model=setting.chat_completion.model,
            temperature=setting.chat_completion.temperature,
            max_retries=1,
            is_chat_model=True,
        )

    def build_prompt(self, doc_item: DocItem, main_idea="", context_length=20000):
        """
        Constructs a prompt for enhancing code documentation, incorporating details about the code's type, name, content, docstring, and file path. It also includes information about referencing and referenced objects, along with their associated documentation and code, to provide context and facilitate comprehensive updates. Optionally integrates a user-defined main idea to guide the enhancement process.

        Args:
            doc_item: A DocItem object containing code information and references.
            main_idea: An optional main idea to incorporate into the prompt.
            context_length: The maximum length of the context window (default is 20000).

        Returns:
            str: A formatted string representing the prompt for documentation enhancement.
        """

        setting = SettingsManager.get_setting()
        code_info = doc_item.content
        referenced = len(doc_item.who_reference_me) > 0 and len(code_info) < 16000
        code_type = code_info["type"]
        code_name = code_info["name"]
        code_content = code_info["code_content"]
        have_return = code_info["have_return"]
        docstring = (
            code_info["md_content"][-1]
            if code_info["md_content"]
            else "Empty docstring"
        )
        file_path = doc_item.get_full_name()

        def get_referenced_prompt(doc_item: DocItem) -> str:
            if len(doc_item.reference_who) == 0:
                return ""
            prompt = [
                "As you can see, the code calls the following objects, their code and docs are as following:"
            ]
            for reference_item in doc_item.reference_who:
                instance_prompt = (
                    f"obj: {reference_item.get_full_name()}\nDocument: \n{(reference_item.md_content[-1] if len(reference_item.md_content) > 0 else 'None')}\nRaw code:```\n{(reference_item.content['code_content'] if 'code_content' in reference_item.content.keys() else '')}\n```"
                    + "=" * 10
                )
                prompt.append(instance_prompt)
            return "\n".join(prompt)

        def get_referencer_prompt(doc_item: DocItem) -> str:
            if len(doc_item.who_reference_me) == 0:
                return ""
            prompt = [
                "Also, the code has been called by the following objects, their code and docs are as following:"
            ]
            for referencer_item in doc_item.who_reference_me:
                instance_prompt = (
                    f"obj: {referencer_item.get_full_name()}\nDocument: \n{(referencer_item.md_content[-1] if len(referencer_item.md_content) > 0 else 'None')}\nRaw code:```\n{(referencer_item.content['code_content'] if 'code_content' in referencer_item.content.keys() else 'None')}\n```"
                    + "=" * 10
                )
                prompt.append(instance_prompt)
            return "\n".join(prompt)

        def get_relationship_description(referencer_content, reference_letter):
            if referencer_content and reference_letter:
                return "And please include the reference relationship with its callers and callees in the project from a functional perspective"
            elif referencer_content:
                return "And please include the relationship with its callers in the project from a functional perspective."
            elif reference_letter:
                return "And please include the relationship with its callees in the project from a functional perspective."
            else:
                return ""

        code_type_tell = "Class" if code_type == "ClassDef" else "Function"
        if referenced:
            combine_ref_situation = (
                "and combine it with its calling situation in the project,"
            )
            referencer_content = get_referencer_prompt(doc_item)
            reference_letter = get_referenced_prompt(doc_item)
            has_relationship = get_relationship_description(
                referencer_content, reference_letter
            )
        else:
            combine_ref_situation = ""
            referencer_content = ""
            reference_letter = ""
            has_relationship = ""
        if main_idea:
            return docstring_update_chat_templates.format_messages(
                combine_ref_situation=combine_ref_situation,
                file_path=file_path,
                code_type_tell=code_type_tell,
                code_name=code_name,
                main_idea=(
                    main_idea
                    if not main_idea
                    else f"You can use user-defined main idea of the project to enhance exist docstring\n{main_idea}"
                ),
                docstring=docstring,
                has_relationship=has_relationship,
                reference_letter=reference_letter,
                referencer_content=referencer_content,
                language=setting.project.language,
            )
        else:
            return chat_template.format_messages(
                combine_ref_situation=combine_ref_situation,
                file_path=file_path,
                code_type_tell=code_type_tell,
                code_name=code_name,
                code_content=code_content,
                main_idea=(
                    main_idea
                    if not main_idea
                    else f"You can use user-defined main idea of the project to enhance exist docstring\n{main_idea}"
                ),
                docstring=docstring,
                has_relationship=has_relationship,
                reference_letter=reference_letter,
                referencer_content=referencer_content,
                language=setting.project.language,
            )

    def generate_doc(self, doc_item: DocItem):
        """
        Generates documentation for a given document item by constructing a prompt and querying a language model. The generated response is then post-processed to remove code formatting.

            Args:
                doc_item: The DocItem for which to generate documentation.
            Returns:
                str: The generated documentation string, with code block markers removed.
            Raises:
                Exception: If there is an error during the LLM chat call.
        """

        settings = SettingsManager.get_setting()
        if settings.project.main_idea:
            messages = self.build_prompt(doc_item, main_idea=settings.project.main_idea)
        else:
            messages = self.build_prompt(doc_item)
        try:
            response = self.llm.chat(messages)
            answer = response.message.content
            return answer.replace("```python\n", "").replace("```", "")
        except Exception as e:
            logger.error(f"Error in llamaindex chat call: {e}")
            raise

    def generate_idea(self, list_items: str):
        """
        Generates a creative concept or suggestion from provided components, leveraging language settings to tailor the output. It interacts with a large language model and logs token usage for monitoring purposes. Errors during LLM interaction are logged and re-raised.

            Args:
                list_items: A string containing the list of items to base the idea on.

            Returns:
                str: The generated idea as a string.  If an error occurs during the LLM chat call, it will be re-raised after logging.
        """

        settings = SettingsManager.get_setting()
        messages = idea_chat_template.format_messages(
            components=list_items, language=settings.project.language
        )
        try:
            response = self.llm.chat(messages)
            logger.debug(f"LLM Prompt Tokens: {response.raw.usage.prompt_tokens}")
            logger.debug(
                f"LLM Completion Tokens: {response.raw.usage.completion_tokens}"
            )
            logger.debug(f"Total LLM Token Count: {response.raw.usage.total_tokens}")
            return response.message.content
        except Exception as e:
            logger.error(f"Error in llamaindex chat call: {e}")
            raise

    def summarize_module(self, module_desc: str):
        """
        Generates a concise summary of a module’s functionality, leveraging project settings for context and language. The summary is produced by interacting with a large language model (LLM), and logging token usage for monitoring purposes.

            Args:
                module_desc: The description of the module to be summarized.

            Returns:
                str: The summary generated by the LLM.  Raises any exceptions encountered during the LLM call.
        """

        settings = SettingsManager.get_setting()
        messages = module_summary_template.format_messages(
            components=module_desc,
            main_idea=settings.project.main_idea,
            language=settings.project.language,
        )
        try:
            response = self.llm.chat(messages)
            logger.debug(f"LLM Prompt Tokens: {response.raw.usage.prompt_tokens}")
            logger.debug(
                f"LLM Completion Tokens: {response.raw.usage.completion_tokens}"
            )
            logger.debug(f"Total LLM Token Count: {response.raw.usage.total_tokens}")
            return response.message.content
        except Exception as e:
            logger.error(f"Error in llamaindex chat call: {e}")
            raise
