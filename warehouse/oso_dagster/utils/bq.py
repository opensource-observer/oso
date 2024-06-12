from typing import List
from dataclasses import dataclass, field

from google.cloud.bigquery import DatasetReference, AccessEntry, Client as BQClient
from google.cloud.bigquery.enums import EntityTypes
from google.cloud.exceptions import NotFound
from dagster_gcp import BigQueryResource
from dagster import DagsterLogManager


@dataclass
class DatasetOptions:
    dataset_ref: DatasetReference
    is_public: bool = False


def ensure_dataset(client: BQClient, options: DatasetOptions):
    try:
        client.get_dataset(options.dataset_ref)
    except NotFound:
        client.create_dataset(options.dataset_ref)
    # Manage the public settings for this dataset
    dataset = client.get_dataset(options.dataset_ref)
    access_entries = dataset.access_entries
    new_entries: List[AccessEntry] = []
    if options.is_public:
        new_entries.append(
            AccessEntry(
                role="READER",
                entity_type=EntityTypes.SPECIAL_GROUP.value,
                entity_id="allAuthenticatedUsers",
            )
        )
    for entry in access_entries:
        if entry.entity_id == "allAuthenticatedUsers":
            continue
        new_entries.append(entry)
    dataset.access_entries = new_entries

    client.update_dataset(dataset, ["access_entries"])
