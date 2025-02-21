import json
import os
from dataclasses import dataclass
from typing import Optional

import requests
from pyoso.exceptions import OsoError, OsoHTTPError

_DEFAULT_BASE_URL = "https://www.opensource.observer/api/v1/"
OSO_API_KEY = "OSO_API_KEY"


@dataclass
class ClientConfig:
    base_url: Optional[str]


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

    def query(self, query: str):
        headers = {}
        if self.__api_key:
            headers["Authorization"] = f"Bearer {self.__api_key}"
        try:
            response = requests.post(
                f"{self.__base_url}sql",
                headers=headers,
                json={"query": query},
                stream=True,
            )
            response.raise_for_status()
            json_response = []
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    json_response.extend(json.loads(chunk))
            return json_response
        except requests.HTTPError as e:
            raise OsoHTTPError(e, response=e.response) from None
