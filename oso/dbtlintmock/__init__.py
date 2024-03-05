import os


def env_var(name, default=None):
    """In case we need to use env_var in model compilation this provides the same
    behaviour"""
    if not default:
        return os.environ[name]
    return os.environ.get(name, default)
