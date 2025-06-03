import inspect
import json
import logging
import textwrap
import typing as t
import uuid
from pathlib import Path

from sqlmesh.core import constants as c
from sqlmesh.core.macros import ExecutableOrMacro, MacroRegistry, macro
from sqlmesh.core.model.decorator import model
from sqlmesh.utils.metaprogramming import (
    Executable,
    ExecutableKind,
    build_env,
    normalize_source,
    serialize_env,
)

logger = logging.getLogger(__name__)

CallableAliasList = t.List[t.Callable[..., t.Any] | t.Tuple[t.Callable[..., t.Any], t.List[str]]]


class MacroOverridingModel(model):
    def __init__(
        self,
        override_module_path: Path,
        override_path: Path,
        locals: t.Dict[str, t.Any],
        additional_macros: CallableAliasList,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._additional_macros = additional_macros
        self._locals = locals
        self._override_module_path = override_module_path
        self._override_path = override_path

    def model(self, *args, **kwargs):
        if len(self._additional_macros) > 0:
            macros = MacroRegistry(f"macros_for_{self.name}")
            system_macros = kwargs.get("macros", macros)
            macros.update(system_macros) 
            macros.update(macro.get_registry())

            additional_macros = create_macro_registry_from_list(self._additional_macros)
            macros.update(additional_macros)
            if not macros.get('datetrunc'):
                raise ValueError("FUCL")
            kwargs["macros"] = macros

        vars = kwargs.get("variables", {})
        if len(self._locals) > 0:
            vars.update(self._locals)

        kwargs["variables"] = vars
        kwargs["module_path"] = self._override_module_path
        kwargs["path"] = self._override_path

        return super().model(*args, **kwargs)


def escape_triple_quotes(input_string: str) -> str:
    escaped_string = input_string.replace("'''", "\\'\\'\\'")
    escaped_string = escaped_string.replace('"""', '\\"\\"\\"')
    return escaped_string


def create_unregistered_macro_registry(
    macros: t.List[t.Callable[..., t.Any] | t.Tuple[t.Callable[..., t.Any], t.List[str]]]
):
    registry = MacroRegistry(f"macro_registry_{uuid.uuid4().hex}")
    for additional_macro in macros:
        if isinstance(additional_macro, tuple):
            registry.update(create_unregistered_wrapped_macro(*additional_macro)) # type: ignore
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
    func: t.Callable[..., t.Any],
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
    def value(cls, v: t.Any, is_metadata: t.Optional[bool] = None) -> Executable:
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
            registry.update(create_unregistered_wrapped_macro(*additional_macro)) # type: ignore
        else:
            registry.update(create_unregistered_wrapped_macro(additional_macro))
    return registry
