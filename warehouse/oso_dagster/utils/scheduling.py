from dagster import FreshnessPolicy
from .types import params_from
from .. import constants


@params_from(FreshnessPolicy)
def production_freshness_policy(*args, **kwargs) -> FreshnessPolicy | None:
    """Creates a freshness policy that is automatically disabled in a
    non-production mode."""

    if constants.env == "production":
        return FreshnessPolicy(*args, **kwargs)
    return None
