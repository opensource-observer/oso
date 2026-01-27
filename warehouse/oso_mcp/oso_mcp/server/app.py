import base64
import hashlib
import os
import re
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Generic, List, Optional, TypeVar, Union

import requests
from mcp.server.fastmcp import Context, FastMCP
from pyoso import Client, ClientConfig

from .config import MCPConfig

MCP_SSE_PORT = 8000

P = TypeVar("P")
R = TypeVar("R")


@dataclass
class McpErrorResponse(Generic[P]):
    tool_name: str
    error: str
    success: bool = False
    parameters: Optional[List[P]] = None


@dataclass
class McpSuccessResponse(Generic[P, R]):
    tool_name: str
    results: List[R]
    success: bool = True
    parameters: Optional[List[P]] = None


McpResponse = Union[McpErrorResponse[P], McpSuccessResponse[P, R]]


@dataclass
class AppContext:
    oso_client: Optional[Client] = None


def default_lifespan(config: MCPConfig):
    @asynccontextmanager
    async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
        """Manage application lifecycle with OSO client in context"""
        api_key = config.oso_api_key

        client = Client(
            api_key=api_key.get_secret_value(),
            client_opts=ClientConfig(base_url=config.pyoso_base_url),
        )
        context = AppContext(oso_client=client)

        try:
            yield context
        finally:
            pass

    return app_lifespan


def setup_mcp_app(config: MCPConfig):
    mcp = FastMCP(
        "OSO Data Lake Explorer",
        port=config.port,
        host=config.host,
        dependencies=["pyoso", "python-dotenv", "requests"],
        lifespan=default_lifespan(config),
    )

    @mcp.tool(
        description="Convert a natural language question into a SQL query using the OSO text2sql agent. Returns the generated SQL string.",
    )
    async def query_text2sql_agent(nl_query: str, ctx: Context) -> McpResponse:
        """
        Convert a natural language question into a SQL query using the OSO text2sql agent.

        Args:
            natural_language_query (str): The user's question in plain English.
            ctx (Context): The request context.

        Returns:
            McpSuccessResponse: Generated SQL string.
            McpErrorResponse: On error, contains error details.

        Example:
            query_text2sql_agent("Show all projects in the Ethereum collection", ctx)
        """
        if ctx:
            await ctx.info(f"Converting natural language query to SQL: {nl_query}")

        api_key = config.oso_api_key
        if not api_key:
            raise ValueError("OSO API key is not available in the context")

        url = config.text2sql_endpoint
        headers = {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }

        data = {
            "id": str(uuid.uuid4()),
            "messages": [{"role": "user", "content": nl_query}],
        }

        response = requests.post(url, json=data, headers=headers)

        return McpSuccessResponse(
            tool_name="query_text2sql_agent",
            parameters=[nl_query],
            results=[response.json()["sql"]],
        )

    @mcp.tool(
        description="Generates a deterministic OSO ID (SHA256 hash base64 encoded) from a list of input values. Use this to verify IDs in tests.",
    )
    async def generate_oso_id(args: List[Any], ctx: Context) -> McpResponse:
        """
        Generates a deterministic OSO ID.

        Args:
            args: List of values to concatenate and hash (e.g. ["GITHUB", "my-org", "my-repo"] or ["GITHUB", "<repo_id>", 1])
        """
        # Logic matches warehouse/oso_sqlmesh/macros/oso_id.py
        normalized_args: List[str] = [str(a) for a in args]
        concatenated = "".join(normalized_args)
        sha_hash = hashlib.sha256(concatenated.encode("utf-8")).digest()
        # Trino/Presto TO_BASE64 usually returns standard base64
        # We need to ensure it matches exactly how the SQL dialect does it.
        # Based on the macro, it's a simple concat -> sha256 -> base64

        result_id = base64.b64encode(sha_hash).decode("utf-8")
        result_id_hex = sha_hash.hex()

        return McpSuccessResponse(
            tool_name="generate_oso_id",
            parameters=normalized_args,
            results=[
                f"ID (Hex): {result_id_hex}",
                f"ID (Base64): {result_id}",
            ],
        )

    @mcp.tool(description="Upload CSV file as static model to OSO")
    async def upload_csv(
        csv_file_path: str,
        org_name: str,
        dataset_name: str,
        model_name: str,
        ctx: Context,
    ) -> McpResponse:
        """
        Upload a CSV file as a static model to OSO.

        Args:
            csv_file_path (str): Absolute path to the CSV file to upload.
            org_name (str): Organization name (human-readable name or slug).
            dataset_name (str): Dataset name (human-readable name or slug).
            model_name (str): Static model name (must match pattern ^[a-z][a-z0-9_]*$).
            ctx (Context): The request context.

        Returns:
            McpSuccessResponse: Simple success message with upload result.
            McpErrorResponse: On error, contains error details.

        Example:
            upload_csv(
                "/path/to/data.csv",
                "my-organization",
                "my-dataset",
                "my_data_model",
                ctx
            )
        """
        try:
            if not os.path.exists(csv_file_path) or not csv_file_path.endswith(".csv"):
                return McpErrorResponse(
                    tool_name="upload_csv",
                    error=f"File not found or not a CSV file: {csv_file_path}",
                    parameters=[csv_file_path, org_name, dataset_name, model_name],
                )

            if not re.match(r"^[a-z][a-z0-9_]*$", model_name):
                return McpErrorResponse(
                    tool_name="upload_csv",
                    error=f"Model name must match pattern ^[a-z][a-z0-9_]*$: {model_name}",
                    parameters=[csv_file_path, org_name, dataset_name, model_name],
                )

            api_key = config.oso_api_key
            if not api_key:
                return McpErrorResponse(
                    tool_name="upload_csv",
                    error="OSO API key is not configured",
                    parameters=[csv_file_path, org_name, dataset_name, model_name],
                )

            graphql_url = f"{config.pyoso_base_url}/osograph"
            headers = {
                "Authorization": f"Bearer {api_key.get_secret_value()}",
                "Content-Type": "application/json",
            }

            org_query = "query { organizations { edges { node { id name } } } }"
            orgs_response = requests.post(
                graphql_url, json={"query": org_query}, headers=headers
            )
            orgs_response.raise_for_status()
            orgs_data = orgs_response.json()

            if "errors" in orgs_data:
                return McpErrorResponse(
                    tool_name="upload_csv",
                    error=f"GraphQL error fetching organizations: {orgs_data['errors']}",
                    parameters=[csv_file_path, org_name, dataset_name, model_name],
                )

            org_id = next(
                (
                    org["node"]["id"]
                    for org in orgs_data["data"]["organizations"]["edges"]
                    if org["node"]["name"] == org_name
                ),
                None,
            )
            if not org_id:
                return McpErrorResponse(
                    tool_name="upload_csv",
                    error=f"Organization not found: {org_name}",
                    parameters=[csv_file_path, org_name, dataset_name, model_name],
                )

            dataset_query = """query GetDatasets($where: JSON) {
                datasets(where: $where) {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
            }"""
            datasets_response = requests.post(
                graphql_url,
                json={
                    "query": dataset_query,
                    "variables": {"where": {"org_id": {"eq": org_id}}},
                },
                headers=headers,
            )
            datasets_response.raise_for_status()
            datasets_data = datasets_response.json()

            if "errors" in datasets_data:
                return McpErrorResponse(
                    tool_name="upload_csv",
                    error=f"GraphQL error fetching datasets: {datasets_data['errors']}",
                    parameters=[csv_file_path, org_name, dataset_name, model_name],
                )

            dataset_id = next(
                (
                    ds["node"]["id"]
                    for ds in datasets_data["data"]["datasets"]["edges"]
                    if ds["node"]["name"] == dataset_name
                ),
                None,
            )

            if not dataset_id:
                create_dataset_mutation = """
                mutation CreateDataset($input: CreateDatasetInput!) {
                    createDataset(input: $input) {
                        success
                        dataset {
                            id
                            name
                        }
                        message
                    }
                }
                """
                create_dataset_response = requests.post(
                    graphql_url,
                    json={
                        "query": create_dataset_mutation,
                        "variables": {
                            "input": {
                                "orgId": org_id,
                                "name": dataset_name,
                                "displayName": dataset_name,
                                "type": "STATIC_MODEL",
                            }
                        },
                    },
                    headers=headers,
                )
                create_dataset_response.raise_for_status()
                create_dataset_data = create_dataset_response.json()

                if "errors" in create_dataset_data:
                    return McpErrorResponse(
                        tool_name="upload_csv",
                        error=f"GraphQL error creating dataset: {create_dataset_data['errors']}",
                        parameters=[csv_file_path, org_name, dataset_name, model_name],
                    )

                create_dataset_payload = create_dataset_data["data"]["createDataset"]
                if not create_dataset_payload["success"]:
                    return McpErrorResponse(
                        tool_name="upload_csv",
                        error=f"Failed to create dataset: {create_dataset_payload.get('message', 'Unknown error')}",
                        parameters=[csv_file_path, org_name, dataset_name, model_name],
                    )

                dataset_id = create_dataset_payload["dataset"]["id"]

            create_mutation = """
            mutation CreateStaticModel($input: CreateStaticModelInput!) {
                createStaticModel(input: $input) {
                    success
                    staticModel {
                        id
                        name
                    }
                    message
                }
            }
            """
            create_response = requests.post(
                graphql_url,
                json={
                    "query": create_mutation,
                    "variables": {
                        "input": {
                            "orgId": org_id,
                            "datasetId": dataset_id,
                            "name": model_name,
                        }
                    },
                },
                headers=headers,
            )
            create_response.raise_for_status()
            create_data = create_response.json()

            if "errors" in create_data:
                return McpErrorResponse(
                    tool_name="upload_csv",
                    error=f"GraphQL error creating static model: {create_data['errors']}",
                    parameters=[csv_file_path, org_name, dataset_name, model_name],
                )

            create_payload = create_data["data"]["createStaticModel"]
            if not create_payload["success"]:
                return McpErrorResponse(
                    tool_name="upload_csv",
                    error=f"Failed to create static model: {create_payload.get('message', 'Unknown error')}",
                    parameters=[csv_file_path, org_name, dataset_name, model_name],
                )

            static_model_id = create_payload["staticModel"]["id"]

            upload_mutation = """
            mutation CreateStaticModelUploadUrl($staticModelId: ID!) {
                createStaticModelUploadUrl(staticModelId: $staticModelId)
            }
            """
            upload_response = requests.post(
                graphql_url,
                json={
                    "query": upload_mutation,
                    "variables": {"staticModelId": static_model_id},
                },
                headers=headers,
            )
            upload_response.raise_for_status()
            upload_data = upload_response.json()

            if "errors" in upload_data:
                return McpErrorResponse(
                    tool_name="upload_csv",
                    error=f"GraphQL error getting upload URL: {upload_data['errors']}",
                    parameters=[csv_file_path, org_name, dataset_name, model_name],
                )

            upload_url = upload_data["data"]["createStaticModelUploadUrl"]

            with open(csv_file_path, "rb") as f:
                put_response = requests.put(
                    upload_url, data=f, headers={"Content-Type": "text/csv"}
                )
                put_response.raise_for_status()

            create_run_mutation = """
            mutation CreateStaticModelRunRequest($input: CreateStaticModelRunRequestInput!) {
                createStaticModelRunRequest(input: $input) {
                    success
                    message
                    run {
                        id
                        status
                    }
                }
            }
            """
            run_response = requests.post(
                graphql_url,
                json={
                    "query": create_run_mutation,
                    "variables": {
                        "input": {
                            "datasetId": dataset_id,
                            "selectedModels": [static_model_id],
                        }
                    },
                },
                headers=headers,
            )
            run_response.raise_for_status()
            run_data = run_response.json()

            if "errors" in run_data:
                return McpErrorResponse(
                    tool_name="upload_csv",
                    error=f"GraphQL error creating run: {run_data['errors']}. CSV uploaded successfully but run creation failed.",
                    parameters=[csv_file_path, org_name, dataset_name, model_name],
                )

            run_payload = run_data["data"]["createStaticModelRunRequest"]
            if not run_payload["success"]:
                return McpErrorResponse(
                    tool_name="upload_csv",
                    error=f"Failed to create run: {run_payload.get('message', 'Unknown error')}. CSV uploaded successfully but run creation failed.",
                    parameters=[csv_file_path, org_name, dataset_name, model_name],
                )

            run_id = run_payload["run"]["id"]

            return McpSuccessResponse(
                tool_name="upload_csv",
                parameters=[csv_file_path, org_name, dataset_name, model_name],
                results=[
                    f"Uploaded {csv_file_path} as {model_name} and created run {run_id} for processing"
                ],
            )

        except requests.exceptions.RequestException as e:
            return McpErrorResponse(
                tool_name="upload_csv",
                error=f"Network error: {str(e)}",
                parameters=[csv_file_path, org_name, dataset_name, model_name],
            )
        except Exception as e:
            return McpErrorResponse(
                tool_name="upload_csv",
                error=f"Unexpected error: {str(e)}",
                parameters=[csv_file_path, org_name, dataset_name, model_name],
            )

    return mcp
