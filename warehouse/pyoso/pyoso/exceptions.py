from requests import HTTPError


class OsoError(Exception):
    pass


class OsoHTTPError(HTTPError):
    def __str__(self):
        str = super().__str__()
        response = self.response.json()
        return f"{str} - {response['error'] if response['error'] else response}"


class InsufficientCreditError(OsoError):
    """Raised when the user has insufficient credits to execute a query."""
