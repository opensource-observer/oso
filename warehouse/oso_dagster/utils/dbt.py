import logging
import os
import pathlib
import typing as t
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml
from dagster_dbt import DbtCliResource

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class BQTargetConfigTemplate:
    job_execution_time_seconds: int = 3600
    job_retries: int = 3
    location: str = "US"
    method: str = "oauth"
    keyfile: str = ""
    impersonate_service_account: str = ""
    threads: int = 32

    def as_dict(self) -> dict:
        output = asdict(self)
        output["type"] = "bigquery"
        if self.method == "oauth":
            del output["keyfile"]
            if self.impersonate_service_account == "":
                del output["impersonate_service_account"]
        else:
            del output["impersonate_service_account"]
        return output


def get_profiles_dir():
    # Gets the path to dbt profiles
    return os.environ.get("DBT_PROFILES_DIR", os.path.expanduser("~/.dbt"))


def default_profiles_path():
    # Gets the default path for the dbt `profiles.yml` file
    return os.path.join(get_profiles_dir(), "profiles.yml")


def generate_dbt_profile(
    project_id: str,
    profile_name: str,
    targets: t.List[t.Tuple[str, str]],
    template: BQTargetConfigTemplate,
):
    """Generates the contents of a dbt `profiles.yml` file

    Parameters
    ----------
    project_id: str
        The Google Cloud project ID
    profile_name: str
        The dbt profile name
    targets: List[Tuple[str, str]]
        List of (dbt_target_name, bigquery_dataset)
        e.g. [("production", "oso"), ("playground", "oso_playground")]
    template: BQTargetConfigTemplate
        The base template to use per target

    Returns
    -------
    str
        Contents to write to a dbt `profiles.yml` file
    """
    targets_dict = dict()
    for target_name, dataset_name in targets:
        target_dict = template.as_dict()
        target_dict["project"] = project_id
        target_dict["dataset"] = dataset_name
        targets_dict[target_name] = target_dict
    yaml_dict = {profile_name: {"outputs": targets_dict}}
    return yaml.dump(yaml_dict)


def write_dbt_profile(
    project_id: str,
    profile_name: str,
    targets: t.List[t.Tuple[str, str]],
    template: BQTargetConfigTemplate,
    profile_path: str = "",
):
    if not profile_path:
        profile_path = default_profiles_path()

    Path(os.path.dirname(profile_path)).mkdir(parents=True, exist_ok=True)

    generated_profiles_yml = generate_dbt_profile(
        project_id, profile_name, targets, template
    )

    with open(profile_path, "w") as f:
        f.write(generated_profiles_yml)


def support_home_dir_profiles(default: t.Optional[str] = None):
    # DagsterDbt now defaults to using the current working directory for the
    # dbt profile. Our old version relied on the dbt profile being in the
    # home directory. To support both the _old_ style and the new style we
    # will search for both. As we, hope to use sqlmesh in the future, we
    # shouldn't worry about this too much. It would be more work to force
    # people to change their configurations for now
    profiles_dir = os.environ.get("DAGSTER_DBT_PROFILE_DIR", default)
    if not profiles_dir:
        if not os.path.isfile(os.path.join(os.getcwd(), "profiles.yml")):
            profiles_dir = os.path.expanduser("~/.dbt")
    return profiles_dir


def load_dbt_manifests(
    dbt_target_base_dir: str | Path,
    dbt_project_dir: str | Path,
    project_id: str,
    profile_name: str,
    targets: t.List[t.Tuple[str, str]],
    template: BQTargetConfigTemplate,
    parse_projects: bool = False,
    force_auth: bool = False,
) -> t.Dict[str, Path]:
    """
    Run `dbt parse` to create a `manifest.json` for each dbt target
    https://docs.getdbt.com/reference/artifacts/manifest-json
    """
    manifests: t.Dict[str, Path] = dict()
    logger.debug(f"checking for profile {default_profiles_path()}")

    if not os.path.isfile(default_profiles_path()) or force_auth:
        logger.debug("Writing dbt profile")
        write_dbt_profile(
            project_id,
            profile_name,
            targets,
            template,
        )

    if parse_projects:
        logger.debug("generating dbt manifests")
        for target, _ in targets:
            target_path = Path(dbt_target_base_dir, target)
            # Ensure the dbt_target_base_dir exists
            pathlib.Path(dbt_target_base_dir).mkdir(parents=True, exist_ok=True)

            dbt = DbtCliResource(
                project_dir=os.fspath(dbt_project_dir),
                target=target,
                profiles_dir=support_home_dir_profiles(),
            )
            manifests[target] = (
                dbt.cli(
                    ["--quiet", "parse"],
                    target_path=target_path,
                )
                .wait()
                .target_path.joinpath("manifest.json")
            )
    else:
        for target, _ in targets:
            manifests[target] = Path(dbt_target_base_dir, target, "manifest.json")
    return manifests
