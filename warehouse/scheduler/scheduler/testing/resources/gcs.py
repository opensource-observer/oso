from unittest.mock import MagicMock, Mock


class FakeGCSFileResource:
    gcs_project: str

    def __init__(self, gcs_project: str):
        self.gcs_project = gcs_project
        self.mock_client = MagicMock()
        self.async_client = Mock()

        self.mock_client.open.return_value.__enter__.return_value = Mock()
        self.mock_client.open.return_value.__exit__.return_value = None

    def get_client(self, asynchronous: bool = True):
        if asynchronous:
            return self.async_client
        return self.mock_client
