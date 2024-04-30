import os

from dagster import Definitions
from dagster_dbt import DbtCliResource
from dagster_gcp import BigQueryResource, GCSResource

from .assets import (
    main_dbt_assets,
    karma3_globaltrust,
    karma3_globaltrust_config,
    karma3_localtrust,
    optimism_traces_parallel,
)
from .constants import main_dbt_project_dir
from .schedules import schedules

from dotenv import load_dotenv

load_dotenv()

defs = Definitions(
    assets=[
        main_dbt_assets,
        optimism_traces_parallel,
    ]
    + karma3_globaltrust.assets
    + karma3_globaltrust_config.assets
    + karma3_localtrust.assets,
    schedules=schedules,
    resources={
        "main_dbt": DbtCliResource(project_dir=os.fspath(main_dbt_project_dir)),
        "bigquery": BigQueryResource(
            project=os.environ.get("GOOGLE_PROJECT_ID"),  # required
        ),
        "gcs": GCSResource(
            project=os.environ.get("GOOGLE_PROJECT_ID"),  # required
        ),
    },
    jobs=[]
    + karma3_globaltrust.jobs
    + karma3_globaltrust_config.jobs
    + karma3_localtrust.jobs,
    sensors=[]
    + karma3_globaltrust.sensors
    + karma3_globaltrust_config.sensors
    + karma3_localtrust.sensors,
)
