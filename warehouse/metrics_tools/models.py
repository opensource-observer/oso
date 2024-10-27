import inspect
import logging
import re
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
    normalize_source,
)

logger = logging.getLogger(__name__)


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
        physical_schema_mapping: t.Optional[t.Dict[re.Pattern, str]] = None,
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
                    macros.update(create_unregistered_wrapped_macro(*additional_macro))
                else:
                    macros.update(create_unregistered_wrapped_macro(additional_macro))

        common_kwargs: t.Dict[str, t.Any] = dict(
            defaults=defaults,
            path=fake_module_path,
            time_column_format=time_column_format,
            physical_schema_mapping=physical_schema_mapping,
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
    func: t.Callable,
    aliases: t.Optional[t.List[str]] = None,
):
    aliases = aliases or []
    name = func.__name__
    source = normalize_source(func)
    registry: t.Dict[str, ExecutableOrMacro] = {
        name: Executable(
            name=name,
            payload=source,
            kind=ExecutableKind.DEFINITION,
            path=f"/__generated/macro/{name}.py",
            alias=None,
            is_metadata=False,
        ),
    }

    for alias_name in aliases:
        alias_as_str = textwrap.dedent(
            f"""
        def {alias_name}(evaluator, *args, **kwargs):
            return {name}(evaluator, *args, **kwargs)
        """
        )
        registry[alias_name] = Executable(
            name=alias_name,
            payload=alias_as_str,
            kind=ExecutableKind.DEFINITION,
            path=f"/__generated/macro/{name}.py",
            alias=None,
            is_metadata=False,
        )

    return registry


def create_unregistered_wrapped_macro(
    func: t.Callable,
    aliases: t.Optional[t.List[str]] = None,
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


def create_basic_python_env(
    env: t.Dict[str, t.Any],
    path: str | Path = "",
    project_path: str | Path = "",
    macros: t.Optional[MacroRegistry] = None,
    additional_macros: t.Optional[MacroRegistry] = None,
    variables: t.Optional[t.Dict[str, t.Any]] = None,
):
    if isinstance(path, str):
        path = Path(path)
    if isinstance(project_path, str):
        project_path = Path(project_path)

    serialized = env.copy()
    macros = macros or macro.get_registry()

    if additional_macros:
        macros = t.cast(MacroRegistry, macros.copy())
        macros.update(additional_macros)

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

    return serialized


def create_import_call_env(
    name: str,
    import_module: str,
    config: t.Mapping[str, t.Any],
    source: str,
    env: t.Dict[str, t.Any],
    path: str | Path,
    project_path: str | Path,
    macros: t.Optional[MacroRegistry] = None,
    entrypoint_name: str = "macro_entrypoint",
    additional_macros: t.Optional[MacroRegistry] = None,
    variables: t.Optional[t.Dict[str, t.Any]] = None,
):
    if isinstance(path, str):
        path = Path(path)

    if isinstance(project_path, str):
        project_path = Path(project_path)

    serialized = create_basic_python_env(
        env,
        path,
        project_path,
        macros=macros,
        variables=variables,
        additional_macros=additional_macros,
    )

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

    return (entrypoint_name, serialized)
