import ast


def find_arcee_import(tree: ast.AST):
    """
    Finds the kiroframe_arcee import in the given tree
    """
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if any(x == "kiroframe_arcee"
                       for x in (alias.name, getattr(node, 'module', None))):
                    return True
    return False
