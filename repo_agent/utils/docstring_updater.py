import ast
import re

def update_doc(node, new_docstring):
    """
    Updates the docstring of an AST node.
    
    This method updates the docstring of an AST node with a new docstring. If the node does not have a docstring, it inserts a new one. If the node already has a docstring, it replaces the existing one. This is particularly useful in the context of automating documentation for a Git repository, where ensuring that code comments and docstrings are up-to-date is crucial.
    
    Args:
        node (ast.AST): The AST node to update.
        new_docstring (str): The new docstring to set.
    
    Returns:
        ast.AST: The updated AST node.
    
    Raises:
        TypeError: If `node` is not an instance of `ast.AST`.
    
    Note:
        The method ensures that the new docstring is properly indented based on the node type. If the node is not a module, an additional indentation level is applied. This helps maintain consistent and readable code documentation.
    
        This functionality is part of the `repo_agent` project, which automates the generation and management of documentation for Python projects within a Git repository. The project integrates various functionalities to detect changes, manage file handling, and generate documentation summaries, while also providing a command-line interface (CLI) for easy interaction. Additionally, it supports multi-threaded task management and configuration settings to customize the documentation generation process. The primary purpose of the `repo_agent` project is to streamline the documentation process for developers and maintainers of Python projects, reducing the manual effort required to keep documentation in sync with the codebase.
    """
    indent = '    ' if not isinstance(node, ast.Module) else ''
    lines = new_docstring.split('\n')
    if len(lines) > 1:
        lines[1:] = [indent + line for line in lines[1:]]
    processed_doc = '\n' + indent + '\n'.join(lines) + '\n' + indent
    if ast.get_docstring(node) is None:
        node.body.insert(0, ast.Expr(value=ast.Str(s=processed_doc)))
    else:
        node.body[0] = ast.Expr(value=ast.Str(s=processed_doc))
    return node

def remove_docstrings(code):
    """
    Removes docstrings from the given code.
    
    This method takes a string containing Python code and removes any docstrings from it. Docstrings are defined as triple-quoted strings that appear at the beginning of a function, class, or module. This is particularly useful in the context of the `repo_agent` project, which automates the generation and management of documentation for a Git repository, ensuring that only relevant code is processed for further tasks.
    
    Args:
        code (str): The Python code from which docstrings will be removed.
    
    Returns:
        str: The Python code with docstrings removed.
    
    Raises:
        None
    
    Note:
        This method uses a regular expression to identify and remove docstrings. It is important to ensure that the input code is well-formed to avoid unintended removal of string literals. This tool is part of a larger project aimed at streamlining documentation management in a Git environment, which includes automated detection of changes, file handling, and multi-task dispatch for efficient processing.
    """
    pattern = re.compile('^\\s*("""|\\\'\\\'\\\').*?^\\s*\\1', re.DOTALL | re.MULTILINE)
    return pattern.sub('', code)