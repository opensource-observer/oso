"""Random manual debugging utilities"""

import asyncio
import logging

from metrics_service.cluster import KubeClusterFactory, make_new_cluster_with_defaults
from metrics_service.types import AppConfig

logger = logging.getLogger(__name__)


def async_test_setup_cluster(config: AppConfig):
    cluster_spec = make_new_cluster_with_defaults(config=config)

    cluster_factory = KubeClusterFactory(
        config.cluster_namespace,
        config.worker_resources,
        cluster_spec=cluster_spec,
        log_override=logger,
    )
    asyncio.run(cluster_factory.create_cluster(2, 2))
