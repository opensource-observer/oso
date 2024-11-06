import logging
import os

connected_to_sqlmesh_logs = False


def add_metrics_tools_to_sqlmesh_logging():
    """sqlmesh won't automatically add metrics_tools logging. This will enable
    logs from any of the metrics tools utilities. If sqlmesh is the runner"""
    import __main__

    global connected_to_sqlmesh_logs

    class MetricsToolsFilter(logging.Filter):
        def filter(self, record):
            return record.name == "metrics_tools"

    app_name = os.path.basename(__main__.__file__)
    if app_name == "sqlmesh" and not connected_to_sqlmesh_logs:
        app_logger = logging.getLogger(app_name)
        app_logger.addFilter(MetricsToolsFilter())
        connected_to_sqlmesh_logs = True
