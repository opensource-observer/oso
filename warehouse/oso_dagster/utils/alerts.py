import io
import logging
from datetime import datetime
from typing import Mapping, Optional

import pytz
import requests
from attr import dataclass
from dagster import Config, DagsterEvent, DagsterEventType, OpExecutionContext
from dagster._core.events import JobFailureData
from discord_webhook import DiscordEmbed, DiscordWebhook
from PIL import Image, ImageDraw, ImageFile, ImageFont

logger = logging.getLogger(__name__)


class AlertOpConfig(Config):
    run_id: str


class FreshnessOpConfig(Config):
    fresh_assets: int
    stale_assets: Mapping[str, float]


class AlertManager:
    """Base class for an alert manager"""

    def alert(self, message: Optional[str]) -> None:
        raise NotImplementedError()

    def failure_op(
        self, base_url: str, context: OpExecutionContext, config: AlertOpConfig
    ) -> None:
        raise NotImplementedError()

    def freshness_op(self, base_url: str, config: FreshnessOpConfig) -> None:
        raise NotImplementedError()


def get_asset_step_events(
    context: OpExecutionContext,
    config: AlertOpConfig,
) -> list[DagsterEvent]:
    """Get the step events (succeeded and failed) for a given asset in a given run"""

    instance = context.instance
    records = instance.get_records_for_run(config.run_id).records
    events = [record.event_log_entry for record in records if record.event_log_entry]
    dagster_events = [event.dagster_event for event in events if event.dagster_event]

    return dagster_events


class SimpleAlertManager(AlertManager):
    def failure_op(
        self, base_url: str, context: OpExecutionContext, config: AlertOpConfig
    ):
        dagster_events = get_asset_step_events(context, config)
        failures = [event for event in dagster_events if event.is_failure]
        step_failures = [
            failure
            for failure in failures
            if failure.event_type in [DagsterEventType.STEP_FAILURE]
        ]

        self.alert(
            f"{len(step_failures)} failed steps in run ({base_url}/runs/{config.run_id})"
        )

    def freshness_op(self, base_url, config):
        output_lines: list[str] = []

        for asset, timestamp in config.stale_assets.items():
            output_lines.append(
                f"{asset} last materialized at {datetime.fromtimestamp(timestamp)}"
            )

        self.alert("\n".join(output_lines))


class LogAlertManager(SimpleAlertManager):
    def alert(self, message: Optional[str]):
        logging.error(message)


class DiscordWebhookAlertManager(SimpleAlertManager):
    def __init__(self, url: str):
        self._url = url

    def alert(self, message: Optional[str]):
        wh = DiscordWebhook(url=self._url, content=message)
        wh.execute()


@dataclass
class CanvasConfig:
    job_name: str
    success: bool
    steps_ok: int
    steps_failed: int
    kind: str
    message: str


class CanvasDiscordWebhookAlertManager(AlertManager):
    AVATAR_URL = "https://avatars.githubusercontent.com/u/145079657?s=200&v=4"

    def __init__(self, url: str):
        self._url = url
        self._base_url: str
        self._config: Optional[CanvasConfig] = None
        self._webhook: DiscordWebhook = DiscordWebhook(
            url=self._url, avatar_url=self.AVATAR_URL, username="OSO Alerts"
        )
        self._image: Optional[ImageFile.ImageFile] = None
        self._run_id = "00000000"

    def build_image(self, config: CanvasConfig):
        image = Image.new("RGB", (800, 400), "white")
        medium_font = ImageFont.load_default(38)
        small_font = ImageFont.load_default(24)

        image_req = requests.get(
            self.AVATAR_URL,
            stream=True,
            timeout=10,
        )
        image_bytes = io.BytesIO(image_req.content)
        avatar = Image.open(image_bytes).resize((150, 150))
        image.paste(avatar, (620, 30))

        image_draw = ImageDraw.Draw(image)
        image_draw.text(
            (50, 30),
            f"{self._run_id[-8:]} has failed steps",
            font=medium_font,
            fill="black",
        )

        def format_steps(steps: int) -> str:
            return f"{steps} step{'s' if steps != 1 else ''}"

        text_entries = [
            ("Name", config.job_name),
            ("Type", config.kind),
            ("Status", "Success" if config.success else "Failure"),
            ("Succeeded", format_steps(config.steps_ok)),
            ("Failed", format_steps(config.steps_failed)),
            (
                "Message",
                (
                    config.message[:45] + "..."
                    if len(config.message) > 50
                    else config.message
                ),
            ),
        ]

        y_start = 120
        y_offset = 30

        for i, (label, value) in enumerate(text_entries):
            y_coord = y_start + i * y_offset
            image_draw.text((50, y_coord), label, font=small_font, fill="black")
            image_draw.text((250, y_coord), value, font=small_font, fill="black")

        date_font = ImageFont.load_default(20)

        image_draw.text(
            (550, 350),
            datetime.now(tz=pytz.timezone("America/Denver")).strftime(
                "%Y/%m/%d - %H:%M:%S"
            ),
            font=date_font,
            fill="black",
        )

        image_data = io.BytesIO()
        image.save(image_data, format="PNG")

        return image_data.getvalue()

    def failure_op(
        self, base_url: str, context: OpExecutionContext, config: AlertOpConfig
    ):
        dagster_events = get_asset_step_events(context, config)
        result = next(
            (
                event
                for event in dagster_events
                if event.event_type
                in [DagsterEventType.RUN_SUCCESS, DagsterEventType.RUN_FAILURE]
            ),
            None,
        )

        if not result:
            raise ValueError("Could not find run result")

        job_name = result.job_name

        if isinstance(result.event_specific_data, JobFailureData):
            if (
                result.event_specific_data.first_step_failure_event
                and result.event_specific_data.first_step_failure_event.step_key
            ):
                job_name = result.event_specific_data.first_step_failure_event.step_key

        canvas_config = CanvasConfig(
            job_name=job_name,
            success=result.event_type == DagsterEventType.RUN_SUCCESS,
            steps_ok=len(
                [
                    event
                    for event in dagster_events
                    if event.event_type == DagsterEventType.STEP_SUCCESS
                ]
            ),
            steps_failed=len(
                [
                    event
                    for event in dagster_events
                    if event.is_failure
                    and event.event_type == DagsterEventType.STEP_FAILURE
                ]
            ),
            kind=result.event_type.value,
            message=result.message or "Unknown error cause",
        )

        description = f"Oops! Click [`here`]({base_url}/runs/{config.run_id}) to view the details of this failure."
        self.alert_discord(
            "Failed Materialization", description, canvas_config=canvas_config
        )

    def freshness_op(self, base_url, config):
        output_fields: Mapping[str, str] = {}

        for asset, timestamp in config.stale_assets.items():
            output_fields[asset] = (
                f"[`Asset`]({base_url}/assets/{asset}) last materialized at {datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}"
            )

        self.alert_discord_chunks(
            "Asset Freshness Summary",
            (
                f"Found {config.fresh_assets} fresh assets."
                + (
                    "The following assets are stale:"
                    if len(config.stale_assets) > 0
                    else ""
                )
            ),
            output_fields,
        )

    def alert_discord_chunks(
        self, title: str, description: str, fields: Mapping[str, str]
    ):
        items = list(fields.items())
        if len(items) == 0:
            self.alert_discord(title, description)
            return
        for i in range(0, len(items), 10):
            self.alert_discord(
                title, description if i == 0 else "", fields=items[i : i + 20]
            )

    def alert_discord(
        self,
        title: str,
        description: str,
        fields: Optional[list[tuple[str, str]]] = None,
        canvas_config: Optional[CanvasConfig] = None,
    ):
        embed = DiscordEmbed(
            title=title,
            description=description,
            color="ffffff",
        )
        if canvas_config:
            self._webhook.add_file(
                file=self.build_image(canvas_config), filename="dagster_result.png"
            )
            embed.set_image(url="attachment://dagster_result.png")

        if fields:
            for name, value in fields:
                embed.add_embed_field(name=name, value=value, inline=False)
        self._webhook.add_embed(embed)
        self._webhook.execute()
        self._webhook.remove_embeds()
        self._webhook.remove_files()
