import ast


def update_doc(node, new_docstring):
    if ast.get_docstring(node) is None:
        #########################################
        # If no docstring exists, add one
        #########################################
        node.body.insert(0, ast.Expr(value=ast.Str(s=new_docstring)))
    else:
        #########################################
        # If docstring exists, replace it
        #########################################
        node.body[0].value.s = new_docstring
    return node

