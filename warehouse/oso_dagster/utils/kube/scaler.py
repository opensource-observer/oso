# We have some resources that should only be scaled up if they are in use by a
# dagster job.
from kr8s.objects import Deployment


async def ensure_scale_up(*, name: str, namespace: str, scale: int) -> None:
    # Check if the deployment is in use by a dagster job
    deployment = await Deployment.get(name=name, namespace=namespace)
    if deployment.replicas != scale:
        await deployment.scale(scale)


async def ensure_scale_down(*, name: str, namespace: str) -> None:
    # Check if the deployment is in use by a dagster job
    deployment = await Deployment.get(name=name, namespace=namespace)
    if deployment.replicas != 0:
        await deployment.scale(0)
