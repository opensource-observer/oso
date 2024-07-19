from dagster import FreshnessPolicy
from .types import params_from


@params_from(FreshnessPolicy)
def production_freshness_policy(*args, **kwargs) -> FreshnessPolicy | None:
    """Creates a freshness policy that is automatically disabled in a
    non-production mode."""

    # Lazily import this because importing constants in the utils forces the
    # need to certain environment variables.
    from .. import constants

    if constants.env == "production":
        return FreshnessPolicy(*args, **kwargs)
    return None
