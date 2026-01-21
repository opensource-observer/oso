import ast
import copy
import typing as t

from .utils import (
    collect_used_names,
    filter_imports,
    load_source_module,
    resolve_import_alias,
    resolve_relative_imports,
)


def default_private_methods_match(name: str) -> bool:
    return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))


def create_protocol_module(
    target: str,
    protocol_name: t.Optional[str] = None,
    extra_imports: t.Optional[t.List[ast.stmt]] = None,
    module_source_code: t.Optional[str] = None,
    include_star_imports: bool = False,
    private_methods_match: t.Callable[[str], bool] = default_private_methods_match,
) -> ast.Module:
    """
    Creates a typing.Protocol definition from a target class specified by string.
    """
    source_module, _, module_path, class_name = load_source_module(
        target, module_source_code
    )

    target_class_def = None
    for node in source_module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            target_class_def = node
            break

    if not target_class_def:
        raise ValueError(f"Could not find ClassDef for '{class_name}' in source")

    # Prepare Protocol Class
    protocol_cls = copy.deepcopy(target_class_def)

    # Reset bases immediately
    protocol_cls.bases = []

    if protocol_name:
        protocol_cls.name = protocol_name
    else:
        protocol_cls.name = f"{target_class_def.name}Protocol"

    # Strip bodies
    new_body: t.List[ast.stmt] = []
    for node in protocol_cls.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if private_methods_match(node.name):
                continue
            node.body = [ast.Expr(value=ast.Constant(value=...))]
            new_body.append(node)
        elif isinstance(node, ast.AnnAssign):
            node.value = None
            new_body.append(node)
        elif isinstance(node, ast.Assign):
            pass
        elif isinstance(node, ast.Pass):
            pass
        elif (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            new_body.append(node)
        else:
            pass
    protocol_cls.body = new_body

    # Collect used names in the protocol class
    used_names = collect_used_names(protocol_cls)

    # Filter imports from source module
    needed_imports = filter_imports(
        source_module,
        used_names,
        module_path=module_path,
        include_star_imports=include_star_imports,
    )

    # Resolve relative imports
    needed_imports = resolve_relative_imports(needed_imports, module_path)

    if extra_imports:
        needed_imports.extend(extra_imports)

    # Create module and resolve typing alias
    module_body = list(needed_imports)
    # Create temp module to analyze
    temp_mod = ast.Module(body=module_body, type_ignores=[])

    typing_alias, typing_import = resolve_import_alias(temp_mod, "typing", alias="t")

    if typing_import:
        module_body.insert(0, typing_import)

    # Set base class using resolved alias
    protocol_cls.bases = [
        ast.Attribute(
            value=ast.Name(id=typing_alias, ctx=ast.Load()),
            attr="Protocol",
            ctx=ast.Load(),
        )
    ]

    module_body.append(protocol_cls)

    module = ast.Module(body=module_body, type_ignores=[])
    ast.fix_missing_locations(module)

    return module
