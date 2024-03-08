import sys
from cloudquery.sdk import serve
from .plugin import ExamplePlugin


def run():
    p = ExamplePlugin()
    serve.PluginCommand(p).run(sys.argv[1:])
