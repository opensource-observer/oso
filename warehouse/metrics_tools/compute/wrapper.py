# A very basic cli or function wrapper that starts a dask cluster and injects an
# environment variable for it that sqlmesh can use.

import subprocess
import sys


def cli():
    subprocess.run(sys.argv[1:])


if __name__ == "__main__":
    cli()
