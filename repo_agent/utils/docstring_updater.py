import ast

def update_doc(node, new_docstring):

    indent = '    ' if not isinstance(node, ast.Module) else ''
    lines = new_docstring.split('\n')
    if len(lines) > 1:
        lines[1:] = [indent + line for line in lines[1:]]
    processed_doc = '\n'.join(lines)

    if ast.get_docstring(node) is None:
        node.body.insert(0, ast.Expr(value=ast.Str(s=processed_doc)))
    else:
        node.body[0].value.s = processed_doc
    return node