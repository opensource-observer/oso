import logging
import os

connected_to_sqlmesh_logs = False

logger = logging.getLogger(__name__)


def add_metrics_tools_to_sqlmesh_logging():
    """sqlmesh won't automatically add metrics_tools logging. This will enable
    logs from any of the metrics tools utilities. If sqlmesh is the runner"""
    import __main__

    global connected_to_sqlmesh_logs

    try:
        app_name = os.path.basename(__main__.__file__)
    except AttributeError:
        # Do nothing if __main__.__file__ doesn't exist
        return
    if app_name == "sqlmesh" and not connected_to_sqlmesh_logs:
        add_metrics_tools_to_existing_logger(app_name)
        connected_to_sqlmesh_logs = True
        logger.info("metrics_tools logs connected to sqlmesh")


def add_metrics_tools_to_existing_logger(logger_name: str):
    class MetricsToolsFilter(logging.Filter):
        def filter(self, record):
            return record.name == "metrics_tools"

    app_logger = logging.getLogger(logger_name)
    app_logger.addFilter(MetricsToolsFilter())
