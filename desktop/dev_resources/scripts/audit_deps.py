import ast
import os
import sys

def get_imports(file_path):
    """Parse file and return a list of imported module names."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
            elif node.level > 0:
                # Handle relative imports (naive approach for now)
                pass 
    return imports

def resolve_module_to_file(module_name, base_dir):
    """Convert module name to file path."""
    parts = module_name.split('.')
    
    # Check for direct file match (package/module.py)
    path = os.path.join(base_dir, *parts) + '.py'
    if os.path.exists(path):
        return path
    
    # Check for package init (package/module/__init__.py)
    path = os.path.join(base_dir, *parts, '__init__.py')
    if os.path.exists(path):
        return path
        
    return None

def trace_dependencies(entry_file, base_dir):
    queue = [entry_file]
    visited = set()
    reachable = set()

    while queue:
        current_file = queue.pop(0)
        if current_file in visited:
            continue
        visited.add(current_file)
        reachable.add(current_file)

        # Get imports
        imports = get_imports(current_file)
        
        # Resolve imports
        for mod in imports:
            resolved = resolve_module_to_file(mod, base_dir)
            if resolved and resolved not in visited:
                queue.append(resolved)
                
    return reachable

if __name__ == "__main__":
    base_dir = os.getcwd()
    entry_point = os.path.join(base_dir, "ppcsuite_v4_ui_experiment.py")
    
    print(f"Tracing dependencies from: {entry_point}")
    reachable_files = trace_dependencies(entry_point, base_dir)
    
    print("\n--- Reachable Files ---")
    for f in sorted(reachable_files):
        print(os.path.relpath(f, base_dir))
