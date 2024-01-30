import sys
import arrow
from dataclasses import dataclass
from typing import List, Tuple, Union, TypeAlias, Optional, Generator
import codecs
import csv

ENCODING = "utf-8"

UsageRow: TypeAlias = tuple[Optional[str], Optional[str], int, int, int]
UsageRows: TypeAlias = List[UsageRow]

csv.field_size_limit(sys.maxsize)


@dataclass
class DuneContractUsageRows:
    date: arrow.Arrow
    address: str
    usage_rows: UsageRows


@dataclass
class DuneContractUsage:
    date: arrow.Arrow
    address: str
    user_address: Optional[str]
    safe_address: Optional[str]
    l2_gas: int
    l1_gas: int
    tx_count: int


def string_to_int(x: str) -> int:
    # If it contains scientific notation, parse as float.
    if "e" in x:
        return int(float(x))

    return int(x)


def parse_dune_csv(path: str) -> Generator[DuneContractUsage, None, None]:
    with codecs.open(path, "r", ENCODING) as fp:
        reader = csv.reader(fp)

        # We might do something with this but doesn't really matter
        csv_headers = next(reader)

        for row in reader:
            parsed_row = parse_dune_contract_usage_csv_row(row)
            row = None
            # Turn parsed row into many rows
            for usage in parsed_row.usage_rows:
                yield DuneContractUsage(
                    parsed_row.date,
                    parsed_row.address,
                    usage[0],
                    usage[1],
                    usage[2],
                    usage[3],
                    usage[4],
                )


def parse_dune_contract_usage_csv_row(row: List[str]) -> DuneContractUsageRows:
    usage_array = parse_dune_csv_array(row[2])
    usage = [
        [
            u[0] if u[0] != "<nil>" else None,
            u[1] if u[1] != "<nil>" else None,
            string_to_int(u[2] if u[2] != "<nil>" else "0"),
            string_to_int(u[3] if u[3] != "<nil>" else "0"),
            string_to_int(u[4]),
        ]
        for u in usage_array
    ]

    return DuneContractUsageRows(
        arrow.get(row[0], "YYYY-MM-DD HH:mm:ss.SSS ZZZ"), row[1], usage
    )


def parse_dune_csv_array(array_string: str) -> List[Union[str, List[Union[str, List]]]]:
    def recursive_parser(
        index: int, depth: int
    ) -> Tuple[List[Union[str, List[Union[str, List]]]], int]:
        index += 1
        result = []
        buffer = ""

        while index < len(array_string):
            if array_string[index] == "]":
                if buffer:
                    result.append(buffer)
                return result, index + 1

            if array_string[index] == "[":
                res, next_index = recursive_parser(index, depth + 1)
                index = next_index
                result.append(res)
                continue

            if array_string[index] != " ":
                buffer += array_string[index]

            if array_string[index] == " " and buffer:
                result.append(buffer)
                buffer = ""

            index += 1

        raise ValueError("Invalid data. An array is unterminated")

    return recursive_parser(0, 0)[0]


if __name__ == "__main__":
    for row in parse_dune_csv(sys.argv[1]):
        print(row)
