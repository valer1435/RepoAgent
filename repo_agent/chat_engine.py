from typing import List, Dict

from llama_index.llms.openai_like import OpenAILike

from repo_agent.doc_meta_info import DocItem
from repo_agent.log import logger
from repo_agent.prompt import chat_template, idea_chat_template, new_desc_chat_template, module_summary_template, \
    docstring_update_templates, docstring_update_chat_templates
from repo_agent.settings import SettingsManager


class ChatEngine:
    """
    ChatEngine is used to generate the doc of functions or classes.
    """

    def __init__(self, project_manager):
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
        """Builds and returns the system and user prompts based on the DocItem."""
        setting = SettingsManager.get_setting()

        code_info = doc_item.content
        referenced = len(doc_item.who_reference_me) > 0 and len(code_info) < 16000

        code_type = code_info["type"]
        code_name = code_info["name"]
        code_content = code_info["code_content"]
        have_return = code_info["have_return"]
        docstring = code_info['md_content'][-1] if  code_info['md_content'] else "Empty docstring"
        file_path = doc_item.get_full_name()

        def get_referenced_prompt(doc_item: DocItem) -> str:
            if len(doc_item.reference_who) == 0:
                return ""
            prompt = [
                """As you can see, the code calls the following objects, their code and docs are as following:"""
            ]
            for reference_item in doc_item.reference_who:
                instance_prompt = (
                        f"""obj: {reference_item.get_full_name()}\nDocument: \n{reference_item.md_content[-1] if len(reference_item.md_content) > 0 else 'None'}\nRaw code:```\n{reference_item.content['code_content'] if 'code_content' in reference_item.content.keys() else ''}\n```"""
                        + "=" * 10
                )
                prompt.append(instance_prompt)
            return "\n".join(prompt)

        def get_referencer_prompt(doc_item: DocItem) -> str:
            if len(doc_item.who_reference_me) == 0:
                return ""
            prompt = [
                """Also, the code has been called by the following objects, their code and docs are as following:"""
            ]
            for referencer_item in doc_item.who_reference_me:
                instance_prompt = (
                        f"""obj: {referencer_item.get_full_name()}\nDocument: \n{referencer_item.md_content[-1] if len(referencer_item.md_content) > 0 else 'None'}\nRaw code:```\n{referencer_item.content['code_content'] if 'code_content' in referencer_item.content.keys() else 'None'}\n```"""
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
            combine_ref_situation = "and combine it with its calling situation in the project,"
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
                main_idea=main_idea if not main_idea else f"You can use user-defined main idea of the project to enhance exist docstring\n{main_idea}",
                docstring=docstring,
                has_relationship=has_relationship,
                reference_letter=reference_letter,
                referencer_content=referencer_content,
                language=setting.project.language)
        else:
            return chat_template.format_messages(
                combine_ref_situation=combine_ref_situation,
                file_path=file_path,
                code_type_tell=code_type_tell,
                code_name=code_name,
                code_content=code_content,
                main_idea=main_idea if not main_idea else f"You can use user-defined main idea of the project to enhance exist docstring\n{main_idea}",
                docstring=docstring,
                has_relationship=has_relationship,
                reference_letter=reference_letter,
                referencer_content=referencer_content,
                language=setting.project.language)


    def generate_doc(self, doc_item: DocItem):
        """Generates documentation for a given DocItem."""
        settings = SettingsManager.get_setting()
        if settings.project.main_idea:
            messages = self.build_prompt(doc_item, main_idea=settings.project.main_idea)
        else:
            messages = self.build_prompt(doc_item)

        try:
            response = self.llm.stream_chat(messages)
            answer = ""
            for chunk in response:
                answer += chunk.delta
            # logger.debug(f"LLM Prompt Tokens: {response.raw.usage.prompt_tokens}")  # type: ignore
            # logger.debug(
            #     f"LLM Completion Tokens: {response.raw.usage.completion_tokens}"  # type: ignore
            # )
            # logger.debug(
            #     f"Total LLM Token Count: {response.raw.usage.total_tokens}"  # type: ignore
            # )
            print(answer)
            return answer.replace("```python\n", "").replace("```", "")
        except Exception as e:
            logger.error(f"Error in llamaindex chat call: {e}")
            raise

    def generate_idea(self, list_items: str):
        settings = SettingsManager.get_setting()
        messages = idea_chat_template.format_messages(components=list_items, language=settings.project.language)
        try:
            response = self.llm.chat(messages)
            logger.debug(f"LLM Prompt Tokens: {response.raw.usage.prompt_tokens}")  # type: ignore
            logger.debug(
                f"LLM Completion Tokens: {response.raw.usage.completion_tokens}"  # type: ignore
            )
            logger.debug(
                f"Total LLM Token Count: {response.raw.usage.total_tokens}"  # type: ignore
            )
            return response.message.content
        except Exception as e:
            logger.error(f"Error in llamaindex chat call: {e}")
            raise

    def summarize_module(self, module_desc: str):
        settings = SettingsManager.get_setting()
        messages = module_summary_template.format_messages(components=module_desc,
                                                           main_idea=settings.project.main_idea,
                                                           language=settings.project.language)
        try:
            response = self.llm.chat(messages)
            logger.debug(f"LLM Prompt Tokens: {response.raw.usage.prompt_tokens}")  # type: ignore
            logger.debug(
                f"LLM Completion Tokens: {response.raw.usage.completion_tokens}"  # type: ignore
            )
            logger.debug(
                f"Total LLM Token Count: {response.raw.usage.total_tokens}"  # type: ignore
            )
            return response.message.content
        except Exception as e:
            logger.error(f"Error in llamaindex chat call: {e}")
            raise
