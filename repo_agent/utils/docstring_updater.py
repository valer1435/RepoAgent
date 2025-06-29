import ast
import re


def update_doc(node, new_docstring):
    """
    Replaces the docstring of a given AST node with new content, handling indentation to maintain code structure. If no docstring exists, it adds one; otherwise, it updates the existing one.

    Args:
        node: The AST node to update.
        new_docstring: The new docstring content.

    Returns:
        The updated AST node.

    """

    indent = "    " if not isinstance(node, ast.Module) else ""
    lines = new_docstring.split("\n")
    if len(lines) > 1:
        lines[1:] = [indent + line for line in lines[1:]]
    processed_doc = "\n" + indent + "\n".join(lines) + "\n" + indent
    if ast.get_docstring(node) is None:
        node.body.insert(0, ast.Expr(value=ast.Str(s=processed_doc)))
    else:
        node.body[0] = ast.Expr(value=ast.Str(s=processed_doc))
    return node


def remove_docstrings(code):
    """
    No valid docstring found.

    """

    pattern = re.compile(r'^\s*("""|\'\'\').*?^\s*\1', re.DOTALL | re.MULTILINE)
    return pattern.sub("", code)
