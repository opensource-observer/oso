import inspect
import logging
import textwrap
import typing as t
from pathlib import Path

from sqlglot import exp
from sqlmesh.core import constants as c
from sqlmesh.core.dialect import MacroFunc
from sqlmesh.core.macros import ExecutableOrMacro, MacroRegistry, macro
from sqlmesh.core.model.decorator import model
from sqlmesh.core.model.definition import create_sql_model
from sqlmesh.utils.jinja import JinjaMacroRegistry
from sqlmesh.utils.metaprogramming import (
    Executable,
    ExecutableKind,
    build_env,
    serialize_env,
)

logger = logging.getLogger(__name__)


# class model(registry_decorator):
#     """Specifies a function is a python based model."""

#     registry_name = "python_models"
#     _dialect: DialectType = None

#     def __init__(self, name: t.Optional[str] = None, is_sql: bool = False, **kwargs: t.Any) -> None:
#         if not is_sql and "columns" not in kwargs:
#             raise ConfigError("Python model must define column schema.")

#         self.name = name or ""
#         self.is_sql = is_sql
#         self.kwargs = kwargs

#         # Make sure that argument values are expressions in order to pass validation in ModelMeta.
#         calls = self.kwargs.pop("audits", [])
#         self.kwargs["audits"] = [
#             (
#                 (call, {})
#                 if isinstance(call, str)
#                 else (
#                     call[0],
#                     {
#                         arg_key: exp.convert(
#                             tuple(arg_value) if isinstance(arg_value, list) else arg_value
#                         )
#                         for arg_key, arg_value in call[1].items()
#                     },
#                 )
#             )
#             for call in calls
#         ]

#         if "default_catalog" in kwargs:
#             raise ConfigError("`default_catalog` cannot be set on a per-model basis.")

#         self.columns = {
#             column_name: (
#                 column_type
#                 if isinstance(column_type, exp.DataType)
#                 else exp.DataType.build(str(column_type))
#             )
#             for column_name, column_type in self.kwargs.pop("columns", {}).items()
#         }

#     def model(
#         self,
#         *,
#         module_path: Path,
#         path: Path,
#         defaults: t.Optional[t.Dict[str, t.Any]] = None,
#         macros: t.Optional[MacroRegistry] = None,
#         jinja_macros: t.Optional[JinjaMacroRegistry] = None,
#         dialect: t.Optional[str] = None,
#         time_column_format: str = c.DEFAULT_TIME_COLUMN_FORMAT,
#         physical_schema_override: t.Optional[t.Dict[str, str]] = None,
#         project: str = "",
#         default_catalog: t.Optional[str] = None,
#         variables: t.Optional[t.Dict[str, t.Any]] = None,
#         infer_names: t.Optional[bool] = False,
#     ) -> Model:
#         """Get the model registered by this function."""
#         env: t.Dict[str, t.Any] = {}
#         entrypoint = self.func.__name__

#         if not self.name and infer_names:
#             self.name = get_model_name(Path(inspect.getfile(self.func)))

#         if not self.name:
#             raise ConfigError("Python model must have a name.")

#         kind = self.kwargs.get("kind", None)
#         if kind is not None:
#             if isinstance(kind, _ModelKind):
#                 logger.warning(
#                     f"""Python model "{self.name}"'s `kind` argument was passed a SQLMesh `{type(kind).__name__}` object. This may result in unexpected behavior - provide a dictionary instead."""
#                 )
#             elif isinstance(kind, dict):
#                 if "name" not in kind or not isinstance(kind.get("name"), ModelKindName):
#                     raise ConfigError(
#                         f"""Python model "{self.name}"'s `kind` dictionary must contain a `name` key with a valid ModelKindName enum value."""
#                     )

#         build_env(self.func, env=env, name=entrypoint, path=module_path)

#         common_kwargs = dict(
#             defaults=defaults,
#             path=path,
#             time_column_format=time_column_format,
#             python_env=serialize_env(env, path=module_path),
#             physical_schema_override=physical_schema_override,
#             project=project,
#             default_catalog=default_catalog,
#             variables=variables,
#             **self.kwargs,
#         )

#         dialect = common_kwargs.pop("dialect", dialect)
#         for key in ("pre_statements", "post_statements"):
#             statements = common_kwargs.get(key)
#             if statements:
#                 common_kwargs[key] = [
#                     parse_one(s, dialect=dialect) if isinstance(s, str) else s for s in statements
#                 ]

#         if self.is_sql:
#             query = MacroFunc(this=exp.Anonymous(this=entrypoint))
#             if self.columns:
#                 common_kwargs["columns"] = self.columns
#             return create_sql_model(
#                 self.name, query, module_path=module_path, dialect=dialect, **common_kwargs
#             )

#         return create_python_model(
#             self.name,
#             entrypoint,
#             module_path=module_path,
#             macros=macros,
#             jinja_macros=jinja_macros,
#             columns=self.columns,
#             dialect=dialect,
#             **common_kwargs,
#         )


# class metrics_model(model):
#     """This is a hack upon hacks. We abuse the sqlmesh serialization system
#     to create a new type of model. That we can forcibly inject into sqlmesh
#     state"""

#     def __init__(self, name: t.Optional[str], inject_env: t.Dict[str, t.Any]):
#         super().__init__(name=name, is_sql=True)
#         self._inject_env = inject_env

#     def model(
#         self,
#         *,
#         module_path: Path,
#         path: Path,
#         defaults: t.Optional[t.Dict[str, t.Any]] = None,
#         macros: t.Optional[MacroRegistry] = None,
#         jinja_macros: t.Optional[JinjaMacroRegistry] = None,
#         dialect: t.Optional[str] = None,
#         time_column_format: str = c.DEFAULT_TIME_COLUMN_FORMAT,
#         physical_schema_override: t.Optional[t.Dict[str, str]] = None,
#         project: str = "",
#         default_catalog: t.Optional[str] = None,
#         variables: t.Optional[t.Dict[str, t.Any]] = None,
#         infer_names: t.Optional[bool] = False,
#     ) -> Model:
#         """Get the model registered by this function."""
#         env: t.Dict[str, t.Any] = {}
#         entrypoint = self.func.__name__

#         if not self.name and infer_names:
#             self.name = get_model_name(Path(inspect.getfile(self.func)))

#         if not self.name:
#             raise ConfigError("Python model must have a name.")

#         kind = self.kwargs.get("kind", None)
#         if kind is not None:
#             if isinstance(kind, _ModelKind):
#                 logger.warning(
#                     f"""Python model "{self.name}"'s `kind` argument was passed a SQLMesh `{type(kind).__name__}` object. This may result in unexpected behavior - provide a dictionary instead."""
#                 )
#             elif isinstance(kind, dict):
#                 if "name" not in kind or not isinstance(
#                     kind.get("name"), ModelKindName
#                 ):
#                     raise ConfigError(
#                         f"""Python model "{self.name}"'s `kind` dictionary must contain a `name` key with a valid ModelKindName enum value."""
#                     )

#         self.build_env(env=env, name=entrypoint, path=module_path)

#         common_kwargs: t.Dict[str, t.Any] = dict(
#             defaults=defaults,
#             path=path,
#             time_column_format=time_column_format,
#             python_env=serialize_env(env, path=module_path),
#             physical_schema_override=physical_schema_override,
#             project=project,
#             default_catalog=default_catalog,
#             variables=variables,
#             **self.kwargs,
#         )

#         dialect = common_kwargs.pop("dialect", dialect)
#         for key in ("pre_statements", "post_statements"):
#             statements = common_kwargs.get(key)
#             if statements:
#                 common_kwargs[key] = [
#                     parse_one(s, dialect=dialect) if isinstance(s, str) else s
#                     for s in statements
#                 ]

#         if self.is_sql:
#             query = MacroFunc(this=exp.Anonymous(this=entrypoint))
#             if self.columns:
#                 common_kwargs["columns"] = self.columns
#             return create_sql_model(
#                 self.name,
#                 query,
#                 module_path=module_path,
#                 dialect=dialect,
#                 **common_kwargs,
#             )

#         return create_python_model(
#             self.name,
#             entrypoint,
#             module_path=module_path,
#             macros=macros,
#             jinja_macros=jinja_macros,
#             columns=self.columns,
#             dialect=dialect,
#             **common_kwargs,
#         )

# python_env = _python_env(
#     [*pre_statements, query, *post_statements, *audit_expressions],
#     jinja_macro_references,
#     module_path,
#     macros or macro.get_registry(),
#     variables=variables,
#     used_variables=used_variables,
#     path=path,
# )


class GeneratedModel:
    @classmethod
    def create(
        cls,
        *,
        func: t.Callable[..., t.Any],
        config: t.Mapping[str, t.Any],
        name: str,
        columns: t.Dict[str, exp.DataType],
        entrypoint_path: str,
        source: t.Optional[str] = None,
        source_loader: t.Optional[t.Callable[[], str]] = None,
        **kwargs,
    ):
        if not source and not source_loader:
            try:
                source = inspect.getsource(func)
            except:  # noqa: E722
                pass

        assert (
            source is not None or source_loader is not None
        ), "Must have a way to load the source for state diffs"

        instance = cls(
            func_name=func.__name__,
            import_module=func.__module__,
            config=config,
            name=name,
            columns=columns,
            entrypoint_path=entrypoint_path,
            source=source,
            source_loader=source_loader,
            **kwargs,
        )
        registry = model.registry()
        registry[name] = instance
        return instance

    def __init__(
        self,
        *,
        func_name: str,
        import_module: str,
        config: t.Mapping[str, t.Any],
        name: str,
        columns: t.Dict[str, exp.DataType],
        entrypoint_path: str,
        source: t.Optional[str] = None,
        source_loader: t.Optional[t.Callable[[], str]] = None,
        additional_macros: t.Optional[
            t.List[t.Callable | t.Tuple[t.Callable, t.List[str]]]
        ] = None,
        **kwargs,
    ):
        self.kwargs = kwargs
        self.func_name = func_name
        self.import_module = import_module
        self.config = config
        self.name = name
        self.columns = columns
        self.entrypoint_path = entrypoint_path
        self.source_loader = source_loader
        self.source = source
        self.additional_macros = additional_macros or []

    def model(
        self,
        *,
        module_path: Path,
        path: Path,
        defaults: t.Optional[t.Dict[str, t.Any]] = None,
        macros: t.Optional[MacroRegistry] = None,
        jinja_macros: t.Optional[JinjaMacroRegistry] = None,
        dialect: t.Optional[str] = None,
        time_column_format: str = c.DEFAULT_TIME_COLUMN_FORMAT,
        physical_schema_override: t.Optional[t.Dict[str, str]] = None,
        project: str = "",
        default_catalog: t.Optional[str] = None,
        variables: t.Optional[t.Dict[str, t.Any]] = None,
        infer_names: t.Optional[bool] = False,
    ):
        macros = macros or macro.get_registry()
        fake_module_path = Path(self.entrypoint_path)

        if self.additional_macros:
            macros = t.cast(MacroRegistry, macros.copy())
            for additional_macro in self.additional_macros:
                if isinstance(additional_macro, tuple):
                    macros.update(create_unregistered_macro(*additional_macro))
                else:
                    macros.update(create_unregistered_macro(additional_macro))

        common_kwargs: t.Dict[str, t.Any] = dict(
            defaults=defaults,
            path=fake_module_path,
            time_column_format=time_column_format,
            physical_schema_override=physical_schema_override,
            project=project,
            default_catalog=default_catalog,
            variables=variables,
            **self.kwargs,
        )

        source = self.source
        if not source:
            if self.source_loader:
                source = self.source_loader()
        assert source is not None, "source cannot be empty"

        # env = macros.copy()
        env = {}

        entrypoint_name, env = create_import_call_env(
            self.func_name,
            self.import_module,
            self.config,
            source,
            env,
            fake_module_path,
            project_path=module_path,
            macros=macros,
            variables=variables,
        )
        common_kwargs["python_env"] = env

        query = MacroFunc(this=exp.Anonymous(this=entrypoint_name))
        if self.columns:
            common_kwargs["columns"] = self.columns

        return create_sql_model(
            self.name,
            query,
            module_path=fake_module_path,
            jinja_macros=jinja_macros,
            **common_kwargs,
        )


def escape_triple_quotes(input_string: str) -> str:
    escaped_string = input_string.replace("'''", "\\'\\'\\'")
    escaped_string = escaped_string.replace('"""', '\\"\\"\\"')
    return escaped_string


def create_unregistered_macro(
    func: t.Callable, aliases: t.Optional[t.List[str]] = None
) -> t.Dict[str, ExecutableOrMacro]:
    aliases = aliases or []
    entrypoint_name = func.__name__
    import_module = func.__module__
    delegated_name = f"_wrapped_{entrypoint_name}"

    source = inspect.getsource(func)

    all_aliases = [entrypoint_name] + aliases

    registry: t.Dict[str, ExecutableOrMacro] = {
        delegated_name: Executable(
            payload=f"from {import_module} import {func.__name__} as {delegated_name}",
            kind=ExecutableKind.IMPORT,
        ),
    }

    for alias_name in all_aliases:
        alias_as_str = textwrap.dedent(
            f"""
        def {alias_name}(evaluator, *args, **kwargs):
            '''
            Source: 
            
            {textwrap.indent("\n" + escape_triple_quotes(source), "        ")}
            '''
            return {delegated_name}(evaluator, *args, **kwargs)
        """
        )
        registry[alias_name] = Executable(
            name=alias_name,
            payload=alias_as_str,
            kind=ExecutableKind.DEFINITION,
            path=f"/__generated/macro/{entrypoint_name}.py",
            alias=None,
            is_metadata=False,
        )
    return registry


def create_import_call_env(
    name: str,
    import_module: str,
    config: t.Mapping[str, t.Any],
    source: str,
    env: t.Dict[str, t.Any],
    path: Path,
    project_path: Path,
    macros: t.Optional[MacroRegistry] = None,
    entrypoint_name: str = "macro_entrypoint",
    additional_macros: t.Optional[MacroRegistry] = None,
    variables: t.Optional[t.Dict[str, t.Any]] = None,
):

    serialized = env.copy()
    macros = macros or macro.get_registry()

    if additional_macros:
        macros = t.cast(MacroRegistry, macros.copy())
        macros.update(additional_macros)

    entrypoint_as_str = textwrap.dedent(
        f"""
    def {entrypoint_name}(evaluator):
        '''
        Source: 
        
        {textwrap.indent("\n" + escape_triple_quotes(source), "        ")}
        '''
        return {name}(evaluator, **entrypoint_config)
    """
    )
    entrypoint_config_name = "entrypoint_config"
    serialized[entrypoint_name] = Executable(
        name=entrypoint_name,
        payload=entrypoint_as_str,
        kind=ExecutableKind.DEFINITION,
        path=path.as_posix(),
        alias=entrypoint_name,
        is_metadata=False,
    )
    serialized[entrypoint_config_name] = Executable.value(config)

    serialized[name] = Executable(
        payload=f"from {import_module} import {name}",
        kind=ExecutableKind.IMPORT,
    )

    python_env = {}
    for name, used_macro in macros.items():
        if isinstance(used_macro, Executable):
            serialized[name] = used_macro
        elif not hasattr(used_macro, c.SQLMESH_BUILTIN):
            build_env(used_macro.func, env=python_env, name=name, path=path)

    if variables:
        for name, value in variables.items():
            serialized[name] = Executable.value(value)

    serialized.update(serialize_env(python_env, project_path))

    return (entrypoint_name, serialized)
