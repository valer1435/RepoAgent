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
    A class for generating documentation and ideas using a Language Model (LLM).

        This class provides methods to build prompts, generate documentation for code items,
        generate project ideas from lists of components, and summarize module descriptions.
        It interacts with an LLM to perform these tasks and handles potential errors during the process.
    """

    def __init__(self, project_manager):
        """
        Initializes the chat engine with language model parameters and API configurations retrieved from project settings.

            Args:
                project_manager: The project manager instance.  Not directly used in initialization but likely needed for later functionality.

            Returns:
                None
        """

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
        Constructs a prompt to enhance existing documentation by incorporating code details, relationships with other components, and optionally a user-provided main idea of the project. The prompt includes information about the code's type, name, content, docstring, file path, and its callers and callees if applicable.

            Args:
                doc_item: A DocItem object containing information about the code to document.
                main_idea: An optional user-defined main idea of the project to enhance the docstring.
                context_length: The maximum length of the context (not directly used in the provided code).

            Returns:
                str: A formatted prompt string for documentation enhancement, incorporating code details,
                     relationships with other code elements, and potentially a user-defined main idea.
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
        Generates documentation for a given code item by interacting with a language model, potentially incorporating project-level context. Handles potential errors during the LLM call and returns the generated text.

            This method constructs a prompt based on the DocItem and optional project main idea,
            sends it to the LLM for processing, and returns the generated documentation content.
            It handles potential errors during the LLM chat call and logs them if they occur.

            Args:
                doc_item: The DocItem object containing information about the item to document.

            Returns:
                str: The generated documentation content as a string, with code block markers removed.
                     Returns the response from the LLM after removing '```python
        ' and '```'.
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
        Generates a summary based on the provided list of components, utilizing language settings to tailor the output. It interacts with a language model to produce this summary and logs token usage for cost tracking.

            This method uses an LLM to create an idea from the provided components,
            formatted with messages according to project settings. It logs token usage
            from the LLM call and handles potential exceptions during the chat interaction.

            Args:
                list_items: A string representing a list of items or components for idea generation.

            Returns:
                str: The generated idea as a string, obtained from the LLM's response content.
                     Raises an exception if there is an error during the LLM chat call.
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
        Generates a summary for a module based on its description and project settings, utilizing a language model. The summary is formatted using a predefined template incorporating the module's components and project language. Token usage from the LLM call is logged for monitoring purposes.

            This method takes a module description as input, formats it with project settings
            (main idea and language), sends it to the LLM for summarization, and returns
            the LLM's response. It also logs token usage information from the LLM call.

            Args:
                module_desc: The description of the module to summarize.

            Returns:
                str: The summarized content generated by the LLM.

            Raises:
                Exception: If an error occurs during the LLM chat call, it is logged and re-raised.
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
