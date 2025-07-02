# OSO Agents

A multi-agent framework that can answer questions from the OSO data lake.

> [!WARNING]
> This is a work in progress and is not yet ready for production use yet.

## Installation

Install dependencies from the root

```bash
uv sync --all-packages
```

Get an OSO API key from [Open Source Observer](https://www.opensource.observer).
Follow the instructions in the [Getting OSO API Key](#getting-oso-api-key)
section to obtain your key.

Add this to the `.env` file in `warehouse/oso_mcp/`

## Run the agent

First run the MCP server in a separate terminal:

```bash
uv run mcp serve
```

For now, in another separate terminal run arize phoenix in a docker container
(this command is intentionally ephemeral):

```bash
docker run -it --rm -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest
```

Before we start interacting with any of the agents you will also need to initialize the vector db. On production we use Vertex AI Vector Search. When running locally, you need to setup the vector store to write to a local directory. Update your `.env` to include the following options:

```
AGENT_VECTOR_STORE__TYPE=local
AGENT_VECTOR_STORE__DIR=/some/directory/to/store/vector/db
```

To initialize the vector store run this (it will take a while):

```bash
uv run agent initialize-vector-store
```

Once this is completed you should have a vector db stored on disk. It may take quite a while depending on the speed of your system. Luckily, this should only need to be run if you with to change anything in the vector db.

Finally you can run the agent with an example query:

```bash
% uv run agent query "what columns does the table timeseries_metrics_by_artifact_v0 have?"
Processing query  [####################################]

Response:
────────────────────────────────────────────────────────────────────────────────
The columns are ["metric_id", "artifact_id", "sample_date", "amount", "unit"].
────────────────────────────────────────────────────────────────────────────────
```

For more information on how to run the agent, check the `--help` flag:

```bash
% uv run agent --help
```

## Adding new workflows

Each of the "agents" available in the oso_agent service are modeled as a set of
[llamaindex
workflows](https://docs.llamaindex.ai/en/stable/module_guides/workflow/). In
addition to using existing llamaindex workflow patterns we add some additional
functionality to enable a much more reusable experience that allows for complex
composition of workflows as mixins in the form of the `MixableWorkflow` base
class. This base class, which should be used as the base for any new workflow in
oso_agent, allows for the following:

- Workflow Composition
  - Workflows can be composed of other workflows, allowing for complex
    behavior to be built up from simpler components. This is done by using the
    inherently event driven nature of the vanilla llamaindex workflows, where
    each workflow step simply declares the events for which it is interested
    and the workflow engine will automatically trigger the appropriate steps
    when those events occur.
- Resource Declarations
  - Each `MixableWorkflow` can declare resources that it needs to run. These
    resources are then automatically injected into the workflow as properties
    of the given workflow class.
- Additional methods
  - `wrapped_run`
    - An workflow execution method that specifically wraps responses in the
      workflow with `oso_agent.types.WrappedResponse` objects. In the future
      it might be best to simply replace the `run` function of llamaindex
      but for now this is an additional method.
  - `run_events_iter`
    - An async generator that yields events as they are processed by the
      workflow. This is useful for streaming responses or for debugging
      purposes.

### Defining a new workflow

Workflows are defined in the `oso_agent/workflows` directory. A simple workflow
would look something like this:

```python
from llama_index.core.workflow import step, StartEvent, StopEvent
from oso_agent.workflows import MixableWorkflow, ResourceDependency

class HelloWorkflow(MixableWorkflow):
    """A simple example workflow relies on some resource dependency
    """

    some_dep: ResourceDependency[str]

    @step
    def handle_start(self, event: StartEvent) -> StopEvent:
        print("Hello workflow...")
        print(f"Using resource: {self.some_dep}")
        return StopEvent(
            result=f"Hello from some workflow with dependency {self.some_dep}!",
        )
```

Here we define the most basic type of workflow. If you haven't read the
llamaindex docs on workflows, the most basic workflow must have a step that
consumes a `StartEvent` and must produce a `StopEvent`.

In addition, this workflow defines a resource dependency. Normally, this
resource dependency might be something like a handle to a DB connection or
better yet, an instance of some factory class for db connections. This resource
dependency is injected based on the use of an instance of
`oso_agent.workflows.ResourceResolver` and should function fairly similarly to
dagster resource dependencies. At this time the ResourceResolver is a using a
fairly simple key based retrieval so the attribute name should match the key
used to register the resource. Some additional checks are performed to ensure
that the `ResourceResolver` is providing the correct type of resource.

To instantiate and run this workflow you would do this:

```python
import asyncio
from oso_agent.workflows import ResourceResolver
# Make sure to import HelloWorkflow from the right place, let's pretend it's in
# oso_agent.workflows.hello
from oso_agent.workflows.hello import HelloWorkflow

async def run():
    resolver = ResourceResolver()
    resolver.add_resource("some_dep", "This is a resource dependency")
    workflow = HelloWorkflow(resolver=resolver)
    result = await workflow.run()
    print(result)

if __name__ == "__main__":
    asyncio.run(run())
```

### Adding a new workflow to the service

_This section is currently a work in progress and will be completed soon._

In a previous iteration of this service we selected different agents from an
agent registry. That has now been replaced with a `WorkflowRegistry` that is
used to register workflows. However, the simple agent workflows can still be
modeled as a single workflow.
