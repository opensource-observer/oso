from dotenv import load_dotenv
from metrics_tools.utils import env

load_dotenv()

cluster_namespace = env.required_str("METRICS_CLUSTER_NAMESPACE")
cluster_name = env.required_str("METRICS_CLUSTER_NAME")
cluster_image_repo = env.required_str(
    "METRICS_CLUSTER_IMAGE_REPO", "ghcr.io/opensource-observer/oso"
)
cluster_image_tag = env.required_str("METRICS_CLUSTER_IMAGE_TAG")
scheduler_memory_limit = env.required_str("METRICS_SCHEDULER_MEMORY_LIMIT", "90000Mi")
scheduler_memory_request = env.required_str(
    "METRICS_SCHEDULER_MEMORY_REQUEST", "85000Mi"
)
scheduler_pool_type = env.required_str("METRICS_WORKER_POOL_TYPE", "sqlmesh-scheduler")
worker_threads = env.required_int("METRICS_WORKER_THREADS", 16)
worker_memory_limit = env.required_str("METRICS_WORKER_MEMORY_LIMIT", "90000Mi")
worker_memory_request = env.required_str("METRICS_WORKER_MEMORY_REQUEST", "85000Mi")
worker_pool_type = env.required_str("METRICS_WORKER_POOL_TYPE", "sqlmesh-worker")

gcs_bucket = env.required_str("METRICS_GCS_BUCKET")
gcs_key_id = env.required_str("METRICS_GCS_KEY_ID")
gcs_secret = env.required_str("METRICS_GCS_SECRET")

results_path_prefix = env.required_str("METRICS_GCS_RESULTS_PATH_PREFIX", "mcs-results")

worker_duckdb_path = env.required_str("METRICS_WORKER_DUCKDB_PATH")

trino_host = env.required_str("METRICS_TRINO_HOST")
trino_port = env.required_str("METRICS_TRINO_PORT")
trino_user = env.required_str("METRICS_TRINO_USER")
trino_catalog = env.required_str("METRICS_TRINO_CATALOG")

hive_catalog = env.required_str("METRICS_HIVE_CATALOG", "source")
hive_schema = env.required_str("METRICS_HIVE_SCHEMA", "export")

debug_all = env.ensure_bool("METRICS_DEBUG_ALL", False)
debug_with_duckdb = env.ensure_bool("METRICS_DEBUG_WITH_DUCKDB", False)
if not debug_all:
    debug_cache = env.ensure_bool("METRICS_DEBUG_CACHE", False)
    debug_cluster = env.ensure_bool("METRICS_DEBUG_CLUSTER", False)
    debug_cluster_no_shutdown = env.ensure_bool(
        "METRICS_DEBUG_CLUSTER_NO_SHUTDOWN", False
    )
else:
    debug_cache = debug_all
    debug_cluster = debug_all
    debug_cluster_no_shutdown = debug_all
