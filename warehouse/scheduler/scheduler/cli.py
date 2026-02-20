import logging
import sys

from dotenv import load_dotenv
from oso_core.cli.utils import CliApp, CliContext
from oso_core.logging.defaults import configure_structured_logging
from pydantic_settings import (
    CliSubCommand,
)
from scheduler.config import CommonSettings, Initialize, Run, Testing
from scheduler.resources import default_resource_registry

load_dotenv()


class SchedulerCLI(
    CommonSettings,
    cli_parse_args=True,
    cli_exit_on_error=False,
    cli_kebab_case=True,
    cli_prog_name="scheduler",
):
    initialize: CliSubCommand[Initialize]
    run: CliSubCommand[Run]
    testing: CliSubCommand[Testing]

    def cli_cmd(self, context: CliContext) -> None:
        context.data["common_settings"] = self

        resources_registry = default_resource_registry(self)
        context.data["resources_registry"] = resources_registry

        CliApp.run_subcommand(context, self)


def cli():
    from oso_core.logging import setup_module_logging

    configure_structured_logging()
    setup_module_logging("scheduler")
    setup_module_logging("dlt")
    setup_module_logging("google", level=1000)
    setup_module_logging("google.cloud", level=1000)
    setup_module_logging("google.cloud.pubsub_v1", level=logging.INFO)
    CliApp.run(SchedulerCLI, sys.argv[1:])
