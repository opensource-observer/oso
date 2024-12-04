import inspect
import json
import logging
import re
import textwrap
import typing as t
from pathlib import Path
import uuid

from sqlglot import exp
from sqlmesh.core import constants as c
from sqlmesh.core.dialect import MacroFunc
from sqlmesh.core.macros import ExecutableOrMacro, MacroRegistry, macro
from sqlmesh.core.model.decorator import model
from sqlmesh.core.model.definition import create_sql_model, create_python_model
from sqlmesh.utils.jinja import JinjaMacroRegistry
from sqlmesh.utils.metaprogramming import (
    Executable,
    ExecutableKind,
    build_env,
    serialize_env,
    normalize_source,
)

logger = logging.getLogger(__name__)

CallableAliasList = t.List[t.Callable | t.Tuple[t.Callable, t.List[str]]]


class GeneratedPythonModel:
    @classmethod
    def create(
        cls,
        *,
        name: str,
        entrypoint_path: str,
        func: t.Callable,
        columns: t.Dict[str, exp.DataType],
        additional_macros: t.Optional[CallableAliasList] = None,
        variables: t.Optional[t.Dict[str, t.Any]] = None,
        imports: t.Optional[t.Dict[str, t.Any]] = None,
        **kwargs,
    ):
        instance = cls(
            name=name,
            entrypoint_path=entrypoint_path,
            func=func,
            additional_macros=additional_macros or [],
            variables=variables or {},
            columns=columns,
            imports=imports or {},
            **kwargs,
        )
        registry = model.registry()
        registry[name] = instance
        return instance

    def __init__(
        self,
        *,
        name: str,
        entrypoint_path: str,
        func: t.Callable,
        additional_macros: CallableAliasList,
        variables: t.Dict[str, t.Any],
        columns: t.Dict[str, exp.DataType],
        imports: t.Dict[str, t.Any],
        **kwargs,
    ):
        self.name = name
        self._func = func
        self._entrypoint_path = entrypoint_path
        self._additional_macros = additional_macros
        self._variables = variables
        self._kwargs = kwargs
        self._columns = columns
        self._imports = imports

    def model(
        self,
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
        fake_module_path = Path(self._entrypoint_path)
        macros = MacroRegistry(f"macros_for_{self.name}")
        macros.update(macros or macro.get_registry())

        if self._additional_macros:
            macros.update(create_macro_registry_from_list(self._additional_macros))

        all_vars = self._variables.copy()
        global_variables = variables or {}
        all_vars["sqlmesh_vars"] = global_variables

        common_kwargs: t.Dict[str, t.Any] = dict(
            defaults=defaults,
            path=path,
            time_column_format=time_column_format,
            physical_schema_mapping=physical_schema_mapping,
            project=project,
            default_catalog=default_catalog,
            variables=all_vars,
            **self._kwargs,
        )

        env = {}
        python_env = create_basic_python_env(
            env,
            self._entrypoint_path,
            module_path,
            macros=macros,
            callables=[self._func],
            imports=self._imports,
        )

        return create_python_model(
            self.name,
            self._func.__name__,
            python_env,
            macros=macros,
            module_path=fake_module_path,
            jinja_macros=jinja_macros,
            columns=self._columns,
            dialect=dialect,
            **common_kwargs,
        )


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
        additional_macros: t.Optional[CallableAliasList] = None,
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
            additional_macros=additional_macros,
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
        additional_macros: t.Optional[CallableAliasList] = None,
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
            macros.update(create_macro_registry_from_list(self.additional_macros))

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


def create_unregistered_macro_registry(
    macros: t.List[t.Callable | t.Tuple[t.Callable, t.List[str]]]
):
    registry = MacroRegistry(f"macro_registry_{uuid.uuid4().hex}")
    for additional_macro in macros:
        if isinstance(additional_macro, tuple):
            registry.update(create_unregistered_wrapped_macro(*additional_macro))
        else:
            registry.update(create_unregistered_wrapped_macro(additional_macro))
    return registry


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
    callables: t.Optional[t.List[t.Callable]] = None,
    imports: t.Optional[t.Dict[str, t.Any]] = None,
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

    imports = imports or {}
    for name, imp in imports.items():
        python_env[name] = imp
        # serialized[func.__name__] = Executable(
        #     payload=f"from {func.__module__} import {func.__name__}",
        #     kind=ExecutableKind.IMPORT,
        # )

    callables = callables or []
    for func in callables:
        # FIXME: this is not ideal right now, we should generalize
        # create_import_call_env to support this.

        serialized[func.__name__] = Executable(
            name=func.__name__,
            payload=normalize_source(func),
            kind=ExecutableKind.DEFINITION,
            path="",
            alias=None,
            is_metadata=False,
        )

    serialized.update(serialize_env(python_env, project_path))
    return serialized


class PrettyExecutable(Executable):
    @classmethod
    def value(cls, v: t.Any) -> Executable:
        pretty_v = json.dumps(v, indent=1)
        return cls(payload=pretty_v, kind=ExecutableKind.VALUE)


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
    is_local = variables.get("gateway", "unknown") == "local" if variables else False

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
    serialized[entrypoint_config_name] = (
        PrettyExecutable.value(config) if is_local else Executable.value(config)
    )

    serialized[name] = Executable(
        payload=f"from {import_module} import {name}",
        kind=ExecutableKind.IMPORT,
    )

    return (entrypoint_name, serialized)


def create_macro_registry_from_list(macro_list: CallableAliasList):
    registry = MacroRegistry("macros")
    for additional_macro in macro_list:
        if isinstance(additional_macro, tuple):
            registry.update(create_unregistered_wrapped_macro(*additional_macro))
        else:
            registry.update(create_unregistered_wrapped_macro(additional_macro))
    return registry
