import ast
import sys

from oso_core.cli.utils import CliApp, CliContext
from oso_core.codegen.fake import create_fake_module
from oso_core.codegen.protocol import create_protocol_module
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    CliImplicitFlag,
    CliPositionalArg,
    CliSubCommand,
)


class ProtocolCmd(BaseSettings):
    """Generate a typing.Protocol from a class"""

    import_path: CliPositionalArg[str] = Field(
        description="Import path in the form 'module.path:Class'"
    )
    output_path: CliPositionalArg[str] = Field(description="Path to output file")
    use_inspect: CliImplicitFlag[bool] = Field(
        default=False,
        description="Whether to use the inspect module to gather members (slower, but more accurate)",
    )
    import_overrides: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of module import paths to override when generating the protocol",
    )

    async def cli_cmd(self, context: CliContext) -> None:
        try:
            protocol_mod = create_protocol_module(
                self.import_path,
                use_inspect=self.use_inspect,
                import_overrides=self.import_overrides,
            )
            code = ast.unparse(protocol_mod)
            # Unparse can potentially generate invalid syntax (eg, when there are
            # type comments). We re-parse to ensure validity.
            ast.parse(code)

            with open(self.output_path, "w") as f:
                f.write(code)

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error generating protocol: {e}", file=sys.stderr)
            sys.exit(1)


class FakeCmd(BaseSettings):
    """Generate a fake implementation of a protocol"""

    import_path: CliPositionalArg[str] = Field(
        description="Import path in the form 'module.path:Protocol'"
    )
    output_path: CliPositionalArg[str] = Field(description="Path to output file")

    async def cli_cmd(self, context: CliContext) -> None:
        try:
            fake_mod = create_fake_module(self.import_path)
            code = ast.unparse(fake_mod)

            with open(self.output_path, "w") as f:
                f.write(code)

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error generating fake: {e}", file=sys.stderr)
            sys.exit(1)


class CodegenCLI(
    BaseSettings,
    cli_parse_args=True,
    cli_exit_on_error=False,
    cli_kebab_case=True,
    cli_prog_name="oso-core-codegen",
):
    protocol: CliSubCommand[ProtocolCmd]
    fake: CliSubCommand[FakeCmd]

    def cli_cmd(self, context: CliContext) -> None:
        CliApp.run_subcommand(context, self)


def cli():
    CliApp.run(CodegenCLI, sys.argv[1:])
