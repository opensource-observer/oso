import os
from pathlib import Path

from dagster_dbt import DbtCliResource


main_dbt_project_dir = Path(__file__).joinpath("..", "..", "..").resolve()
main_dbt = DbtCliResource(project_dir=os.fspath(main_dbt_project_dir))

# Leaving this for now as it allows a separate source related dbt model
# source_dbt_project_dir = Path(__file__).joinpath("..", "..", "source_dbt").resolve()
# source_dbt = DbtCliResource(project_dir=os.fspath(source_dbt_project_dir))

# If DAGSTER_DBT_PARSE_PROJECT_ON_LOAD is set, a manifest will be created at run time.
# Otherwise, we expect a manifest to be present in the project's target directory.
if os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD"):
    main_dbt_manifest_path = (
        main_dbt.cli(
            ["--quiet", "parse"],
            target_path=Path("target"),
        )
        .wait()
        .target_path.joinpath("manifest.json")
    )
    # source_dbt_manifest_path = (
    #     source_dbt.cli(
    #         ["--quiet", "parse"],
    #         target_path=Path("target"),
    #     )
    #     .wait()
    #     .target_path.joinpath("manifest.json")
    # )
    # print(f"THE PATH {source_dbt_manifest_path}")
else:
    main_dbt_manifest_path = main_dbt_project_dir.joinpath("target", "manifest.json")
    # source_dbt_manifest_path = source_dbt_project_dir.joinpath(
    #     "target", "manifest.json"
    # )
