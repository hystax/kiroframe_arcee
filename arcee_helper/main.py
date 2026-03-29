import ast
import argparse
import difflib
import re
import shutil
import uuid
from pathlib import Path

from modules.arcee_import import find_arcee_import
from modules.artifacts import find_artifacts
from modules.datasets import find_datasets
from modules.metrics import find_metrics
from modules.models import find_models


class PythonFileAnalyzer:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.file_read_operations = []
        self.tree = None
        self.report = {
            "kiroframe_imported": None,
            "artifacts": [],
            "datasets": [],
            "metrics": [],
            "models": [],
        }
        self.rows = []

    def _analyze_tree(self):
        self.report["kiroframe_imported"] = find_arcee_import(self.tree)
        self.report["artifacts"] = find_artifacts(self.tree)
        self.report["datasets"] = find_datasets(self.tree)
        self.report["metrics"] = find_metrics(self.tree)
        self.report["models"] = find_models(self.tree)

    def print_report(self, token=None, task_key=None, url=None, ssl=False):

        def print_data(line_num, data):
            print(f"line {line_num}:")
            print(data)
            print("\n")

        print("#" * 100)
        if not self.report["kiroframe_imported"]:
            print("IMPORTS")
            print("Import kiroframe arcee in your script:\n")
            if token is None:
                token = str(uuid.UUID(int=0))
            if task_key is None:
                task_key = str(uuid.uuid4())
            init_params = f"'{token}', '{task_key}'"
            if url is not None:
                init_params += f", endpoint_url='{url}'"
            if ssl is not None:
                init_params += f", ssl={ssl}"
            text = (f"import kiroframe_arcee as arcee\n"
                    f"arcee.init({init_params})")
            self.rows.append({
                "line": 0,
                "text": text
            })
            print_data(0, text)
            print("#" * 100)

        if self.report["artifacts"]:
            print("ARTIFACTS")
            print("Found potential artifacts. Add the following lines to log them:\n")
            for artifact in self.report["artifacts"]:
                text = "arcee.artifact('{}')".format(artifact["path"])
                self.rows.append({
                    "line": artifact["line"] + 1,
                    "text": text
                })
                print_data(artifact["line"] + 1, text)
            print("#" * 100)

        if self.report["datasets"]:
            print("DATASETS")
            print("Found potential datasets. Add the following lines to log them:\n")
            for dataset in self.report["datasets"]:
                text = (f"ds = arcee.Dataset('{dataset["path"]}')\n"
                        f"ds.add_file('{dataset["path"]}')\n"
                        f"arcee.log_dataset(ds)")
                line = dataset["line"] + 1
                self.rows.append({
                    "line": line,
                    "text": text
                })
                print_data(dataset["line"] + 1, text)
            print("#" * 100)

        if self.report["metrics"]:
            print("METRICS")
            print("Found potential metrics. Add the following lines to log them:\n")
            for metric in self.report["metrics"]:
                var_name = metric["name"]
                text = "arcee.send({'" + var_name + "': " + var_name + "})"
                self.rows.append({
                    "line": metric["line"] + 1,
                    "text": text
                })
                print_data(metric["line"] + 1, text)
            print("#" * 100)

        if self.report["models"]:
            print("MODELS")
            print("Found using models. Add the following lines to log them:\n")
            for model in self.report["models"]:
                text = (f"arcee.model('{model["name"]}')\n"
                        f"arcee.model_version(1)")
                for arg in model["args"]:
                    k, v = arg.split("=")
                    text += f"\narcee.model_version_tag('{k}', '{v}')"
                self.rows.append({
                    "line": model["line"] + 1,
                    "text": text
                })
                print_data(model["line"] + 1, text)
            print("#" * 100)

    @staticmethod
    def _insert_lines_with_indent(input_path, output_path, lines_to_insert):
        lines_to_insert = sorted(lines_to_insert, key=lambda x: x["line"])

        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        line_offset = -1
        for insertion in lines_to_insert:
            line_num = insertion["line"] + line_offset
            text = insertion["text"]

            base_indent = ""

            if line_num < len(lines):
                current_line = lines[line_num]
                indent_match = re.match(r'^[ \t]*', current_line)
                base_indent = indent_match.group(0) if indent_match else ""

                if not current_line.strip():
                    for i in range(line_num - 1, -1, -1):
                        if lines[i].strip():
                            indent_match = re.match(r'^[ \t]*', lines[i])
                            base_indent = indent_match.group(0) if indent_match else ""
                            break

                    if not base_indent.strip():
                        for i in range(line_num, len(lines)):
                            if lines[i].strip():
                                indent_match = re.match(r'^[ \t]*', lines[i])
                                base_indent = indent_match.group(0) if indent_match else ""
                                break

            lines_to_add = text.split('\n')
            for i, line in enumerate(lines_to_add):
                if line_num == -1:
                    line_num = 0
                lines.insert(line_num + i, base_indent + line + '\n')
                line_offset += 1

        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def save_to_file(self, output_file_path):
        print(f"Creating file with recommended arcee "
              f"usage: {output_file_path}")
        shutil.copy2(self.file_path, output_file_path)
        self._insert_lines_with_indent(self.file_path, output_file_path,
                                       self.rows)

    def print_diff(self, output_file_path):
        with open(str(self.file_path), 'r', encoding='utf-8') as f1, \
                open(output_file_path, 'r', encoding='utf-8') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
            diff = difflib.unified_diff(
                lines1, lines2,
                fromfile=str(self.file_path),
                tofile=output_file_path,
                lineterm=''
            )
            for line in diff:
                if line.startswith('+'):
                    print(f"\033[92m{line}\033[0m")  # green
                elif line.startswith('-'):
                    print(f"\033[91m{line}\033[0m")  # red
                elif line.startswith('@@'):
                    print(f"\033[94m{line}\033[0m")  # blue
                else:
                    print(line)

    def analyze(self):
        if not self.file_path.exists():
            print(f"File {self.file_path} not found!")
            return False

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.tree = ast.parse(content)
            self._analyze_tree()
            return True
        except SyntaxError as e:
            print(f"Syntax error: {str(e)}")
            return False
        # except Exception as e:
        #     print(f"Error: {str(e)}")
        #     return False


def main():
    # TODO: handle already added arcee rows
    # TODO: alias for script
    # TODO: arcee.finish()
    DESCRIPTION = ("Usage: python main.py file_path <-o new_file_path>.\n"
                   "Example: python main.py myscript.py -o new_myscript.py\n")
    parser = argparse.ArgumentParser(
        description=DESCRIPTION)
    parser.add_argument('path', help='ML script file path to analyze')
    parser.add_argument('--token', help='Profiling token used in arcee.init()',
                        required=False)
    parser.add_argument('--task_key', help='Task key used in arcee.init()',
                        required=False)
    parser.add_argument('--url', help='Cluster url used in arcee.init()',
                        required=False, default='https://my.kiroframe.com/arcee/v2')
    parser.add_argument('--no_ssl', help='Enable/disable SSL checks in arcee.init()',
                        action='store_false', required=False)
    parser.add_argument('-o', '--output', help='Output file path', required=False)
    parser.add_argument('--diff', help='Print diff between input and output files',
                        required=False, action='store_true')
    args = parser.parse_args()

    analyzer = PythonFileAnalyzer(args.path)
    analyzer.analyze()
    analyzer.print_report(args.token, args.task_key, args.url, args.no_ssl)

    if args.output:
        analyzer.save_to_file(args.output)
        print("#" * 100)
        if args.diff:
            analyzer.print_diff(args.output)

    print("#" * 100)
    print("Script finished successfully!")


if __name__ == "__main__":
    main()
