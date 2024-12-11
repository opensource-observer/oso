"""Random manual debugging utilities"""

import asyncio
import logging

from metrics_tools.compute.cluster import (
    KubeClusterFactory,
    make_new_cluster_with_defaults,
    start_duckdb_cluster,
)

from . import constants

logger = logging.getLogger(__name__)


def test_setup_cluster():
    cluster_spec = make_new_cluster_with_defaults()
    return start_duckdb_cluster(constants.cluster_namespace, cluster_spec)


def async_test_setup_cluster():
    cluster_spec = make_new_cluster_with_defaults()

    cluster_factory = KubeClusterFactory(
        constants.cluster_namespace,
        cluster_spec=cluster_spec,
        log_override=logger,
    )
    asyncio.run(cluster_factory.create_cluster(2, 2))
