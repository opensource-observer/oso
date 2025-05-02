import click

from ..agent.config import AgentConfig

pass_config = click.make_pass_decorator(AgentConfig, ensure=True)


def common_options(f):
    """Common options decorator for commands that use the agent."""
    f = click.option(
        "--system-prompt",
        "-p",
        help="System prompt for the agent",
        envvar="AGENT_SYSTEM_PROMPT",
    )(f)
    return f
