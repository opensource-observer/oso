import json
import os
import sys
from importlib import reload
from unittest import TestCase, mock

import requests
from oso_semantic import Registry
from pyoso.client import Client, ClientConfig
from pyoso.exceptions import OsoError, OsoHTTPError


class TestClient(TestCase):
    DEFAULT_API_KEY = "test_key"
    CUSTOM_API_KEY = "custom_key"

    @mock.patch.dict(os.environ, {"OSO_API_KEY": ""})
    def test_constructor_without_api_key(self):
        with self.assertRaises(OsoError):
            Client(api_key=None)

    @mock.patch.dict(sys.modules, {"oso_semantic": None})
    def test_constructor_without_semantic(self):
        reload(sys.modules["pyoso.client"])
        client = Client(api_key=self.CUSTOM_API_KEY)
        self.assertFalse(
            hasattr(client, "semantic"),
            "Semantic should not be initialized without oso_semantic",
        )

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
            json={"query": query, "format": "minimal"},
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
            json={"query": query, "format": "minimal"},
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
            json={"query": query, "format": "minimal"},
            stream=True,
        )
