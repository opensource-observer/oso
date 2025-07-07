from .definition import Registry
from .register import register_oso_models


def setup_registry():
    registry = Registry()

    register_oso_models(registry, "memory")

    return registry
