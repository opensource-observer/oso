import json
import os
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd
import requests
from pyoso.exceptions import OsoError, OsoHTTPError
from sqlglot import parse

_DEFAULT_BASE_URL = "https://www.opensource.observer/api/v1/"
OSO_API_KEY = "OSO_API_KEY"


@dataclass
class ClientConfig:
    base_url: Optional[str]


@dataclass
class QueryData:
    columns: list[str]
    data: list[list[Any]]


class Client:
    def __init__(
        self, api_key: Optional[str] = None, client_opts: Optional[ClientConfig] = None
    ):
        self.__api_key = api_key if api_key else os.environ.get(OSO_API_KEY)
        if not self.__api_key:
            raise OsoError(
                "API key is required. Either set it in the environment variable OSO_API_KEY or pass it as an argument."
            )
        self.__base_url = _DEFAULT_BASE_URL
        if client_opts and client_opts.base_url:
            self.__base_url = client_opts.base_url
            if not self.__base_url.endswith("/"):
                self.__base_url += "/"

    def __query(
        self, query: str, input_dialect="trino", output_dialect="trino"
    ) -> QueryData:
        # The following checks are only for providing better error messages as
        # the oso api does _not_ support multiple queries nor the use of
        # semicolons.
        if not query:
            raise OsoError("Query cannot be empty.")
        parsed_query = parse(query, dialect=input_dialect)
        if len(parsed_query) != 1:
            raise OsoError(
                "Only single queries are supported. Please provide a single SQL statement."
            )
        query_expression = parsed_query[0]
        assert query_expression is not None, "query could not be parsed"

        headers = {
            "Content-Type": "application/json",
        }
        if self.__api_key:
            headers["Authorization"] = f"Bearer {self.__api_key}"
        try:
            response = requests.post(
                f"{self.__base_url}sql",
                headers=headers,
                json={
                    "query": query_expression.sql(dialect=output_dialect),
                    "format": "minimal",
                },
                stream=True,
            )
            response.raise_for_status()
            columns = []
            data = []
            for chunk in response.iter_lines(chunk_size=None):
                if chunk:
                    parsed_obj = json.loads(chunk)
                    if "columns" in parsed_obj:
                        columns.extend(parsed_obj["columns"])
                    if "data" in parsed_obj:
                        data.extend(parsed_obj["data"])

            return QueryData(columns=columns, data=data)
        except requests.HTTPError as e:
            raise OsoHTTPError(e, response=e.response) from None

    def to_pandas(self, query: str):
        query_data = self.__query(query)
        return pd.DataFrame(
            query_data.data, columns=query_data.columns
        ).convert_dtypes()
