import json
import typing as t
from dataclasses import dataclass


@dataclass
class QueryData:
    columns: list[str]
    data: list[list[t.Any]]


def parse_bytes_string(input_bytes: bytes) -> QueryData:
    if not input_bytes.strip():
        return QueryData(columns=[], data=[])

    input_string = input_bytes.decode("utf-8")

    json_objects = [
        "{" + obj.strip() + "}" for obj in input_string.strip("{}").split("}{")
    ]
    columns = []
    data = []
    for obj in json_objects:
        parsed_obj = json.loads(obj)
        if "columns" in parsed_obj:
            columns.extend(parsed_obj["columns"])
        if "data" in parsed_obj:
            data.extend(parsed_obj["data"])

    return QueryData(columns=columns, data=data)
