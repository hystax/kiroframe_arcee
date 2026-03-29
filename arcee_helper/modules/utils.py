import ast


def extract_string_value(node):
    # string
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    # f-string
    elif isinstance(node, ast.JoinedStr):
        parts = []
        for part in node.values:
            if isinstance(part, ast.Constant):
                parts.append(str(part.value))
            elif isinstance(part, ast.FormattedValue):
                # f"{variable}"
                parts.append(f"{{{extract_string_value(part.value)}}}")
        return ''.join(parts) if parts else None
    # BinOp object (str concat)
    elif isinstance(node, ast.BinOp):
        left = extract_string_value(node.left)
        right = extract_string_value(node.right)
        if left is not None and right is not None:
            # str + str
            if isinstance(node.op, ast.Add):
                return left + right
            # str / str
            elif isinstance(node.op, ast.Div):
                return f"{left}/{right}"
            return None
    elif isinstance(node, ast.Name):
        return node.id
    return None