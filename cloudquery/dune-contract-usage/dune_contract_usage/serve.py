import sys
from cloudquery.sdk import serve
from .plugin import ContractUsagePlugin


def run():
    p = ContractUsagePlugin()
    serve.PluginCommand(p).run(sys.argv[1:])
