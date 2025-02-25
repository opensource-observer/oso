import json
from unittest import TestCase

from pyoso.utils import parse_bytes_string


class TestUtils(TestCase):
    def test_parse_bytes_string_empty(self):
        self.assertEqual(parse_bytes_string(b""), [])

    def test_parse_bytes_string_single_object(self):
        input_bytes = b'[{"key": "value"}]'
        expected_output = [{"key": "value"}]
        self.assertEqual(parse_bytes_string(input_bytes), expected_output)

    def test_parse_bytes_string_multiple_objects(self):
        input_bytes = b'[{"key1": "value1"}, {"key2": "value2"}][{"key3": "value3"}]'
        expected_output = [{"key1": "value1"}, {"key2": "value2"}, {"key3": "value3"}]
        self.assertEqual(parse_bytes_string(input_bytes), expected_output)

    def test_parse_bytes_string_invalid_json(self):
        input_bytes = b'[{"key": "value"}][invalid]'
        with self.assertRaises(json.JSONDecodeError):
            parse_bytes_string(input_bytes)
