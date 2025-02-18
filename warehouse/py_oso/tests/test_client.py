import os
from logging import config
from unittest import TestCase, mock

import pandas
import requests
from py_oso.client import Client, ClientConfig, OsoHTTPError


class TestClient(TestCase):
    DEFAULT_API_KEY = "test_key"
    CUSTOM_API_KEY = "custom_key"

    @mock.patch("requests.get")
    def test_query(self, mock_get):
        mock_response = mock.Mock()
        expected_json = {"data": "test"}
        mock_response.json.return_value = expected_json
        mock_get.return_value = mock_response

        client = Client(
            api_key=self.CUSTOM_API_KEY,
            client_opts=ClientConfig(base_url="http://localhost:8000/api/v1"),
        )
        query = "SELECT * FROM test_table"
        response = client.query(query)

        mock_get.assert_called_once_with(
            "http://localhost:8000/api/v1/sql",
            headers={"Authorization": f"Bearer {self.CUSTOM_API_KEY}"},
            params={"query": query},
        )
        self.assertEqual(response, expected_json)

    @mock.patch.dict(os.environ, {"OSO_API_KEY": DEFAULT_API_KEY})
    @mock.patch("requests.get")
    def test_query_with_default_api_key(self, mock_get):
        mock_response = mock.Mock()
        expected_json = {"data": "test"}
        mock_response.json.return_value = expected_json
        mock_get.return_value = mock_response

        client = Client()
        query = "SELECT * FROM test_table"
        response = client.query(query)

        mock_get.assert_called_once_with(
            "https://opensource.observer/api/v1/sql",
            headers={"Authorization": f"Bearer {self.DEFAULT_API_KEY}"},
            params={"query": query},
        )
        self.assertEqual(response, expected_json)

    @mock.patch("requests.get")
    def test_query_without_api_key(self, mock_get):
        mock_response = mock.Mock()
        expected_json = {"data": "test"}
        mock_response.json.return_value = expected_json
        mock_get.return_value = mock_response

        client = Client(api_key=None)
        query = "SELECT * FROM test_table"
        response = client.query(query)

        mock_get.assert_called_once_with(
            "https://opensource.observer/api/v1/sql",
            headers={},
            params={"query": query},
        )
        self.assertEqual(response, expected_json)

    @mock.patch("requests.get")
    def test_query_http_error(self, mock_get):
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP Error")
        mock_get.return_value = mock_response

        client = Client(api_key=self.CUSTOM_API_KEY)
        query = "SELECT * FROM test_table"

        with self.assertRaises(OsoHTTPError):
            client.query(query)

        mock_get.assert_called_once_with(
            "https://opensource.observer/api/v1/sql",
            headers={"Authorization": f"Bearer {self.CUSTOM_API_KEY}"},
            params={"query": query},
        )
