import json
import os
from typing import Any

import pandas as pd
import requests
from pydantic import BaseModel
from pyoso.analytics import DataAnalytics, DataStatus
from pyoso.constants import DEFAULT_BASE_URL, OSO_API_KEY
from pyoso.exceptions import OsoError, OsoHTTPError
from pyoso.semantic import create_registry
from sqlglot import parse

HAS_OSO_SEMANTIC = False
try:
    import oso_semantic  # noqa: F401

    HAS_OSO_SEMANTIC = True
except ImportError:
    pass


class ClientConfig(BaseModel):
    base_url: str | None


class QueryData(BaseModel):
    columns: list[str]
    data: list[list[Any]]


class QueryResponse:
    """Response object containing query data and optional analytics."""

    def __init__(self, data: QueryData, analytics: DataAnalytics):
        self._data = data
        self._analytics = analytics

    def to_pandas(self) -> pd.DataFrame:
        """Convert the query data to a pandas DataFrame."""
        return pd.DataFrame(
            self._data.data, columns=self._data.columns
        ).convert_dtypes()

    @property
    def analytics(self) -> DataAnalytics:
        """Get the analytics data."""
        return self._analytics

    @property
    def data(self) -> QueryData:
        """Get the raw query data."""
        return self._data

    @staticmethod
    def from_response_chunks(response_chunks) -> "QueryResponse":
        """Parse HTTP response chunks into QueryResponse."""
        columns = []
        data = []
        analytics = {}

        for chunk in response_chunks:
            if chunk:
                parsed_obj = json.loads(chunk)

                if "assetStatus" in parsed_obj:
                    for asset in parsed_obj["assetStatus"]:
                        data_status = DataStatus.model_validate(asset)
                        analytics[data_status.key] = data_status
                elif "columns" in parsed_obj:
                    columns.extend(parsed_obj["columns"])

                if "data" in parsed_obj:
                    data.extend(parsed_obj["data"])

        query_data = QueryData(columns=columns, data=data)
        return QueryResponse(data=query_data, analytics=DataAnalytics(analytics))


class Client:
    def __init__(
        self, api_key: str | None = None, client_opts: ClientConfig | None = None
    ):
        self.__api_key = api_key if api_key else os.environ.get(OSO_API_KEY)
        if not self.__api_key:
            raise OsoError(
                "API key is required. Either set it in the environment variable OSO_API_KEY or pass it as an argument."
            )
        self.__base_url = DEFAULT_BASE_URL
        if client_opts and client_opts.base_url:
            self.__base_url = client_opts.base_url
            if not self.__base_url.endswith("/"):
                self.__base_url += "/"

        if HAS_OSO_SEMANTIC:
            self.semantic = create_registry(
                self.__base_url, self.__api_key, self.to_pandas
            )

    def __query(
        self,
        query: str,
        input_dialect="trino",
        output_dialect="trino",
        include_analytics: bool = True,
    ) -> QueryResponse:
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
                    "includeAnalytics": include_analytics,
                },
                stream=True,
            )
            response.raise_for_status()

            return QueryResponse.from_response_chunks(
                response.iter_lines(chunk_size=None)
            )
        except requests.HTTPError as e:
            raise OsoHTTPError(e, response=e.response) from None

    def to_pandas(self, query: str):
        query_response = self.__query(query)
        return query_response.to_pandas()

    def query(self, query: str, include_analytics: bool = True) -> QueryResponse:
        """Execute a SQL query and return the full response including analytics data."""
        return self.__query(query, include_analytics=include_analytics)
