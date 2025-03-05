import json


def parse_bytes_string(input_bytes: bytes):
    if not input_bytes.strip():
        return []

    input_string = input_bytes.decode("utf-8")

    json_objects = [obj.strip() for obj in input_string.strip("[]").split("][")]
    parsed_objects = []
    for obj in json_objects:
        parsed_objects.extend(json.loads(f"[{obj}]"))

    return parsed_objects
