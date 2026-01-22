import ast
import copy
import dataclasses
import typing as t

import pydantic

from .utils import (
    collect_used_names,
    filter_imports,
    find_class_def,
    load_source_module,
    resolve_import_alias,
    resolve_relative_imports,
)


def _determine_factory_info(return_type: t.Any) -> t.Optional[t.Tuple[str, str]]:
    """Determines the factory class and module for a given return type.

    Args:
        return_type: The return type to analyze.

    Returns:
        A tuple of (factory_module, factory_class) if supported, else None.
    """
    # Check Pydantic
    if isinstance(return_type, type) and issubclass(return_type, pydantic.BaseModel):
        return "polyfactory.factories.pydantic_factory", "ModelFactory"

    if dataclasses.is_dataclass(return_type):
        return "polyfactory.factories.dataclass_factory", "DataclassFactory"

    # Check TypedDict
    # Best effort TypedDict check
    if (
        isinstance(return_type, type)
        and issubclass(return_type, dict)
        and hasattr(return_type, "__annotations__")
    ):
        return "polyfactory.factories.typed_dict_factory", "TypedDictFactory"

    return None


def _create_factory_call(factory_class: str, return_type_name: str) -> t.List[ast.stmt]:
    """Creates the AST for the factory call.

    return Factory.create_factory(Type).build()

    Args:
        factory_class: The name of the factory class.
        return_type_name: The name of the return type.

    Returns:
        A list of statements containing the return statement.
    """
    factory_call = ast.Call(
        func=ast.Attribute(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id=factory_class, ctx=ast.Load()),
                    attr="create_factory",
                    ctx=ast.Load(),
                ),
                args=[ast.Name(id=return_type_name, ctx=ast.Load())],
                keywords=[],
            ),
            attr="build",
            ctx=ast.Load(),
        ),
        args=[],
        keywords=[],
    )
    return [ast.Return(value=factory_call)]


def _implement_fake_methods(
    fake_cls: ast.ClassDef, target_cls_obj: t.Optional[t.Any]
) -> t.Set[t.Tuple[str, str]]:
    """Implements methods in the fake class using Polyfactory.

    Args:
        fake_cls: The fake class definition to modify.
        target_cls_obj: The runtime object of the target class for type hint resolution.

    Returns:
        A set of tuples (module, class) for required factory imports.
    """
    polyfactory_imports: t.Set[t.Tuple[str, str]] = set()

    for node in fake_cls.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            factory_code = None

            if target_cls_obj:
                try:
                    # Resolve type hints for the method
                    method_obj = getattr(target_cls_obj, node.name, None)
                    if method_obj:
                        method_hints = t.get_type_hints(method_obj)
                        return_type = method_hints.get("return")

                        if return_type:
                            factory_info = _determine_factory_info(return_type)
                            if factory_info:
                                factory_module, factory_class = factory_info
                                polyfactory_imports.add((factory_module, factory_class))
                                factory_code = _create_factory_call(
                                    factory_class, return_type.__name__
                                )
                except Exception:
                    pass

            if factory_code:
                node.body = t.cast(list[ast.stmt], factory_code)
            else:
                node.body = [ast.Expr(value=ast.Constant(value=...))]

    return polyfactory_imports


def create_fake_module(
    target: str,
    fake_name: t.Optional[str] = None,
    extra_imports: t.Optional[t.List[ast.stmt]] = None,
    module_source_code: t.Optional[str] = None,
) -> ast.Module:
    source_module, target_cls_obj, module_path, class_name = load_source_module(
        target, module_source_code
    )

    target_class_def = find_class_def(source_module, class_name)
    if not target_class_def:
        raise ValueError(f"Could not find ClassDef for '{class_name}' in source")

    fake_cls = copy.deepcopy(target_class_def)
    if fake_name:
        fake_cls.name = fake_name
    else:
        fake_cls.name = f"Fake{target_class_def.name}"

    # Reset bases. We will add the Protocol base later.
    fake_cls.bases = []

    used_names = collect_used_names(fake_cls)
    needed_imports = filter_imports(source_module, used_names, module_path=module_path)
    needed_imports = resolve_relative_imports(needed_imports, module_path)

    # Import the Protocol itself
    temp_mod = ast.Module(body=needed_imports, type_ignores=[])
    protocol_alias, protocol_import = resolve_import_alias(
        temp_mod, class_name, module_path=module_path
    )

    if protocol_import:
        needed_imports.append(protocol_import)

    fake_cls.bases = [ast.Name(id=protocol_alias, ctx=ast.Load())]

    # Implement methods
    polyfactory_imports = _implement_fake_methods(fake_cls, target_cls_obj)

    # Add polyfactory imports
    # We insert them at the top of needed_imports
    # Resolve aliases for factories
    for mod, cls in polyfactory_imports:
        temp_mod = ast.Module(body=needed_imports, type_ignores=[])
        alias, stmt = resolve_import_alias(temp_mod, cls, module_path=mod)
        if stmt:
            needed_imports.insert(0, stmt)

    module_body = list(needed_imports)
    if extra_imports:
        module_body.extend(extra_imports)

    module_body.append(fake_cls)

    module = ast.Module(body=module_body, type_ignores=[])
    ast.fix_missing_locations(module)
    return module
