from typing import List
from dataclasses import dataclass, field

from google.cloud.bigquery import DatasetReference, AccessEntry, Client as BQClient
from google.cloud.bigquery.enums import EntityTypes
from google.cloud.exceptions import NotFound, PreconditionFailed
from .retry import retry


@dataclass
class DatasetOptions:
    dataset_ref: DatasetReference
    is_public: bool = False


def ensure_dataset(client: BQClient, options: DatasetOptions):
    try:
        client.get_dataset(options.dataset_ref)
    except NotFound:
        client.create_dataset(options.dataset_ref)

    def retry_update():
        # Manage the public settings for this dataset
        dataset = client.get_dataset(options.dataset_ref)
        access_entries = dataset.access_entries
        for entry in access_entries:
            # Do nothing if the expected entity already has the correct access
            if entry.entity_id == "allAuthenticatedUsers" and entry.role == "READER":
                return

        new_entries: List[AccessEntry] = []
        if options.is_public:
            new_entries.append(
                AccessEntry(
                    role="READER",
                    entity_type=EntityTypes.SPECIAL_GROUP.value,
                    entity_id="allAuthenticatedUsers",
                )
            )
        new_entries.extend(access_entries)
        dataset.access_entries = new_entries
        client.update_dataset(dataset, ["access_entries"])

    def error_handler(exc: Exception):
        if type(exc) != PreconditionFailed:
            raise exc

    retry(retry_update, error_handler)
