import logging
from discord_webhook import DiscordWebhook

logger = logging.getLogger(__name__)


class AlertManager:
    """Base class for an alert manager"""

    def alert(self, message: str):
        raise NotImplementedError()


class LogAlertManager(AlertManager):
    def alert(self, message: str):
        logging.error(message)


class DiscordWebhookAlertManager(AlertManager):
    def __init__(self, url: str):
        self._url = url

    def alert(self, message: str):
        wh = DiscordWebhook(url=self._url, content=message)
        wh.execute()
