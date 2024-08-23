"""
A source macro that can be used for rewriting a source reference at runtime.

This mimics the sources behavior in dbt except that the source and destination
of the rewrite is infinitely flexible.
"""

from typing import Optional, Dict, List
import os
import glob
import yaml
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator
from sqlglot import to_table
from pydantic import BaseModel, model_validator

CURR_DIR = os.path.abspath(os.path.dirname(__file__))
SOURCE_YAML_DIR = os.path.abspath(os.path.join(CURR_DIR, "../sources"))
SOURCE_YAML_GLOB = os.path.join(SOURCE_YAML_DIR, "*.yml")


class TableReference(BaseModel):
    name: str
    catalog: Optional[str] = None
    table_name: Optional[str] = None
    schema_name: str

    @model_validator(mode="after")
    def ensure_table_name(self):
        if self.table_name is None:
            self.table_name = self.name
        return self


class SourcesFile(BaseModel):
    gateway: str
    sources: Dict[str, List[TableReference]]


EnvSourceMap = Dict[str, Dict[str, Dict[str, TableReference]]]


def read_yaml_files(glob_pattern) -> List[SourcesFile]:
    # Something about the multithread/processing of sqlmesh probably interferes
    # with something in pydantic. This is a hack for now to get this working,
    # but we should likely just use a typed dict or a simple dataclass to do
    # this validation.
    from typing import Optional, Dict, List

    class TableReference(BaseModel):
        name: str
        catalog: Optional[str] = None
        table_name: Optional[str] = None
        schema_name: str

        @model_validator(mode="after")
        def ensure_table_name(self):
            if self.table_name is None:
                self.table_name = self.name
            return self

    class SourcesFile(BaseModel):
        gateway: str
        sources: Dict[str, List[TableReference]]

    SourcesFile.model_rebuild()
    sources_files: List[SourcesFile] = []
    # Find all files matching the glob pattern
    for file_name in glob.glob(glob_pattern):
        if os.path.isfile(file_name):
            with open(file_name, "r") as file:
                try:
                    data = yaml.safe_load(file)
                    sources_files.append(SourcesFile.model_validate(data))
                except yaml.YAMLError as exc:
                    print(f"Error parsing {file_name}: {exc}")
    return sources_files


def generate_source_map(sources_files: List[SourcesFile]) -> EnvSourceMap:
    env_source_map: EnvSourceMap = {}
    for sources_file in sources_files:
        if sources_file.gateway not in env_source_map:
            env_source_map[sources_file.gateway] = {}
        source_map = env_source_map[sources_file.gateway]
        for sources in map(lambda s: s.sources, sources_files):
            for key, table_refs in sources.items():
                if key not in source_map:
                    source_map[key] = {}
                for table_ref in table_refs:
                    if table_ref.name in source_map[key]:
                        print("WARNING: table annotated multiple times")
                    source_map[key][table_ref.name] = table_ref
    return env_source_map


@macro()
def source(evaluator: MacroEvaluator, ref: str, table: str):
    """Allows us to change the location of a source when the gateway changes."""
    source_map = generate_source_map(read_yaml_files(SOURCE_YAML_GLOB))
    # print(ENV_SOURCE_MAP)
    print(evaluator.env["SQL"])

    gateway = evaluator.gateway
    if not gateway:
        return ""
    table_ref = source_map[gateway][ref][table]
    if not table_ref.catalog:
        return to_table(f'"{table_ref.schema_name}"."{table_ref.table_name}"')
    return to_table(
        f'"{table_ref.catalog}"."{table_ref.schema_name}"."{table_ref.table_name}"'
    )
