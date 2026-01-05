import ast


def find_metrics(tree: ast.AST):
    """
    metric - int or float variable used in print
    # TODO: support logging
    # TODO: support saving to file?
    """
    result = []
    args = []
    assignments = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'print':
                for arg in node.args:
                    if isinstance(arg, ast.Name):
                        args.append((arg, node.end_lineno))
                    elif isinstance(arg, ast.BinOp):
                        # binary operation (ex.: a + b)
                        if isinstance(arg.left, ast.Name):
                            args.append((arg.left, node.end_lineno))
                        if isinstance(arg.right, ast.Name):
                            args.append((arg.right, node.end_lineno))
                    elif isinstance(arg, ast.UnaryOp):
                        # unary operation (ex.: -a)
                        args.append((arg, node.end_lineno))
                    # TODO:
                    elif isinstance(arg, ast.Attribute):
                        # object attribute
                        continue
                    elif isinstance(arg, ast.Call):
                        # call some func (ex.: int(x))
                        continue
                    elif isinstance(arg, ast.Subscript):
                        # index (ex.: a[0])
                        continue
                    # TODO: support print(f"\n✅ Best Validation Loss: {best_val_loss:.4f}")
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if isinstance(node.value, ast.Constant):
                        if isinstance(node.value.value, (int, float)):
                            assignments.append(target.id)
                    elif isinstance(node.value, ast.Call):
                        # funcs like a = int(b)
                        if isinstance(node.value.func, ast.Name):
                            if node.value.func.id in ['int', 'float']:
                                assignments.append(target.id)
    for data in args:
        arg, lineno = data
        if arg.id in assignments:
            result.append({
                'name': arg.id,
                'line': lineno,
            })
    return result
