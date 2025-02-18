from requests import HTTPError


class OsoHTTPError(HTTPError):
    def __str__(self):
        str = super().__str__()
        response = self.response.json()
        return f"{str} - {response["error"] if response["error"] else response}"
