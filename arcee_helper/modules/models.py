import ast


def _extract_arg_value(node):
    if isinstance(node, ast.Constant):
        return repr(node.value)
    elif isinstance(node, ast.Name):
        return node.id
    # TODO: func, attr
    return None


def _extract_args(call_node):
    args = []
    for arg in call_node.args:
        if isinstance(arg, ast.Constant):
            args.append(repr(arg.value))
        elif isinstance(arg, ast.Name):
            args.append(arg.id)
    for keyword in call_node.keywords:
        args.append(f"{keyword.arg}={_extract_arg_value(keyword.value)}")
    return args

def _get_full_attribute_name(node):
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return _get_full_attribute_name(node.value) + '.' + node.attr
    return ""


def find_models(tree: ast.AST):
    """
    models - some classes from sklern (for now just RandomForestClassifier)
    #TODO: more classes
    """
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for child in ast.walk(node.value):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        if child.func.id == 'RandomForestClassifier':
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    results.append({
                                        'name': target.id,
                                        'line': node.end_lineno,
                                        'args': _extract_args(child)
                                    })
                    elif isinstance(child.func, ast.Attribute):
                        # case 'sklearn.ensemble.RandomForestClassifier'
                        full_name = _get_full_attribute_name(child.func)
                        if 'RandomForestClassifier' in full_name:
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    results.append({
                                        'name': target.id,
                                        'line': node.end_lineno,
                                        'args': _extract_args(child)
                                    })
    return results
