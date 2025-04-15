import ast
import os
import sys
import pkgutil
import importlib.util

# Get the list of stdlib modules to filter them out
stdlib_modules = {
    module.name for module in pkgutil.iter_modules()
    if module.module_finder.path == sys.base_prefix + '/lib/python' + sys.version[:3]
}

def is_stdlib_module(name):
    return name.split('.')[0] in stdlib_modules

#  Only analyze these custom modules
custom_modules_to_analyze = {
    'Users',
    'UserFactory',
    'User_Database_Interface',
    'Train_Database_Interface',
    'Web_Server_Backend',
    'email_manager_control',
    'email_interface',
    'calculate_congestion',
    'authentication',
    'API_Update_Controller',
    'ApiMallInterface'
}

class ModuleVisitor(ast.NodeVisitor):
    def __init__(self, source_lines):
        self.source_lines = source_lines
        self.classes = {}
        self.functions = []
        self.imports = set()
        self.current_class_stack = []

    def is_commented_out(self, node):
        try:
            segment = ast.get_source_segment(''.join(self.source_lines), node)
            if not segment:
                return True
            segment = segment.strip()
            return segment.startswith("#") or segment.startswith("'''") or segment.startswith('"""')
        except Exception:
            return False

    def visit_Import(self, node):
        for alias in node.names:
            if not is_stdlib_module(alias.name):
                self.imports.add(alias.name)

    def visit_ImportFrom(self, node):
        if node.module and not is_stdlib_module(node.module):
            self.imports.add(node.module)

    def visit_FunctionDef(self, node):
        if not self.current_class_stack and not self.is_commented_out(node):
            self.functions.append(node.name)

    def visit_ClassDef(self, node):
        class_name = ".".join(self.current_class_stack + [node.name])
        methods = []
        attrs = []

        self.current_class_stack.append(node.name)
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and not self.is_commented_out(item):
                methods.append(item.name)
            elif isinstance(item, ast.Assign) and not self.is_commented_out(item):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attrs.append(target.id)
        self.classes[class_name] = {'methods': methods, 'attributes': attrs}
        self.generic_visit(node)
        self.current_class_stack.pop()

def analyze_python_file(file_path):
    try:
        with open(file_path, 'r') as f:
            source = f.read()
            source_lines = source.splitlines(keepends=True)
            tree = ast.parse(source)
            visitor = ModuleVisitor(source_lines)
            visitor.visit(tree)
            return visitor
    except Exception as e:
        print(f" Error parsing {file_path}: {e}")
        return ModuleVisitor([])

def resolve_module_path(module_name):
    try:
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin and spec.origin.endswith(".py"):
            return spec.origin
    except Exception:
        return None
    return None

def generate_uml_recursive(file_path, analyzed_modules=None):
    if analyzed_modules is None:
        analyzed_modules = set()

    visitor = analyze_python_file(file_path)
    analyzed_modules.add(os.path.abspath(file_path))

    print(f"\n Analyzing file: {file_path}")

    # Print top-level functions
    if visitor.functions:
        print(f"\nTop-level functions in {os.path.basename(file_path)}:")
        for func in visitor.functions:
            print(f"  - function: {func}")

    # Print classes
    for class_name, content in visitor.classes.items():
        print(f"\nClass {class_name}:")
        for attr in content['attributes']:
            print(f"  - attribute: {attr}")
        for method in content['methods']:
            print(f"  - method: {method}")

    #  Only analyze selected modules
    for module in visitor.imports:
        module_base = module.split('.')[0]
        if module_base in custom_modules_to_analyze:
            module_path = resolve_module_path(module)
            if module_path and os.path.abspath(module_path) not in analyzed_modules:
                generate_uml_recursive(module_path, analyzed_modules)


def show_problematic_bytes(file_path, position):
    try:
        with open(file_path, 'rb') as file:  # Open the file in binary mode
            file.seek(position)  # Move the cursor to the problematic position
            byte = file.read(1)  # Read the byte at that position
            print(f"Problematic byte at position {position}: {byte}")
            
            # Read a few bytes before and after for context
            file.seek(position - 20)  # Read a bit before the position for context
            context_before = file.read(20)
            print(f"Context before position {position}: {context_before}")

            file.seek(position)  # Return to the problematic position
            context_after = file.read(20)  # Read a bit after the position for context
            print(f"Context after position {position}: {context_after}")

    except Exception as e:
        print(f"Error reading the file: {e}")

# Run this function to find the problematic part of the file
#file_path = r"C:\Users\myang\OneDrive\Documents\GitHub\2006-SCSA-M1\Lab 3\code space\Server.py"
#show_problematic_bytes(file_path, 36759)



# Entry point
if __name__ == "__main__":
    current_path = os.path.dirname(__file__)
    target_file = os.path.join(current_path, "Server.py")  # Specify the file to analyze
    generate_uml_recursive(target_file)



'''
import os

def check_files_for_encoding_issue(directory):
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(".py"):  # Only check Python files
                file_path = os.path.join(dirpath, filename)
                print(f"Checking file: {file_path}")  # See which files are being checked
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        file.read()  # Attempt to read the file
                except UnicodeDecodeError:
                    print(f" UnicodeDecodeError in file: {file_path}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
                
                # Try reading the file with alternative encodings
                for encoding in ["utf-8", "latin-1", "cp1252"]:
                    try:
                        with open(file_path, "r", encoding=encoding) as file:
                            file.read()  # Attempt to read with a different encoding
                        print(f" Successfully read {file_path} with {encoding} encoding.")
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        print(f"Error reading {file_path} with {encoding} encoding: {e}")

# Specify the root directory of your project
if __name__ == "__main__":
    project_directory = "C:/Users/myang/OneDrive/Documents/GitHub/2006-SCSA-M1/Lab 3/code space"
    check_files_for_encoding_issue(project_directory)
'''

new_custom_modules_to_analyze = {
    'Api_Mall_Interface',
    'API_Update_Controller',
    'authentication_control',
    'congestion_calculate_control',
    'email_interface',
    'email_manager_control',
    'Server',
    'Train_Database_Interface',
    'uml',
    'User_Database_Interface',
    'Users'
}


def gather_third_party_imports(custom_modules):
    all_imports = set()

    for module_name in custom_modules:
        module_path = resolve_module_path(module_name)
        if not module_path:
            print(f"Could not resolve path for {module_name}")
            continue

        visitor = analyze_python_file(module_path)
        for imp in visitor.imports:
            top_level_pkg = imp.split('.')[0]
            if not is_stdlib_module(imp) and top_level_pkg not in custom_modules:
                all_imports.add(top_level_pkg)

    print("\nExternal libraries used:")
    for lib in sorted(all_imports):
        print(lib)



gather_third_party_imports(new_custom_modules_to_analyze)