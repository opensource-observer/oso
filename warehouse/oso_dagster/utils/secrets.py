"""
Tools for dealing with secret management.
"""

import os
import inspect
from typing import Dict, Optional, Any, Callable
from dagster import EnvVar

from dataclasses import dataclass
from google.cloud import secretmanager
from .types import unpack_config


@dataclass(kw_only=True, frozen=True)
class SecretReference:
    group_name: str
    key: str


@unpack_config(SecretReference)
def secret_ref_arg(
    config: SecretReference,
) -> Any:  # any is returned so this can be used in arg definitions
    return config


class SecretInaccessibleError(Exception):
    def __init__(self, message: str, wrapped_error: Optional[Exception] = None):
        super().__init__(message)
        self.wrapped_error = wrapped_error


class HiddenVar(EnvVar):
    @classmethod
    def create(cls, resolver: "SecretResolver", ref: SecretReference):
        hidden = cls(f"{ref.__repr__()}")
        hidden.setup_resolver(resolver, ref)
        return hidden

    # def __init__(self, resolver: "SecretResolver", ref: SecretReference):
    #     super().__init__(str(uuid.uuid4()))
    #     self._resolver = resolver
    #     self._ref = ref

    def setup_resolver(self, resolver: "SecretResolver", ref: SecretReference):
        self._resolver = resolver
        self._ref = ref

    # @property
    # def env_var_name(self) -> str:
    #     """Returns the name of the environment variable."""
    #     return list(os.environ.keys())[0]

    def get_value(self, default: str | None = None) -> str | None:
        try:
            return self._resolver.resolve_as_str(self._ref)
        except SecretInaccessibleError:
            raise
        except Exception:
            return default


class SecretResolver:
    """Resolves secrets given a specific secret reference"""

    def resolve(self, ref: SecretReference) -> bytes:
        raise NotImplementedError("resolve is not implemented in the base class")

    def resolve_as_str(self, ref: SecretReference) -> str:
        return self.resolve(ref).decode("utf-8")

    def resolve_as_hidden_var(self, ref: SecretReference) -> HiddenVar:
        return HiddenVar.create(self, ref)


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
        try:
            resp = self._client.access_secret_version(request={"name": name})
        except Exception as e:
            raise SecretInaccessibleError(
                "Error retrieving secret from gcp", wrapped_error=e
            )
        return resp.payload.data


class LocalSecretResolver(SecretResolver):
    """Used for resolving secrets locally (from the environment)"""

    def __init__(self, prefix: str):
        self._prefix = prefix

    def resolve(self, ref: SecretReference):
        secret_env_var = f"{self._prefix}__{ref.group_name}__{ref.key}".upper()
        secret = os.environ.get(secret_env_var)
        if not secret:
            raise SecretInaccessibleError(
                f"Cannot access {secret_env_var} in the environment"
            )
        return secret.encode("utf-8")


class SimpleSecretResolver(SecretResolver):
    """Used mostly for testing."""

    def __init__(self, secrets: Dict[str, bytes]):
        self._secrets = secrets

    def resolve(self, ref: SecretReference):
        return self._secrets[f"{ref.group_name}__{ref.key}"]


def resolve_secrets_for_func(resolver: SecretResolver, f: Callable) -> Dict[str, str]:
    signature = inspect.signature(f)
    secrets: Dict[str, str] = {}
    for k, v in signature.parameters.items():
        if not v.default:
            continue
        if isinstance(v.default, SecretReference):
            secrets[k] = resolver.resolve_as_str(v.default)
    return secrets
