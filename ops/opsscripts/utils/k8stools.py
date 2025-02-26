import typing as t

from kr8s.asyncio.objects import Job


async def deploy_oso_k8s_job(
    job_name: str,
    namespace: str,
    cmd: t.List[str],
    user_email: str,
    image: str = "ghcr.io/opensource-observer/oso:latest",
    restart_policy: str = "Never",
    working_dir: str = "",
    env: t.Optional[t.Dict[str, str]] = None,
    resources: t.Optional[t.Dict[str, t.Any]] = None,
    extra_pod_spec: t.Optional[t.Dict[str, t.Any]] = None,
    backoff_limit: int = 1,
    ttl_seconds_after_finished: int = 3600,
):
    """
    Deploys a Kubernetes Job that runs an arbitrary command.

    Args:
        job_name (str): The name of the job.
        namespace (str): The namespace where the job will be created.
        cmd (List[str]): The command to execute in the job.
        image (str, optional): The container image to use. Defaults to "alpine".
        restart_policy (str, optional): The restart policy for the job. Defaults to "Never".

    Returns:
        Job: The created Job object.
    """
    resources = resources or {
        "requests": {"cpu": "100m", "memory": "128Mi"},
        "limits": {"memory": "128Mi"},
    }
    env = env or {}
    k8s_env = [{"name": k, "value": v} for k, v in env.items()]

    container = {
        "name": job_name,
        "image": image,
        "command": cmd,
        "resources": resources,
        "env": k8s_env,
    }
    if working_dir:
        container["workingDir"] = working_dir

    pod_spec = {
        "containers": [container],
        "restartPolicy": restart_policy,
    }
    pod_spec.update(extra_pod_spec or {})

    # Define the Job spec
    job = await Job(
        {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": job_name,
                "namespace": namespace,
                "annotations": {
                    "opensource.observer/user-email": user_email,
                },
            },
            "spec": {
                "template": {
                    "metadata": {"name": job_name},
                    "spec": pod_spec,
                },
                "backoffLimit": backoff_limit,
                "ttlSecondsAfterFinished": ttl_seconds_after_finished,
            },
        }
    )

    await job.create()
    print(f"Job {job_name} created in namespace {namespace}.")
    return job
