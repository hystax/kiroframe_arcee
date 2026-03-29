import ast
from .utils import extract_string_value


def is_pandas_read_func(func_name: str):
    pandas_read_functions = {
        'read_csv',
        'read_excel',
        'read_json',
        'read_html',
        'read_xml',
        'read_parquet',
    }
    if func_name in pandas_read_functions:
        return True
    return False


def find_datasets(tree: ast.AST):
    """
    datasets - files read (or wrote by pandas) during the ml script execution
    # TODO: pandas.dataframes
    # TODO: create dataset from `sklearn.datasets.load_iris`
    """
    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # files read by open
                if node.func.id == 'open':
                    result.append({
                        "path": extract_string_value(node.args[0]),
                        "line": node.end_lineno,
                    })
                # check direct call (ex.: read_csv if 'from pandas import read_csv')
                elif node.func.id == 'pandas' or node.func.id == 'pd':
                    res = is_pandas_read_func(node.func.id)
                    if res:
                        result.append({
                            "path": extract_string_value(node.args[0]),
                            "line": node.end_lineno,
                        })
            # check if it's method (ex.: pd.read_csv)
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == 'pandas' or node.func.value.id == 'pd':
                        res = is_pandas_read_func(node.func.attr)
                        if res:
                            result.append({
                                "path": extract_string_value(node.args[0]),
                                "line": node.end_lineno,
                            })
    return result
