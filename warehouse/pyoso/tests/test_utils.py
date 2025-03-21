import json
from unittest import TestCase

from pyoso.utils import QueryData, parse_bytes_string


class TestUtils(TestCase):
    def test_parse_bytes_string_empty(self):
        self.assertEqual(parse_bytes_string(b""), QueryData(columns=[], data=[]))

    def test_parse_bytes_string_single_object(self):
        input_bytes = b'{"columns": ["key"], "data": [["value"]]}'
        expected_output = QueryData(columns=["key"], data=[["value"]])
        self.assertEqual(parse_bytes_string(input_bytes), expected_output)

    def test_parse_bytes_string_multiple_objects(self):
        input_bytes = (
            b'{"columns": ["key1"], "data": [["value1"]]}{"data": [["value2"]]}'
        )
        expected_output = QueryData(columns=["key1"], data=[["value1"], ["value2"]])
        self.assertEqual(parse_bytes_string(input_bytes), expected_output)

    def test_parse_bytes_string_invalid_json(self):
        input_bytes = b'[{"columns": ["key"], "data": [["value"]]}, invalid]'
        with self.assertRaises(json.JSONDecodeError):
            parse_bytes_string(input_bytes)
