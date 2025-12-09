import sys

from asyncworker.config import CommonSettings, Initialize, Run
from pydantic_settings import (
    CliApp,
    CliSubCommand,
)


class AsyncWorker(
    CommonSettings, cli_parse_args=True, cli_exit_on_error=False, cli_kebab_case=True
):
    initialize: CliSubCommand[Initialize]
    run: CliSubCommand[Run]

    def cli_cmd(self) -> None:
        CliApp.run_subcommand(self)


def cli():
    from oso_core.logging import setup_module_logging

    setup_module_logging("asyncworker")
    CliApp.run(AsyncWorker, sys.argv[1:])
