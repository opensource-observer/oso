import logging
import socket
import subprocess
import time
from contextlib import contextmanager

import psutil

logger = logging.getLogger(__name__)


def get_available_port():
    """Find an available port on the local machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@contextmanager
def tls_port_forward(*, namespace: str, name: str, remote_port: int):
    """Using kr8s port forwarding for tls is apparently broken. This is a
    workaround that uses the kubectl command"""
    local_port = get_available_port()
    command = [
        "kubectl",
        "port-forward",
        "--namespace",
        namespace,
        f"service/{name}",
        f"{local_port}:{remote_port}",
    ]
    logger.debug(f"Running command: {' '.join(command)}")

    process = None
    try:
        # Wait for the port-forward to stabilize
        time.sleep(1)

        # Start the port-forward process
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Wait for the port-forward to stabilize
        time.sleep(3)

        # Check if the process is still running and hasn't failed
        if process.poll() is not None:
            assert process.stderr is not None
            stderr_output = process.stderr.read().decode()
            raise RuntimeError(f"Failed to port-forward: {stderr_output.strip()}")

        logger.debug(f"Port-forwarding to service '{name}' on port {local_port}")

        # Yield the chosen local port
        yield local_port

    finally:
        if process:
            # Kill the port-forward process and any children
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            parent.wait(timeout=5)
            logger.debug(f"Port-forwarding terminated for service '{name}'")
