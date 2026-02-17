import ast
from .utils import extract_string_value


def find_artifacts(tree: ast.AST):
    """
    artifacts - files wrote during the ml script execution
    """
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # files write by 'open'
                if node.func.id == 'open':
                    # TODO: mode in kwargs?
                    if node.args[1].value != 'r':
                        results.append({
                            "path": extract_string_value(node.args[0]),
                            "line": node.end_lineno,
                        })
        # TODO: savefig for plot
        # TODO: pandas write
    return results
