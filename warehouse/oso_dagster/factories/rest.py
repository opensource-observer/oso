from typing import Callable, Optional, ParamSpec, Sequence, TypeVar, Union, cast

import dlt
from dagster import AssetExecutionContext
from dlt.extract.resource import DltResource
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import EndpointResource, RESTAPIConfig

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
            if name is not None:
                raise ValueError(
                    "Names will be automatically generated for `rest_factory`"
                )

            key_prefix = cast(
                Optional[Union[str, Sequence[str]]],
                asset_kwargs.get("key_prefix", None),
            )
            if key_prefix is None:
                raise ValueError("Key prefix is required for `rest_factory`")

            if not isinstance(key_prefix, str):
                key_prefix = "/".join(key_prefix)

            config = cast(Optional[RESTAPIConfig], rest_kwargs.pop("config", None))
            if config is None:
                raise ValueError("Config is required for `rest_factory`")

            config_resources = config.pop("resources", None)  # type: ignore
            if config_resources is None:
                raise ValueError("Resources is required for `rest_factory`")

            def create_asset_for_resource(resource_ref, config_ref):
                """
                The internal function that creates a new asset for a given resource to use
                the correct reference. If not, the asset will be created with the wrong
                reference, the last resource in the configuration:

                https://pylint.readthedocs.io/en/latest/user_guide/messages/warning/cell-var-from-loop.html
                """

                resource_ref = cast(
                    Union[str, EndpointResource, DltResource], resource_ref
                )

                resource_name = None

                if isinstance(resource_ref, str):
                    resource_name = resource_ref
                elif isinstance(resource_ref, dict):
                    resource_name = resource_ref.get("name", None)
                elif isinstance(resource_ref, DltResource):
                    resource_name = resource_ref.name

                if not isinstance(resource_name, str):
                    raise ValueError("Failed to extract resource name from reference")

                @dlt_factory(name=resource_name, **asset_kwargs)
                def _dlt_ref_asset(context: AssetExecutionContext):
                    """
                    The dlt asset function that creates the REST API source asset.
                    """

                    context.log.info(
                        f"Rest factory materializing asset: {key_prefix}/{resource_name}"
                    )

                    rest_api_config = cast(RESTAPIConfig, config_ref)

                    rest_api_config["resources"] = [resource_ref]

                    for resource in rest_api_resources(rest_api_config, **rest_kwargs):
                        yield dlt.resource(
                            resource,
                            name=resource_name,
                            max_table_nesting=0,
                            write_disposition="merge",
                        )

                return _dlt_ref_asset

            return [
                create_asset_for_resource(resource_ref, {**config})
                for resource_ref in config_resources
            ]

        return cast(Callable[P, R], _wrapper)

    return _factory


create_rest_factory_asset = _rest_source(rest_api_resources, dlt_factory)
