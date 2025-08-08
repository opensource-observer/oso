import json
import os
import sys
from datetime import datetime, timezone
from importlib import reload
from unittest import TestCase, mock

import pandas as pd
import requests
from oso_semantic import Registry
from pyoso.analytics import (
    DataStatus,
    MaterializationStatus,
    PartitionStatus,
    PartitionStatusRange,
)
from pyoso.client import Client, ClientConfig, QueryData, QueryResponse
from pyoso.exceptions import OsoError, OsoHTTPError


class TestClient(TestCase):
    DEFAULT_API_KEY = "test_key"
    CUSTOM_API_KEY = "custom_key"

    @mock.patch.dict(os.environ, {"OSO_API_KEY": ""})
    def test_constructor_without_api_key(self):
        with self.assertRaises(OsoError):
            Client(api_key=None)

    @mock.patch("pyoso.client.create_registry")
    @mock.patch("requests.post")
    def test_to_pandas(self, mock_post: mock.Mock, mock_registry: mock.Mock):
        mock_registry.return_value = Registry()
        mock_response = mock.Mock()
        columns = ["column"]
        data = [["test"]]
        expected_json = {"columns": columns, "data": data}
        mock_response.iter_lines = mock.Mock(
            return_value=[json.dumps(expected_json).encode()]
        )
        mock_post.return_value = mock_response

        client = Client(
            api_key=self.CUSTOM_API_KEY,
            client_opts=ClientConfig(base_url="http://localhost:8000/api/v1"),
        )
        query = "SELECT * FROM test_table"
        df = client.to_pandas(query)

        mock_post.assert_called_once_with(
            "http://localhost:8000/api/v1/sql",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.CUSTOM_API_KEY}",
            },
            json={"query": query, "format": "minimal", "includeAnalytics": True},
            stream=True,
        )
        self.assertEqual(df.columns.tolist(), columns)
        self.assertEqual(df.values.tolist(), data)

    @mock.patch.dict(os.environ, {"OSO_API_KEY": DEFAULT_API_KEY})
    @mock.patch("pyoso.client.create_registry")
    @mock.patch("requests.post")
    def test_to_pandas_with_default_api_key(
        self, mock_post: mock.Mock, mock_registry: mock.Mock
    ):
        mock_registry.return_value = Registry()
        mock_response = mock.Mock()
        columns = ["column"]
        data = [["test"]]
        expected_json = {"columns": columns, "data": data}
        mock_response.iter_lines = mock.Mock(
            return_value=[json.dumps(expected_json).encode()]
        )
        mock_post.return_value = mock_response

        client = Client()
        query = "SELECT * FROM test_table"
        df = client.to_pandas(query)

        mock_post.assert_called_once_with(
            "https://www.opensource.observer/api/v1/sql",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.DEFAULT_API_KEY}",
            },
            json={"query": query, "format": "minimal", "includeAnalytics": True},
            stream=True,
        )
        self.assertEqual(df.columns.tolist(), columns)
        self.assertEqual(df.values.tolist(), data)

    @mock.patch("pyoso.client.create_registry")
    @mock.patch("requests.post")
    def test_to_pandas_http_error(self, mock_post: mock.Mock, mock_registry: mock.Mock):
        mock_registry.return_value = Registry()
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP Error")
        mock_post.return_value = mock_response

        client = Client(api_key=self.CUSTOM_API_KEY)
        query = "SELECT * FROM test_table"

        with self.assertRaises(OsoHTTPError):
            client.to_pandas(query)

        mock_post.assert_called_once_with(
            "https://www.opensource.observer/api/v1/sql",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.CUSTOM_API_KEY}",
            },
            json={"query": query, "format": "minimal", "includeAnalytics": True},
            stream=True,
        )

    @mock.patch("requests.get")
    @mock.patch("requests.post")
    def test_semantic_select_to_pandas(self, mock_post: mock.Mock, mock_get: mock.Mock):
        connector_response_data = [
            {
                "name": "oso.users",
                "description": "User information table",
                "columns": [
                    {"name": "id", "type": "bigint", "description": "User ID"},
                    {"name": "name", "type": "varchar", "description": "User name"},
                    {"name": "email", "type": "varchar", "description": "User email"},
                ],
                "relationships": [],
            }
        ]

        mock_connector_response = mock.Mock()
        mock_connector_response.json.return_value = connector_response_data
        mock_connector_response.raise_for_status.return_value = None
        mock_get.return_value = mock_connector_response

        # Mock the SQL query response
        mock_sql_response = mock.Mock()
        columns = ["id", "name"]
        data = [[1, "Alice"], [2, "Bob"]]
        expected_json = {"columns": columns, "data": data}
        mock_sql_response.iter_lines = mock.Mock(
            return_value=[json.dumps(expected_json).encode()]
        )
        mock_sql_response.raise_for_status.return_value = None
        mock_post.return_value = mock_sql_response

        client = Client(api_key=self.CUSTOM_API_KEY)

        # Test the semantic select functionality
        query_builder = client.semantic.select("users.id", "users.name")
        query_str = query_builder.build().sql(dialect="trino")
        result_df = query_builder.to_pandas()

        # Verify the connector endpoint was called
        mock_get.assert_called_once_with(
            "https://www.opensource.observer/api/v1/connector",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.CUSTOM_API_KEY}",
            },
        )

        # Verify the SQL endpoint was called for the query
        mock_post.assert_called_once_with(
            "https://www.opensource.observer/api/v1/sql",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.CUSTOM_API_KEY}",
            },
            json={"query": query_str, "format": "minimal", "includeAnalytics": True},
            stream=True,
        )

        # Verify the result is a DataFrame
        self.assertIsInstance(result_df, pd.DataFrame)
        self.assertEqual(result_df.columns.tolist(), columns)
        self.assertEqual(result_df.values.tolist(), data)

    @mock.patch("pyoso.client.create_registry")
    @mock.patch("requests.post")
    def test_query_with_analytics(self, mock_post: mock.Mock, mock_registry: mock.Mock):
        mock_registry.return_value = Registry()
        mock_response = mock.Mock()

        # Mock response with asset status and data
        columns = ["column1", "column2"]
        data = [["value1", "value2"]]

        asset_status_line = {
            "assetStatus": [
                {
                    "key": "oso.events",
                    "status": {
                        "partitionStatus": {
                            "numFailed": 0,
                            "numMaterialized": 10,
                            "numMaterializing": 0,
                            "numPartitions": 10,
                            "ranges": [
                                {
                                    "endKey": "2024-01-01",
                                    "startKey": "2024-01-01",
                                    "status": "SUCCESS",
                                }
                            ],
                        },
                        "latestMaterialization": 1642678800,
                    },
                    "dependencies": ["oso.raw_events"],
                }
            ]
        }

        data_line = {"columns": columns, "data": data}

        mock_response.iter_lines = mock.Mock(
            return_value=[
                json.dumps(asset_status_line).encode(),
                json.dumps(data_line).encode(),
            ]
        )
        mock_post.return_value = mock_response

        client = Client(api_key=self.CUSTOM_API_KEY)
        query = "SELECT * FROM oso.events"
        response = client.query(query)

        # Verify the response structure
        self.assertIsInstance(response, QueryResponse)
        self.assertIsInstance(response.data, QueryData)
        self.assertEqual(response.data.columns, columns)
        self.assertEqual(response.data.data, data)

        # Verify analytics data
        analytics = response.analytics
        assert analytics is not None
        self.assertEqual(len(analytics), 1)
        self.assertIn("oso.events", analytics)

        asset = analytics.get("oso.events")
        assert asset is not None
        self.assertIsInstance(asset, DataStatus)
        self.assertEqual(asset.key, "oso.events")
        self.assertEqual(asset.dependencies, ["oso.raw_events"])

        # Verify status details
        self.assertIsInstance(asset.status, MaterializationStatus)
        assert asset.status is not None
        self.assertIsInstance(asset.status.latest_materialization, datetime)
        self.assertEqual(
            asset.status.latest_materialization,
            datetime.fromtimestamp(1642678800, tz=timezone.utc),
        )

        partition_status = asset.status.partition_status
        assert partition_status is not None
        self.assertIsInstance(partition_status, PartitionStatus)
        self.assertEqual(partition_status.num_materialized, 10)
        self.assertEqual(partition_status.num_partitions, 10)
        self.assertEqual(len(partition_status.ranges), 1)

        range_status = partition_status.ranges[0]
        self.assertIsInstance(range_status, PartitionStatusRange)
        self.assertEqual(range_status.status, "SUCCESS")
        self.assertEqual(range_status.start_key, "2024-01-01")


@mock.patch.dict(sys.modules, {"oso_semantic": None})
class TestClientWithoutSemantic(TestCase):
    DEFAULT_API_KEY = "test_key"
    CUSTOM_API_KEY = "custom_key"

    @mock.patch.dict(sys.modules, {"oso_semantic": None})
    def test_constructor_without_semantic(self):
        reload(sys.modules["pyoso.client"])

        from pyoso.client import Client

        client = Client(api_key=self.CUSTOM_API_KEY)
        self.assertFalse(
            hasattr(client, "semantic"),
            "Semantic should not be initialized without oso_semantic",
        )
