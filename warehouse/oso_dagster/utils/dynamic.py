import json
from typing import Any

from dagster import DynamicPartitionsDefinition, SensorEvaluationContext
from oso_dagster.utils.secrets import SecretReference, SecretResolver
from psycopg2.extensions import connection
from pydantic import BaseModel

DYNAMIC_REPLICATION_DATA_QUERY = """
SELECT dr.replication_name, dr.config, dr.credentials_path
FROM dynamic_replications dr
JOIN organizations o ON dr.org_id = o.id
WHERE dr.replication_type = 'rest' AND o.org_name = %s AND dr.replication_name = %s
"""

PARTITION_KEY_FOR_TYPE_QUERY = """
SELECT o.org_name, dr.replication_name
FROM dynamic_replications dr
JOIN organizations o ON dr.org_id = o.id
WHERE dr.replication_type = %s
"""


class DynamicReplication(BaseModel):
    name: str
    config: Any
    credentials_path: str | None


def parse_partition_key(partition_key: str) -> tuple[str, str]:
    org_name, resource_name = partition_key.split("__", 1)
    if not org_name or not resource_name:
        raise Exception(f"Invalid partition key: {partition_key}")
    return org_name, resource_name


def mk_partition_key(org_name: str, resource_name: str) -> str:
    return f"{org_name}__{resource_name}"


def get_credentials(
    secrets: SecretResolver, credentials_path: str | None
) -> Any | None:
    if not credentials_path:
        return None
    group, name = credentials_path.split("__", 1)

    auth_config = json.loads(
        secrets.resolve_as_str(SecretReference(group_name=group, key=name))
    )

    return auth_config


def get_dynamic_replication(
    postgres_conn: connection, partition_key: str
) -> DynamicReplication:
    org_name, resource_name = parse_partition_key(partition_key)
    cur = postgres_conn.cursor()
    cur.execute(
        DYNAMIC_REPLICATION_DATA_QUERY,
        (org_name, resource_name),
    )
    result = cur.fetchone()
    if not result:
        raise Exception(f"No config found for {org_name}.{resource_name}")

    return DynamicReplication(
        name=result[0], config=result[1], credentials_path=result[2]
    )


def get_dynamic_replications_partition_for_type(
    postgres_conn: connection, replication_type: str
):
    cur = postgres_conn.cursor()
    cur.execute(
        PARTITION_KEY_FOR_TYPE_QUERY,
        (replication_type,),
    )
    results = cur.fetchall()

    return {mk_partition_key(row[0], row[1]) for row in results}


def sync_dynamic_partitions(
    context: SensorEvaluationContext,
    partition: DynamicPartitionsDefinition,
    all_partition_keys: set[str],
):
    # Get the set of existing partitions
    # Retrieve existing partitions and normalize to string keys
    existing_raw = context.instance.get_dynamic_partitions(str(partition.name))
    existing_partitions = set(map(str, existing_raw or []))

    # Find new partitions to add
    new_partitions = sorted(list(all_partition_keys - existing_partitions))
    if new_partitions:
        context.instance.add_dynamic_partitions(
            partitions_def_name=str(partition.name),
            partition_keys=new_partitions,
        )
        context.log.info(f"Added new partitions: {new_partitions}")

    # Find partitions to delete
    partitions_to_delete = sorted(list(existing_partitions - all_partition_keys))
    for pk in partitions_to_delete:
        try:
            context.instance.delete_dynamic_partition(
                partitions_def_name=str(partition.name),
                partition_key=pk,
            )
            context.log.info(f"Deleted partition: {pk}")
        except Exception as e:
            context.log.error(f"Failed to delete partition {pk}: {e}")
