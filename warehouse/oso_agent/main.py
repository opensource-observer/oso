import sys

import click
from oso_agent.src.cli import cli


def main():
    """OSO Agent CLI entry point."""
    try:
        cli(standalone_mode=False)  # pylint: disable=no-value-for-parameter
    except click.Abort:
        click.echo("\nOperation aborted.", err=True)
        return 1
    except click.ClickException as e:
        e.show()
        return e.exit_code
    except Exception as e:
        import logging

        logger = logging.getLogger("oso-agent")
        logger.exception("Unhandled exception")
        click.echo(f"Unhandled error: {e}", err=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
