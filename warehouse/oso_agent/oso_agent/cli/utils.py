import click

from ..util.config import AgentConfig

pass_config = click.make_pass_decorator(AgentConfig, ensure=True)

def common_options(f):
    """Common options decorator for commands that use the agent."""
    f = click.option(
        "--agent-name",
        "-n",
        help="Name of the agent to use",
        envvar="AGENT_AGENT_NAME",
    )(f)
    return f
