import ast
import copy
import typing as t

from .utils import (
    collect_used_names,
    load_source_module,
    resolve_import_alias,
    resolve_relative_imports,
)


def create_fake_module(
    target: str,
    fake_name: t.Optional[str] = None,
    extra_imports: t.Optional[t.List[ast.stmt]] = None,
    module_source_code: t.Optional[str] = None,
) -> ast.Module:
    source_module, target_cls_obj, module_path, class_name = load_source_module(
        target, module_source_code
    )

    target_class_def: t.Optional[ast.ClassDef] = None
    for node in source_module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            target_class_def = node
            break

    if not target_class_def:
        raise ValueError(f"Could not find ClassDef for '{class_name}' in source")

    fake_cls = copy.deepcopy(target_class_def)
    if fake_name:
        fake_cls.name = fake_name
    else:
        fake_cls.name = f"Fake{target_class_def.name}"

    # Reset bases. We will add the Protocol base later.
    fake_cls.bases = []

    # Imports logic
    module_body: t.List[ast.stmt] = []

    used_names = collect_used_names(fake_cls)

    needed_imports: t.List[ast.stmt] = []
    for node in source_module.body:
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

    needed_imports = resolve_relative_imports(needed_imports, module_path)

    # Import the Protocol itself
    temp_mod = ast.Module(body=needed_imports, type_ignores=[])
    protocol_alias, protocol_import = resolve_import_alias(
        temp_mod, class_name, module_path=module_path
    )

    if protocol_import:
        needed_imports.append(protocol_import)

    fake_cls.bases = [ast.Name(id=protocol_alias, ctx=ast.Load())]

    # Implement methods with Polyfactory
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
                            factory_class = None
                            factory_module = None

                            # Check Pydantic
                            try:
                                import pydantic

                                if isinstance(return_type, type) and issubclass(
                                    return_type, pydantic.BaseModel
                                ):
                                    factory_class = "ModelFactory"
                                    factory_module = (
                                        "polyfactory.factories.pydantic_factory"
                                    )
                            except ImportError:
                                pass

                            # Check Dataclass
                            if not factory_class:
                                import dataclasses

                                if dataclasses.is_dataclass(return_type):
                                    factory_class = "DataclassFactory"
                                    factory_module = (
                                        "polyfactory.factories.dataclass_factory"
                                    )

                            # Check TypedDict
                            if not factory_class:
                                # Best effort TypedDict check
                                if (
                                    isinstance(return_type, type)
                                    and issubclass(return_type, dict)
                                    and hasattr(return_type, "__annotations__")
                                ):
                                    factory_class = "TypedDictFactory"
                                    factory_module = (
                                        "polyfactory.factories.typed_dict_factory"
                                    )

                            if factory_class and factory_module:
                                polyfactory_imports.add((factory_module, factory_class))

                                type_name = return_type.__name__

                                # Generate: return Factory.create_factory(Type).build()
                                factory_call = ast.Call(
                                    func=ast.Attribute(
                                        value=ast.Call(
                                            func=ast.Attribute(
                                                value=ast.Name(
                                                    id=factory_class, ctx=ast.Load()
                                                ),
                                                attr="create_factory",
                                                ctx=ast.Load(),
                                            ),
                                            args=[
                                                ast.Name(id=type_name, ctx=ast.Load())
                                            ],
                                            keywords=[],
                                        ),
                                        attr="build",
                                        ctx=ast.Load(),
                                    ),
                                    args=[],
                                    keywords=[],
                                )
                                factory_code = [ast.Return(value=factory_call)]
                except Exception:
                    pass

            if factory_code:
                node.body = t.cast(list[ast.stmt], factory_code)
            else:
                node.body = [ast.Expr(value=ast.Constant(value=...))]

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
