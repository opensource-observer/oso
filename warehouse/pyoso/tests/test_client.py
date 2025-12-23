import os
import sys
from importlib import reload
from unittest import TestCase, mock

import requests
from oso_semantic import Registry
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
    @mock.patch("requests.get")
    @mock.patch("requests.post")
    def test_to_pandas(
        self, mock_post: mock.Mock, mock_get: mock.Mock, mock_registry: mock.Mock
    ):
        mock_registry.return_value = Registry()

        # Setup POST response
        mock_post_response = mock.Mock()
        mock_post_response.json.return_value = {
            "id": "query_123",
            "status": "queued",
            "url": None,
        }
        mock_post_response.raise_for_status.return_value = None
        mock_post.return_value = mock_post_response

        # Setup GET responses
        def side_effect_get(url, headers=None, params=None, **kwargs):
            mock_resp = mock.Mock()
            mock_resp.raise_for_status.return_value = None

            if "async-sql" in url and params and params.get("id") == "query_123":
                mock_resp.json.return_value = {
                    "id": "query_123",
                    "status": "completed",
                    "url": "http://s3-bucket/result.csv",
                }
            elif url == "http://s3-bucket/result.csv":
                # Mock iter_lines for streaming response
                mock_resp.iter_lines.return_value = iter(['["column"]', '["test"]'])
            else:
                mock_resp.status_code = 404

            return mock_resp

        mock_get.side_effect = side_effect_get

        client = Client(
            api_key=self.CUSTOM_API_KEY,
            client_opts=ClientConfig(base_url="http://localhost:8000/api/v1"),
        )
        query = "SELECT * FROM test_table"
        df = client.to_pandas(query)

        mock_post.assert_called_once_with(
            "http://localhost:8000/api/v1/async-sql",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.CUSTOM_API_KEY}",
            },
            json={"query": query},
        )

        self.assertEqual(df.columns.tolist(), ["column"])
        self.assertEqual(df.values.tolist(), [["test"]])

    @mock.patch.dict(os.environ, {"OSO_API_KEY": DEFAULT_API_KEY})
    @mock.patch("pyoso.client.create_registry")
    @mock.patch("requests.get")
    @mock.patch("requests.post")
    def test_to_pandas_with_default_api_key(
        self, mock_post: mock.Mock, mock_get: mock.Mock, mock_registry: mock.Mock
    ):
        mock_registry.return_value = Registry()

        # Setup POST response
        mock_post_response = mock.Mock()
        mock_post_response.json.return_value = {
            "id": "query_def",
            "status": "completed",
            "url": "http://s3-bucket/result_def.csv",
        }
        mock_post_response.raise_for_status.return_value = None
        mock_post.return_value = mock_post_response

        # Setup GET response
        def side_effect_get(url, **kwargs):
            mock_resp = mock.Mock()
            mock_resp.raise_for_status.return_value = None
            if url == "http://s3-bucket/result_def.csv":
                mock_resp.iter_lines.return_value = iter(['["column"]', '["test"]'])
            return mock_resp

        mock_get.side_effect = side_effect_get

        client = Client()
        query = "SELECT * FROM test_table"
        df = client.to_pandas(query)

        mock_post.assert_called_once_with(
            "https://www.oso.xyz/api/v1/async-sql",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.DEFAULT_API_KEY}",
            },
            json={"query": query},
        )

        mock_get.assert_called_with("http://s3-bucket/result_def.csv", stream=True)
        self.assertEqual(df.columns.tolist(), ["column"])
        self.assertEqual(df.values.tolist(), [["test"]])

    @mock.patch("pyoso.client.create_registry")
    @mock.patch("requests.post")
    def test_to_pandas_http_error(self, mock_post: mock.Mock, mock_registry: mock.Mock):
        mock_registry.return_value = Registry()
        mock_response = mock.Mock()
        mock_response.status_code = 500
        http_error = requests.HTTPError("HTTP Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        client = Client(api_key=self.CUSTOM_API_KEY)
        query = "SELECT * FROM test_table"

        with self.assertRaises(OsoHTTPError):
            client.to_pandas(query)

        mock_post.assert_called_once_with(
            "https://www.oso.xyz/api/v1/async-sql",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.CUSTOM_API_KEY}",
            },
            json={"query": query},
        )

    @mock.patch("requests.get")
    @mock.patch("requests.post")
    def test_semantic_select_to_pandas(self, mock_post: mock.Mock, mock_get: mock.Mock):
        # Setup Semantic Registry GET response
        connector_response_data = [
            {
                "name": "oso.users",
                "description": "User information table",
                "columns": [
                    {"name": "id", "type": "bigint", "description": "User ID"},
                    {"name": "name", "type": "varchar", "description": "User name"},
                ],
                "relationships": [],
            }
        ]

        # Setup Async SQL responses
        mock_post_response = mock.Mock()
        mock_post_response.json.return_value = {
            "id": "query_sem",
            "status": "completed",
            "url": "http://s3/sem.csv",
        }
        mock_post_response.raise_for_status.return_value = None
        mock_post.return_value = mock_post_response

        def side_effect_get(url, headers=None, **kwargs):
            mock_resp = mock.Mock()
            mock_resp.raise_for_status.return_value = None

            if "connector" in url:
                mock_resp.json.return_value = connector_response_data
            elif url == "http://s3/sem.csv":
                mock_resp.iter_lines.return_value = iter(
                    ['["id", "name"]', '[1, "Alice"]', '[2, "Bob"]']
                )
            return mock_resp

        mock_get.side_effect = side_effect_get

        client = Client(api_key=self.CUSTOM_API_KEY)

        # Test the semantic select functionality
        query_builder = client.semantic.select("users.id", "users.name")
        result_df = query_builder.to_pandas()

        # Verify SQL execution
        self.assertTrue(mock_post.called)
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://www.oso.xyz/api/v1/async-sql")

        # Check columns
        self.assertEqual(result_df.columns.tolist(), ["id", "name"])
        # Check data
        self.assertEqual(result_df.iloc[0]["name"], "Alice")
        self.assertEqual(str(result_df.iloc[0]["id"]), "1")

    @mock.patch("pyoso.client.create_registry")
    @mock.patch("requests.get")
    @mock.patch("requests.post")
    def test_query_with_analytics(
        self, mock_post: mock.Mock, mock_get: mock.Mock, mock_registry: mock.Mock
    ):
        mock_registry.return_value = Registry()

        # Setup POST response
        mock_post_response = mock.Mock()
        mock_post_response.json.return_value = {
            "id": "query_analytics",
            "status": "completed",
            "url": "http://s3/data.csv",
        }
        mock_post_response.raise_for_status.return_value = None
        mock_post.return_value = mock_post_response

        # Setup GET response
        def side_effect_get(url, **kwargs):
            mock_resp = mock.Mock()
            mock_resp.raise_for_status.return_value = None
            if url == "http://s3/data.csv":
                mock_resp.iter_lines.return_value = iter(
                    ['["column1", "column2"]', '["value1", "value2"]']
                )
            return mock_resp

        mock_get.side_effect = side_effect_get

        client = Client(api_key=self.CUSTOM_API_KEY)
        query = "SELECT * FROM oso.events"
        response = client.query(query)

        # Verify the response structure
        self.assertIsInstance(response, QueryResponse)
        self.assertIsInstance(response.data, QueryData)
        self.assertEqual(response.data.columns, ["column1", "column2"])
        self.assertEqual(response.data.data, [["value1", "value2"]])

        # In new implementation analytics is empty
        analytics = response.analytics
        self.assertIsInstance(analytics, (dict, object))  # DataAnalytics or dict
        # Verify it's effectively empty or has no keys
        self.assertEqual(len(analytics), 0)


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
