import os

from repo_agent.main import run_outside_cli

os.environ['OPENAI_API_KEY'] = 'token-abc123'

run_outside_cli(
    '/model',
    0.1,
    180,
    'http://10.32.2.11:8031/v1',
    r'E:\programming\ra',
    hierarchy_path='.project_doc_record',
    markdown_docs_path='docs_',
    ignore_list=".venv,tests,deployment,examples,alembic,docs,tests,test,projects,benchmarks,cmake,csrc,docs,examples,tests,tools",
    language='English',
    max_thread_count=6,
    log_level='INFO',
    print_hierarchy=True
)

# run_outside_cli(
#     'qwen2.5-14b-instruct',
#     0.1,
#     180,
#     'http://127.0.0.1:1234/v1',
#     r'E:\programming\RepoCopilot',
#     hierarchy_path='.project_doc_record',
#     markdown_docs_path='docs',
#     ignore_list=".venv,tests,deployment,examples,alembic,docs,tests,test,projects,benchmarks,cmake,csrc,docs,examples,tools",
#     language='English',
#     max_thread_count=1,
#     log_level='INFO',
#     print_hierarchy=True
# )
#
# import os
# from openai import OpenAI
#
# client = OpenAI(
#     base_url='http://10.32.2.11:8031/v1',
#     api_key="token-abc123",  # This is the default and can be omitted
# )
#
# chat_completion = client.chat.completions.create(
#     messages=[
#         {
#             "role": "user",
#             "content": "Who are you?",
#         }
#     ],
#     model="/model",
# )
# print(chat_completion.choices[0].message.content)
