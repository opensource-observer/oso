from typing import Callable, Optional, ParamSpec, Sequence, TypeVar, Union, cast

from dagster import AssetExecutionContext
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig

from . import dlt_factory

P = ParamSpec("P")
R = TypeVar("R")

Q = ParamSpec("Q")
T = TypeVar("T")


def _rest_source(_rest_source: Callable[Q, T], _asset: Callable[P, R]):
    """
    The main factory for creating a REST API source asset. It is a wrapper
    used to get full type information for both the REST API source and the
    asset factory.
    """

    def _factory(*_args: Q.args, **rest_kwargs: Q.kwargs) -> Callable[P, R]:
        """
        Forwards the arguments to the asset factory and returns a new factory,
        maintaining full type information for the caller.
        """

        def _wrapper(*_args: P.args, **asset_kwargs: P.kwargs):
            """
            Creates a new dlt asset using the `dlt_factory` decorator, forwarding
            the arguments to the REST API source.

            The caller should not provide a name for the asset, as it will be
            automatically generated for each resource in the REST API configuration.
            """

            name = asset_kwargs.get("name", None)
            if name is None:
                raise ValueError("Name is required for `rest_factory`")

            key_prefix = cast(
                Optional[Union[str, Sequence[str]]],
                asset_kwargs.get("key_prefix", None),
            )
            if key_prefix is None:
                raise ValueError("Key prefix is required for `rest_factory`")

            if not isinstance(key_prefix, str):
                key_prefix = "_".join(key_prefix)

            config = cast(Optional[RESTAPIConfig], rest_kwargs.pop("config", None))
            if config is None:
                raise ValueError("Config is required for `rest_factory`")

            if "log_intermediate_results" not in asset_kwargs:
                asset_kwargs["log_intermediate_results"] = True

            @dlt_factory(**asset_kwargs)
            def _dlt_asset(context: AssetExecutionContext):
                context.log.info(
                    f"Rest factory materializing asset: {key_prefix}/{name}"
                )

                yield from rest_api_resources(config)

            return _dlt_asset

        return cast(Callable[P, R], _wrapper)

    return _factory


create_rest_factory_asset = _rest_source(rest_api_resources, dlt_factory)
