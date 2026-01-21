import ast
import copy
import importlib
import inspect
import typing as t


class NameCollector(ast.NodeVisitor):
    """Visitor that collects all used names in an AST node."""

    def __init__(self) -> None:
        self.names: t.Set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.names.add(node.id)
        self.generic_visit(node)


def collect_used_names(node: ast.AST) -> t.Set[str]:
    """Collects all names used in an AST node.

    Args:
        node: The AST node to traverse.

    Returns:
        A set of strings representing the names used in the node.
    """
    collector = NameCollector()
    collector.visit(node)
    return collector.names


def resolve_import_alias(
    module: ast.Module,
    name: str,
    module_path: t.Optional[str] = None,
    alias: t.Optional[str] = None,
) -> t.Tuple[str, t.Optional[ast.stmt]]:
    """Finds or creates an import alias for a given name.

    Checks if the name is already imported in the module. If so, returns existing alias.
    If not, determines a non-conflicting alias (using provided alias preference or name)
    and generates the appropriate import statement.

    Args:
        module: The AST module to analyze for existing imports/names.
        name: The name to import.
        module_path: The module path to import from (None for top-level import).
        alias: A preferred alias to use.

    Returns:
        A tuple containing:
        - The alias to use (str).
        - The import statement to add (Optional[ast.stmt]). None if import exists.
    """
    used_names = set()
    existing_alias = None

    for node in module.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                used_names.add(n.asname or n.name)
                if module_path is None and n.name == name:
                    existing_alias = n.asname or n.name
        elif isinstance(node, ast.ImportFrom):
            for n in node.names:
                used_names.add(n.asname or n.name)
                if (
                    module_path is not None
                    and node.module == module_path
                    and n.name == name
                ):
                    existing_alias = n.asname or n.name
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            used_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    used_names.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                used_names.add(node.target.id)

    if existing_alias:
        return existing_alias, None

    candidates = []
    if alias:
        candidates.append(alias)

    if name not in candidates:
        candidates.append(name)

    base = alias or name
    candidates.append(f"{base}_generated")

    final_alias = None
    for cand in candidates:
        if cand not in used_names:
            final_alias = cand
            break

    if not final_alias:
        i = 1
        while True:
            cand = f"{base}_generated_{i}"
            if cand not in used_names:
                final_alias = cand
                break
            i += 1

    if module_path:
        stmt = ast.ImportFrom(
            module=module_path,
            names=[
                ast.alias(
                    name=name, asname=final_alias if final_alias != name else None
                )
            ],
            level=0,
        )
    else:
        stmt = ast.Import(
            names=[
                ast.alias(
                    name=name, asname=final_alias if final_alias != name else None
                )
            ]
        )

    return final_alias, stmt


def resolve_relative_imports(
    imports: t.List[ast.stmt], module_name: str
) -> t.List[ast.stmt]:
    """Resolves relative imports to absolute imports.

    Args:
        imports: List of import statements.
        module_name: The absolute name of the module where imports originate.

    Returns:
        A new list of import statements with relative imports resolved.

    Raises:
        ValueError: If a relative import attempts to go beyond the top-level package.
    """
    parts = module_name.split(".")
    # Package is everything up to the last part (the module itself)
    package_parts = parts[:-1]

    resolved_imports: t.List[ast.stmt] = []

    for node in imports:
        if isinstance(node, ast.ImportFrom) and node.level > 0:
            # Create a copy to modify
            new_node = copy.deepcopy(node)
            level = new_node.level
            # level 1 = current package
            # level 2 = parent
            steps_up = level - 1

            if steps_up > len(package_parts):
                raise ValueError(
                    f"Relative import level {level} is out of bounds for module {module_name}"
                )

            if steps_up == 0:
                base_parts = package_parts
            else:
                base_parts = package_parts[:-steps_up]

            base_module = ".".join(base_parts)

            if new_node.module:
                absolute_module = (
                    f"{base_module}.{new_node.module}"
                    if base_module
                    else new_node.module
                )
            else:
                absolute_module = base_module

            new_node.module = absolute_module
            new_node.level = 0
            resolved_imports.append(new_node)
        else:
            resolved_imports.append(node)

    return resolved_imports


def load_source_module(
    target: str, module_source_code: t.Optional[str] = None
) -> t.Tuple[ast.Module, t.Optional[t.Any], str, str]:
    """Loads source AST and runtime class from a target string.

    Args:
        target: Import path in 'module.path:Class' format.
        module_source_code: Optional source code to use instead of reading from file.

    Returns:
        A tuple containing:
        - The parsed AST module (ast.Module).
        - The runtime class object (Optional[Any]), None if using source code string.
        - The module path (str).
        - The class name (str).

    Raises:
        ValueError: If parsing or importing fails.
    """
    try:
        module_path, class_name = target.split(":")
    except ValueError:
        raise ValueError("target must be in the format 'module.path:Class'")

    source_module: ast.Module
    target_cls_obj: t.Optional[t.Any] = None

    if module_source_code is not None:
        try:
            source_module = ast.parse(module_source_code)
        except Exception as e:
            raise ValueError(f"Could not parse provided source code: {e}")
    else:
        try:
            module = importlib.import_module(module_path)
            target_cls_obj = getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ValueError(
                f"Could not import class '{class_name}' from '{module_path}': {e}"
            )

        if not inspect.isclass(target_cls_obj):
            raise ValueError(f"'{target}' is not a class")

        try:
            source_file = inspect.getfile(target_cls_obj)
            with open(source_file, "r") as f:
                source_code = f.read()
            source_module = ast.parse(source_code)
        except Exception as e:
            raise ValueError(f"Could not parse source file: {e}")

    return source_module, target_cls_obj, module_path, class_name


def find_class_def(module: ast.Module, class_name: str) -> t.Optional[ast.ClassDef]:
    """Finds a ClassDef node by name in a module's body.

    Args:
        module: The AST module to search.
        class_name: The name of the class to find.

    Returns:
        The ClassDef node if found, otherwise None.
    """
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    return None


def filter_imports(module: ast.Module, used_names: t.Set[str]) -> t.List[ast.stmt]:
    """Filters imports in a module to only include those that are used.

    Args:
        module: The AST module containing imports.
        used_names: A set of names that are used and should be kept.

    Returns:
        A list of filtered import statements.
    """
    needed_imports: t.List[ast.stmt] = []
    for node in module.body:
        if isinstance(node, ast.Import):
            filtered_names = [
                n for n in node.names if (n.asname or n.name) in used_names
            ]
            if filtered_names:
                new_node = copy.deepcopy(node)
                new_node.names = filtered_names
                needed_imports.append(new_node)
        elif isinstance(node, ast.ImportFrom):
            filtered_names = [
                n for n in node.names if (n.asname or n.name) in used_names
            ]
            if filtered_names:
                new_node = copy.deepcopy(node)
                new_node.names = filtered_names
                needed_imports.append(new_node)
    return needed_imports
