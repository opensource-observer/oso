import sys

from oso_core.cli.utils import CliApp, CliContext
from pydantic_settings import (
    CliSubCommand,
)
from scheduler.config import CommonSettings, Initialize, Run, Testing
from scheduler.resources import default_resource_registry


class AsyncWorker(
    CommonSettings, cli_parse_args=True, cli_exit_on_error=False, cli_kebab_case=True
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

    setup_module_logging("asyncworker")
    CliApp.run(AsyncWorker, sys.argv[1:])
