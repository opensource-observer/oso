import logging

import requests

logger = logging.getLogger(__name__)

def delete_phoenix_dataset(base_url: str, dataset_id: str, api_key: str) -> None:
    """
    Issue a DELETE /v1/datasets/{dataset_id} to the Phoenix API.
    """
    resp = requests.delete(
        f"{base_url.rstrip('/')}/v1/datasets/{dataset_id}",
        headers={"api_key": api_key},
        timeout=30,
    )
    if resp.status_code == 204:
        logger.info("Dataset %s deleted successfully.", dataset_id)
        return

    raise RuntimeError(
        f"Failed to delete dataset {dataset_id}: "
        f"{resp.status_code} {resp.text}"
    )
