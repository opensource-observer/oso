from ..definition import Registry
from .entities import register_entities
from .events import register_events
from .metrics import register_metrics


def register_oso_models(registry: Registry, catalog_name: str = "iceberg"):
    """Register OSO models based on the warehouse/oso_sqlmesh/models/marts structure.

    This function registers all the core entities, metrics, and events from the
    OSO data warehouse.
    """
    register_entities(registry, catalog_name)
    register_metrics(registry, catalog_name)
    register_events(registry, catalog_name)
