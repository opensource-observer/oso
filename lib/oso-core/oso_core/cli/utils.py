"""
There's going to be an open PR to `pydantic-settings` that adds this file so we
can remove this file once that PR if that is merged and released.

We have added a `CliContext` that we can use to pass a context around to a
hierachy of CLI commands.
"""

import asyncio
import functools
import inspect
import threading
import typing as t
from argparse import Namespace
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel, Field
from pydantic._internal._signature import _field_name_for_signature
from pydantic._internal._utils import is_model_class
from pydantic.dataclasses import is_pydantic_dataclass
from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    SettingsConfigDict,
    SettingsError,
    get_subcommand,
)
from pydantic_settings.sources.types import PydanticModel

T = t.TypeVar("T")


class CliContext(BaseModel):
    """
    A context object that can be used to pass data between CLI commands and subcommands.
    """

    settings: Any | None = None
    parent: t.Optional["CliContext"] = None
    data: dict[str, Any] = Field(default_factory=dict)

    def get_subcontext(self, settings: Any) -> "CliContext":
        """
        Creates a new subcontext with this context as the parent.

        Returns:
            The new subcontext.
        """
        # The data is shared between parent and subcontext
        return CliContext(parent=self, data=self.data, settings=settings)

    def get_data_as(self, key: str, typ: type[T]) -> T:
        """
        Gets the data from the context as the given type.

        Args:
            key: The key of the data to get.
            typ: The type to cast the data to.
        Returns:
            The data cast to the given type.
        """
        data = self.data.get(key)
        if not data:
            raise KeyError(f"Key '{key}' not found in context data")
        if isinstance(data, typ):
            assert isinstance(data, typ)
            return data
        if issubclass(data, typ):
            assert issubclass(data, typ)
            return data
        raise TypeError(f"Data for key '{key}' is not of type '{typ.__name__}'")


class CliApp:
    """
    A utility class for running Pydantic `BaseSettings`, `BaseModel`, or `pydantic.dataclasses.dataclass` as
    CLI applications.
    """

    @staticmethod
    def _get_base_settings_cls(model_cls: type[Any]) -> type[BaseSettings]:
        if issubclass(model_cls, BaseSettings):
            return model_cls

        class CliAppBaseSettings(BaseSettings, model_cls):  # type: ignore
            __doc__ = model_cls.__doc__
            model_config = SettingsConfigDict(
                nested_model_default_partial_update=True,
                case_sensitive=True,
                cli_hide_none_type=True,
                cli_avoid_json=True,
                cli_enforce_required=True,
                cli_implicit_flags=True,
                cli_kebab_case=True,
            )

        return CliAppBaseSettings

    @staticmethod
    def _run_cli_cmd(
        context: CliContext, model: Any, cli_cmd_method_name: str, is_required: bool
    ) -> Any:
        command = getattr(type(model), cli_cmd_method_name, None)
        if command is None:
            if is_required:
                raise SettingsError(
                    f"Error: {type(model).__name__} class is missing {cli_cmd_method_name} entrypoint"
                )
            return model

        # Inspect if the context is needed as parameter
        sig = inspect.signature(command)

        context_param = sig.parameters.get("context")
        if context_param:
            if issubclass(context_param.annotation, CliContext):
                command = functools.partial(command, model, context=context)
            else:
                command = functools.partial(command, model)
        else:
            command = functools.partial(command, model)

        # If the method is asynchronous, we handle its execution based on the current event loop status.
        if inspect.iscoroutinefunction(command):
            # For asynchronous methods, we have two execution scenarios:
            # 1. If no event loop is running in the current thread, run the coroutine directly with asyncio.run().
            # 2. If an event loop is already running in the current thread, run the coroutine in a separate thread to avoid conflicts.
            try:
                # Check if an event loop is currently running in this thread.
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # We're in a context with an active event loop (e.g., Jupyter Notebook).
                # Running asyncio.run() here would cause conflicts, so we use a separate thread.
                exception_container = []

                def run_coro() -> None:
                    try:
                        # Execute the coroutine in a new event loop in this separate thread.
                        asyncio.run(command())
                    except Exception as e:
                        exception_container.append(e)

                thread = threading.Thread(target=run_coro)
                thread.start()
                thread.join()
                if exception_container:
                    # Propagate exceptions from the separate thread.
                    raise exception_container[0]
            else:
                # No event loop is running; safe to run the coroutine directly.
                asyncio.run(command())
        else:
            # For synchronous methods, call them directly.
            command()

        return model

    @staticmethod
    def run(
        model_cls: type[T],
        cli_args: list[str]
        | Namespace
        | SimpleNamespace
        | dict[str, Any]
        | None = None,
        cli_settings_source: CliSettingsSource[Any] | None = None,
        cli_exit_on_error: bool | None = None,
        cli_cmd_method_name: str = "cli_cmd",
        **model_init_data: Any,
    ) -> T:
        """
        Runs a Pydantic `BaseSettings`, `BaseModel`, or `pydantic.dataclasses.dataclass` as a CLI application.
        Running a model as a CLI application requires the `cli_cmd` method to be defined in the model class.

        Args:
            model_cls: The model class to run as a CLI application.
            cli_args: The list of CLI arguments to parse. If `cli_settings_source` is specified, this may
                also be a namespace or dictionary of pre-parsed CLI arguments. Defaults to `sys.argv[1:]`.
            cli_settings_source: Override the default CLI settings source with a user defined instance.
                Defaults to `None`.
            cli_exit_on_error: Determines whether this function exits on error. If model is subclass of
                `BaseSettings`, defaults to BaseSettings `cli_exit_on_error` value. Otherwise, defaults to
                `True`.
            cli_cmd_method_name: The CLI command method name to run. Defaults to "cli_cmd".
            model_init_data: The model init data.

        Returns:
            The ran instance of model.

        Raises:
            SettingsError: If model_cls is not subclass of `BaseModel` or `pydantic.dataclasses.dataclass`.
            SettingsError: If model_cls does not have a `cli_cmd` entrypoint defined.
        """

        if not (is_pydantic_dataclass(model_cls) or is_model_class(model_cls)):
            raise SettingsError(
                f"Error: {model_cls.__name__} is not subclass of BaseModel or pydantic.dataclasses.dataclass"
            )

        cli_settings = None
        cli_parse_args = True if cli_args is None else cli_args
        if cli_settings_source is not None:
            if isinstance(cli_parse_args, (Namespace, SimpleNamespace, dict)):
                cli_settings = cli_settings_source(parsed_args=cli_parse_args)
            else:
                cli_settings = cli_settings_source(args=cli_parse_args)
        elif isinstance(cli_parse_args, (Namespace, SimpleNamespace, dict)):
            raise SettingsError(
                "Error: `cli_args` must be list[str] or None when `cli_settings_source` is not used"
            )

        model_init_data["_cli_parse_args"] = cli_parse_args
        model_init_data["_cli_exit_on_error"] = cli_exit_on_error
        model_init_data["_cli_settings_source"] = cli_settings
        if not issubclass(model_cls, BaseSettings):
            base_settings_cls = CliApp._get_base_settings_cls(model_cls)
            model = base_settings_cls(**model_init_data)
            model_init_data = {}
            for field_name, field_info in base_settings_cls.model_fields.items():
                model_init_data[_field_name_for_signature(field_name, field_info)] = (
                    getattr(model, field_name)
                )

        context = CliContext(settings=model_cls(**model_init_data))

        return CliApp._run_cli_cmd(
            context,
            model_cls(**model_init_data),
            cli_cmd_method_name,
            is_required=False,
        )

    @staticmethod
    def run_subcommand(
        context: CliContext,
        model: PydanticModel,
        cli_exit_on_error: bool | None = None,
        cli_cmd_method_name: str = "cli_cmd",
    ) -> PydanticModel:
        """
        Runs the model subcommand. Running a model subcommand requires the `cli_cmd` method to be defined in
        the nested model subcommand class.

        Args:
            model: The model to run the subcommand from.
            cli_exit_on_error: Determines whether this function exits with error if no subcommand is found.
                Defaults to model_config `cli_exit_on_error` value if set. Otherwise, defaults to `True`.
            cli_cmd_method_name: The CLI command method name to run. Defaults to "cli_cmd".

        Returns:
            The ran subcommand model.

        Raises:
            SystemExit: When no subcommand is found and cli_exit_on_error=`True` (the default).
            SettingsError: When no subcommand is found and cli_exit_on_error=`False`.
        """

        subcommand = get_subcommand(
            model, is_required=True, cli_exit_on_error=cli_exit_on_error
        )
        subcontext = context.get_subcontext(model)
        return CliApp._run_cli_cmd(
            subcontext, subcommand, cli_cmd_method_name, is_required=True
        )

    @staticmethod
    def serialize(model: PydanticModel) -> list[str]:
        """
        Serializes the CLI arguments for a Pydantic data model.

        Args:
            model: The data model to serialize.

        Returns:
            The serialized CLI arguments for the data model.
        """

        base_settings_cls = CliApp._get_base_settings_cls(type(model))
        return CliSettingsSource[Any](base_settings_cls)._serialized_args(model)
