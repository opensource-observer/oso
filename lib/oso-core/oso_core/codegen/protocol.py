import ast
import copy
import importlib
import inspect
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .utils import (
    collect_used_names,
    filter_imports,
    load_source_module,
    resolve_import_alias,
    resolve_relative_imports,
)


@dataclass
class ProtocolMethod:
    name: str
    args: ast.arguments
    return_annotation: t.Optional[ast.expr]
    decorators: t.List[ast.expr]
    is_async: bool
    type_params: t.List[ast.AST] = field(default_factory=list)
    docstring: t.Optional[str] = None


@dataclass
class ProtocolAttribute:
    name: str
    annotation: t.Optional[ast.expr]
    value: t.Optional[ast.expr]
    docstring: t.Optional[str] = None


@dataclass
class ProtocolIR:
    name: str
    methods: t.List[ProtocolMethod]
    attributes: t.List[ProtocolAttribute]
    imports: t.List[ast.stmt]
    bases: t.List[ast.expr]


class ProtocolTransformer(ABC):
    @abstractmethod
    def transform(self, target: str) -> ProtocolIR:
        pass


class ASTProtocolTransformer(ProtocolTransformer):
    def __init__(
        self,
        module_source_code: t.Optional[str] = None,
        include_star_imports: bool = False,
        private_methods_match: t.Optional[t.Callable[[str], bool]] = None,
    ):
        self.module_source_code = module_source_code
        self.include_star_imports = include_star_imports
        self.private_methods_match = (
            private_methods_match or default_private_methods_match
        )

    def transform(self, target: str) -> ProtocolIR:
        source_module, _, module_path, class_name = load_source_module(
            target, self.module_source_code
        )

        target_class_def = None
        for node in source_module.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                target_class_def = node
                break

        if not target_class_def:
            raise ValueError(f"Could not find ClassDef for '{class_name}' in source")

        methods: t.List[ProtocolMethod] = []
        attributes: t.List[ProtocolAttribute] = []

        # Analyze body
        for node in target_class_def.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self.private_methods_match(node.name):
                    continue

                methods.append(
                    ProtocolMethod(
                        name=node.name,
                        args=copy.deepcopy(node.args),
                        return_annotation=copy.deepcopy(node.returns),
                        decorators=copy.deepcopy(node.decorator_list),
                        is_async=isinstance(node, ast.AsyncFunctionDef),
                        type_params=copy.deepcopy(getattr(node, "type_params", [])),
                        docstring=ast.get_docstring(node),
                    )
                )
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    attributes.append(
                        ProtocolAttribute(
                            name=node.target.id,
                            annotation=copy.deepcopy(node.annotation),
                            value=copy.deepcopy(node.value),
                        )
                    )

        # Collect used names to filter imports
        used_names = set()

        def add_used(node: t.Optional[ast.AST]):
            if node:
                used_names.update(collect_used_names(node))

        for m in methods:
            add_used(m.args)
            add_used(m.return_annotation)
            for d in m.decorators:
                add_used(d)
            for tp in m.type_params:
                add_used(tp)

        for a in attributes:
            add_used(a.annotation)

        needed_imports = filter_imports(
            source_module,
            used_names,
            module_path=module_path,
            include_star_imports=self.include_star_imports,
        )

        needed_imports = resolve_relative_imports(needed_imports, module_path)

        return ProtocolIR(
            name=target_class_def.name,
            methods=methods,
            attributes=attributes,
            imports=needed_imports,
            bases=[],
        )


class InspectProtocolTransformer(ProtocolTransformer):
    def __init__(
        self, private_methods_match: t.Optional[t.Callable[[str], bool]] = None
    ):
        self.private_methods_match = (
            private_methods_match or default_private_methods_match
        )
        self.imports_map: t.Dict[str, t.Set[str]] = {}  # module -> {names}

    def _add_import(self, module: str, name: str):
        if module == "builtins":
            return
        if module not in self.imports_map:
            self.imports_map[module] = set()
        self.imports_map[module].add(name)

    def _type_to_ast(self, type_obj: t.Any) -> t.Optional[ast.expr]:
        if type_obj is inspect.Parameter.empty:
            return None
        if type_obj is None:
            return ast.Constant(value=None)

        # Handle string forward refs
        if isinstance(type_obj, str):
            try:
                # ast.parse returns Module -> Expr -> value
                expr = ast.parse(type_obj, mode="eval").body
                if isinstance(expr, ast.expr):
                    return expr
                return ast.Name(id=type_obj, ctx=ast.Load())  # Fallback
            except SyntaxError:
                return ast.Name(id=type_obj, ctx=ast.Load())

        # Handle Generics
        origin = getattr(type_obj, "__origin__", None)
        if origin is not None:
            # Special handling for typing generics
            args = getattr(type_obj, "__args__", ())

            # Map origin to AST name
            origin_ast = self._type_to_ast(origin)

            if not args:
                return origin_ast

            if origin_ast:
                args_ast = [
                    self._type_to_ast(a) or ast.Name(id="Any", ctx=ast.Load())
                    for a in args
                ]

                # Construct subscript
                slice_val = (
                    ast.Tuple(elts=args_ast, ctx=ast.Load())
                    if len(args) > 1
                    else args_ast[0]
                )

                return ast.Subscript(value=origin_ast, slice=slice_val, ctx=ast.Load())
            return None

        # Handle classes
        if hasattr(type_obj, "__module__") and hasattr(type_obj, "__name__"):
            module = type_obj.__module__
            name = type_obj.__name__
            self._add_import(module, name)
            return ast.Name(id=name, ctx=ast.Load())

        return ast.Name(id="Any", ctx=ast.Load())

    def transform(self, target: str) -> ProtocolIR:
        module_name, class_name = target.split(":")
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Could not load {target}: {e}")

        methods = []
        attributes = []

        # Attributes
        try:
            # This handles both static and instance attributes if they are annotated
            type_hints = t.get_type_hints(cls)
            for name, type_hint in type_hints.items():
                if self.private_methods_match(name):
                    continue

                attributes.append(
                    ProtocolAttribute(
                        name=name, annotation=self._type_to_ast(type_hint), value=None
                    )
                )
        except Exception:
            # cls might not support type hints or other error
            pass

        # Methods
        for name, member in inspect.getmembers(cls):
            if self.private_methods_match(name):
                continue

            if inspect.isfunction(member) or inspect.ismethod(member):
                try:
                    sig = inspect.signature(member)
                except ValueError:
                    continue

                # Convert args
                posonlyargs = []
                args_list = []
                kwonlyargs = []
                vararg = None
                kwarg = None
                defaults = []
                kw_defaults = []

                for param in sig.parameters.values():
                    annotation = self._type_to_ast(param.annotation)
                    arg_node = ast.arg(arg=param.name, annotation=annotation)

                    if param.kind == inspect.Parameter.POSITIONAL_ONLY:
                        posonlyargs.append(arg_node)
                        if param.default is not inspect.Parameter.empty:
                            defaults.append(ast.Constant(value=...))
                    elif param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                        args_list.append(arg_node)
                        if param.default is not inspect.Parameter.empty:
                            defaults.append(ast.Constant(value=...))
                    elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                        vararg = arg_node
                    elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                        kwonlyargs.append(arg_node)
                        if param.default is not inspect.Parameter.empty:
                            kw_defaults.append(ast.Constant(value=...))
                        else:
                            kw_defaults.append(None)
                    elif param.kind == inspect.Parameter.VAR_KEYWORD:
                        kwarg = arg_node

                ast_args = ast.arguments(
                    posonlyargs=posonlyargs,
                    args=args_list,
                    vararg=vararg,
                    kwonlyargs=kwonlyargs,
                    kw_defaults=kw_defaults,
                    kwarg=kwarg,
                    defaults=defaults,
                )

                return_annotation = self._type_to_ast(sig.return_annotation)

                is_async = inspect.iscoroutinefunction(member)

                methods.append(
                    ProtocolMethod(
                        name=name,
                        args=ast_args,
                        return_annotation=return_annotation,
                        decorators=[],  # Decorators hard to retrieve from inspect
                        is_async=is_async,
                        type_params=[],  # Not implemented for inspect
                    )
                )

        # Generate imports statements
        imports = []
        for mod, names in self.imports_map.items():
            if not names:
                continue
            imports.append(
                ast.ImportFrom(
                    module=mod,
                    names=[ast.alias(name=n, asname=None) for n in sorted(names)],
                    level=0,
                )
            )

        return ProtocolIR(
            name=class_name,
            methods=methods,
            attributes=attributes,
            imports=imports,
            bases=[],
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
    use_inspect: bool = False,
) -> ast.Module:
    """
    Creates a typing.Protocol definition from a target class specified by string.
    """
    transformer: ProtocolTransformer
    if use_inspect:
        transformer = InspectProtocolTransformer(
            private_methods_match=private_methods_match
        )
    else:
        transformer = ASTProtocolTransformer(
            module_source_code=module_source_code,
            include_star_imports=include_star_imports,
            private_methods_match=private_methods_match,
        )

    ir = transformer.transform(target)

    # Reconstruct ClassDef from IR

    # Prepare body
    class_body: t.List[ast.stmt] = []

    # Attributes
    for attr in ir.attributes:
        annotation = attr.annotation or ast.Name(id="Any", ctx=ast.Load())
        class_body.append(
            ast.AnnAssign(
                target=ast.Name(id=attr.name, ctx=ast.Store()),
                annotation=annotation,
                value=None,
                simple=1,
            )
        )

    # Methods
    for method in ir.methods:
        func_kwargs = {
            "name": method.name,
            "args": method.args,
            "body": [ast.Expr(value=ast.Constant(value=...))],
            "decorator_list": method.decorators,
            "returns": method.return_annotation,
            "lineno": 0,
        }

        # Check if type_params field exists (Python 3.12+)
        if "type_params" in ast.FunctionDef._fields:
            func_kwargs["type_params"] = method.type_params

        func_cls = ast.AsyncFunctionDef if method.is_async else ast.FunctionDef
        class_body.append(func_cls(**func_kwargs))

    if not class_body:
        class_body.append(ast.Pass())

    cls_kwargs = {
        "name": protocol_name or f"{ir.name}Protocol",
        "bases": ir.bases,
        "keywords": [],
        "body": class_body,
        "decorator_list": [],
    }

    if "type_params" in ast.ClassDef._fields:
        cls_kwargs["type_params"] = []

    protocol_cls = ast.ClassDef(**cls_kwargs)

    # Prepare module body
    module_body = list(ir.imports)

    # Resolve typing alias
    # Create a temp module with current imports to check for typing
    temp_mod = ast.Module(body=module_body, type_ignores=[])
    typing_alias, typing_import = resolve_import_alias(temp_mod, "typing", alias="t")

    if typing_import:
        # If it wasn't present, we get an import statement back
        module_body.insert(0, typing_import)

    # Check if extra imports needed
    if extra_imports:
        module_body.extend(extra_imports)

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
