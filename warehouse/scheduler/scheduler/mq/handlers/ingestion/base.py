import abc

from scheduler.config import CommonSettings
from scheduler.dlt_destination import DLTDestinationResource
from scheduler.types import HandlerResponse, RunContext, StepContext


class IngestionHandler(abc.ABC):
    """Base class for data ingestion handlers.

    All handlers receive the full set of resources, but only use what they need.
    """

    @abc.abstractmethod
    async def execute(
        self,
        context: RunContext,
        step_context: StepContext,
        config: dict[str, object],
        dataset_id: str,
        org_id: str,
        dlt_destination: DLTDestinationResource,
        common_settings: CommonSettings,
    ) -> HandlerResponse:
        """Execute the ingestion process.

        Args:
            context: The run context
            step_context: The step context for logging and materialization
            config: The ingestion configuration dictionary
            dataset_id: The dataset ID
            org_id: The organization ID
            dlt_destination: DLT destination resource
            common_settings: Common settings

        Returns:
            HandlerResponse indicating success or failure
        """
        raise NotImplementedError
