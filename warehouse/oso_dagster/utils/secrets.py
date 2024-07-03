"""
Tools for dealing with secret management.
"""

import os
from typing import Dict
from dataclasses import dataclass
from google.cloud import secretmanager


@dataclass(kw_only=True)
class SecretReference:
    group_name: str
    key: str


class SecretResolver:
    """Resolves secrets given a specific secret reference"""

    def resolve(self, ref: SecretReference) -> bytes:
        raise NotImplementedError("resolve is not implemented in the base class")

    def resolve_as_str(self, ref: SecretReference) -> str:
        return self.resolve(ref).decode("utf-8")


class GCPSecretResolver(SecretResolver):
    @classmethod
    def connect_with_default_creds(cls, project_id: str, prefix: str):
        client = secretmanager.SecretManagerServiceClient()
        return cls(project_id, prefix, client)

    def __init__(
        self,
        project_id: str,
        prefix: str,
        client: secretmanager.SecretManagerServiceClient,
    ):
        self._prefix = prefix
        self._client = client
        self._project_id = project_id

    def resolve(self, ref: SecretReference):
        name = f"projects/{self._project_id}/secrets/{self._prefix}__{ref.group_name}__{ref.key}/versions/latest"
        resp = self._client.access_secret_version(request={"name": name})
        return resp.payload.data


class LocalSecretResolver(SecretResolver):
    """Used for resolving secrets locally (from the environment)"""

    def __init__(self, prefix: str):
        self._prefix = prefix

    def resolve(self, ref: SecretReference):
        secret = os.environ[f"{self._prefix}__{ref.group_name}__{ref.key}".upper()]
        return secret.encode("utf-8")


class SimpleSecretResolver(SecretResolver):
    """Used mostly for testing."""

    def __init__(self, secrets: Dict[str, bytes]):
        self._secrets = secrets

    def resolve(self, ref: SecretReference):
        return self._secrets[f"{ref.group_name}__{ref.key}"]
