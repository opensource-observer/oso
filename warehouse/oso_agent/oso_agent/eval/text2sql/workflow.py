import logging


from oso_agent.workflows.eval import EvalWorkflow

from ...workflows.text2sql.basic import BasicText2SQL
from ...tool.oso_mcp_client import OsoMcpClient
from ...workflows import ResourceDependency

logger = logging.getLogger(__name__)



class Text2SQLExperimentWorkflow(BasicText2SQL, EvalWorkflow):
    """We take advantage of the EvalWorkflow which is a MixableWorkflow used to
    create a recording of the results of an EvalWorkflow

    Events are intercepted and processed as part of the normal execution of the
    workflow.
    """

    oso_mcp_client: ResourceDependency[OsoMcpClient]
    keep_distinct: ResourceDependency[bool]

    # clean data
    # execute
    # handle errors
    # run evals

    # eval 1: check valid SQL (this will populate ExampleResult, clean and prepare SQL, and return if valid SQL has passed)
    # eval 2: if the above works then we will run check valid result (as metadata maybe print a .info())
    # eval 3: query type comparison (metadata should be each set printed)
    # eval 4: oso models used (metadata should be each set printed)
    # eval 5: result exact match (.info() of each df?)
    # eval 6: result fuzzy match (.info() of each df?, maybe some info on why it's fuzzy)

    # ensure all evals now follow this layout:
    # return {
    #     "score": 1.0,
    #     "label": "exact match",
    #     "metadata": {"foo": "bar", "trace_id": "12345"}
    # }
