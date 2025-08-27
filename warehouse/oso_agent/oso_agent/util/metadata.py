import logging
import subprocess
import sys
import typing as t
from datetime import datetime
from pathlib import Path

from ..util.config import AgentConfig

logger = logging.getLogger(__name__)


def _is_containerized() -> bool:
    """Detect if running in a container with deployment metadata.

    Returns:
        bool: True if running in production (containerized)
    """
    return Path("/oso.repo_sha.txt").exists() and Path("/oso.ordered_tag.txt").exists()


def _read_metadata_file(filepath: str) -> t.Optional[str]:
    """Read content from a metadata file.

    Args:
        filepath: Path to the metadata file

    Returns:
        str: File content stripped of whitespace, or None if file doesn't exist
    """
    try:
        return Path(filepath).read_text().strip()
    except (FileNotFoundError, PermissionError, OSError):
        logger.debug(f"Failed to read metadata file: {filepath}")
        return None


def get_git_commit_hash() -> t.Optional[str]:
    """Get the current git commit hash.

    Returns:
        str: Git commit hash, or None if not available
    """
    if _is_containerized():
        return _read_metadata_file("/oso.repo_sha.txt")

    try:
        hash_output = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, timeout=10
        )
        return hash_output.strip().decode("utf-8")
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        logger.debug(
            "Failed to get git commit hash - not in git repo or git not available"
        )
        return None


def get_git_branch() -> t.Optional[str]:
    """Get the current git branch name.

    Returns:
        str: Git branch name, or None if not available
    """
    if _is_containerized():
        return "main"

    try:
        branch_output = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return branch_output.strip().decode("utf-8")
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        logger.debug("Failed to get git branch - not in git repo or git not available")
        return None


def get_git_dirty_status() -> bool:
    """Check if the git working directory has uncommitted changes.

    Returns:
        bool: True if there are uncommitted changes, False otherwise
    """
    if _is_containerized():
        return False

    try:
        subprocess.check_output(
            ["git", "diff-index", "--quiet", "HEAD", "--"],
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return False
    except subprocess.CalledProcessError:
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.debug("Failed to check git dirty status")
        return False


def get_workflow_info(workflow_cls: type) -> dict[str, t.Any]:
    """Get information about the workflow class.

    Args:
        workflow_cls: The workflow class being used

    Returns:
        dict: Workflow information including class name, module, etc.
    """
    return {
        "workflow_class": workflow_cls.__name__,
        "workflow_module": workflow_cls.__module__,
        "workflow_mro": [cls.__name__ for cls in workflow_cls.__mro__],
    }


def get_llm_info(config: AgentConfig) -> dict[str, t.Any]:
    """Get LLM configuration information.

    Args:
        config: Agent configuration

    Returns:
        dict: LLM configuration details
    """
    llm_info = {
        "llm_type": config.llm.type,
    }

    if config.llm.type == "local":
        llm_info.update(
            {
                "ollama_model": config.llm.ollama_model,
                "ollama_embedding": config.llm.ollama_embedding,
                "ollama_url": config.llm.ollama_url,
            }
        )
    elif config.llm.type == "google_genai":
        llm_info.update(
            {
                "model": config.llm.model,
                "embedding": config.llm.embedding,
            }
        )

    return llm_info


def get_system_info() -> dict[str, t.Any]:
    """Get system information.

    Returns:
        dict: System information including Python version, platform, etc.
    """
    import platform

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
    }


def collect_experiment_metadata(
    config: AgentConfig,
    workflow_cls: type,
    additional_metadata: t.Optional[dict[str, t.Any]] = None,
) -> dict[str, t.Any]:
    """Collect comprehensive experiment metadata.

    Args:
        config: Agent configuration
        workflow_cls: The workflow class being used
        additional_metadata: Additional metadata to include

    Returns:
        dict: Complete experiment metadata
    """
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "git": {
            "commit_hash": get_git_commit_hash(),
            "branch": get_git_branch(),
            "has_uncommitted_changes": get_git_dirty_status(),
        },
        "workflow": get_workflow_info(workflow_cls),
        "llm": get_llm_info(config),
        "system": get_system_info(),
        "config": {
            "name": config.agent_name,
            "vector_store_type": config.vector_store.type,
            "enable_telemetry": config.enable_telemetry,
            "workflow_timeout": config.workflow_timeout,
        },
    }

    if additional_metadata:
        metadata.update(additional_metadata)

    logger.info(
        f"Collected experiment metadata: git_hash={metadata['git']['commit_hash']}, workflow={metadata['workflow']['workflow_class']}, llm={metadata['llm']['llm_type']}"
    )

    return metadata
