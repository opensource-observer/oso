import asyncio
import logging
import typing as t
from contextlib import ExitStack
from dataclasses import dataclass, replace
from datetime import datetime

from httpx import HTTPStatusError
from opentelemetry.context import Context
from opentelemetry.sdk.trace import Span
from oso_agent.types.eval import ExampleResult
from oso_agent.types.response import ErrorResponse
from oso_agent.util.config import AgentConfig
from oso_agent.workflows.base import MixableWorkflow, ResourceResolver
from oso_agent.workflows.eval import EvalWorkflow, EvalWorkflowResult
from phoenix.experiments.evaluators.base import CodeEvaluator, Evaluator
from phoenix.experiments.functions import (
    Evaluators,
    _evaluators_by_name,
    _get_tracer,
    _str_trace_id,
)
from phoenix.experiments.tracing import capture_spans
from phoenix.experiments.types import (
    AnnotatorKind,
    Dataset,
    EvaluationResult,
    Example,
    ExampleInput,
    ExampleMetadata,
    ExampleOutput,
    Experiment,
    ExperimentEvaluationRun,
    ExperimentRun,
)
from phoenix.utilities.client import VersionedAsyncClient
from phoenix.utilities.json import jsonify

logger = logging.getLogger(__name__)
# tracer = trace.get_tracer(__name__)


class EvalResultEvaluator(CodeEvaluator):
    @classmethod
    def create(
        cls,
        func: t.Callable[..., t.Awaitable[EvaluationResult]],
        name: str = "",
        kind: AnnotatorKind = AnnotatorKind.CODE,
    ) -> "EvalResultEvaluator":
        """Create an evaluator that evaluates the result of an EvalWorkflow run"""
        name = name or func.__name__
        return cls(func=func, name=name, kind=kind)

    def __init__(
        self,
        func: t.Callable[..., t.Awaitable[EvaluationResult]],
        name: str,
        kind: AnnotatorKind,
    ):
        super().__init__()
        self._name = name
        self._kind = kind
        self._func = func

    async def async_evaluate(self, **kwargs: t.Any) -> EvaluationResult:
        """Evaluate the result of an EvalWorkflow run."""
        bound_signature = self._bind_evaluator_signature(**kwargs)
        return await self._func(*bound_signature.args, **bound_signature.kwargs)

    def _bind_evaluator_signature(self, **kwargs: t.Any) -> t.Any:
        """Bind the evaluator signature to the provided kwargs."""
        from inspect import signature

        sig = signature(self._func)
        expected_params = sig.parameters
        # Get the intersection of the expected parameters and the provided kwargs
        bound_params = {k: v for k, v in kwargs.items() if k in expected_params}
        bound_signature = sig.bind(**bound_params)
        bound_signature.apply_defaults()
        return bound_signature


@dataclass(kw_only=True)
class _ExperimentWorkflowResult:
    example: Example
    experiment: Experiment
    experiment_run: ExperimentRun
    eval_workflow_result: EvalWorkflowResult
    post_processed_result: t.Any | None
    output: t.Any | None


class ExperimentRunner:
    """The builtin runner for experiments is a bit lacking and doesn't give us
    the flexibility to run experiments and output the results in easy to read
    way. Part of the issue is that it seems that the phoenix runner stores the
    output results as a set of raw data so looking at the results of the
    workflow if it's structured data is pretty much useless. This experiment
    runner allows us to format the results in any way and also store additional
    information for each of the experiment runs.

    This runner is designed to allow any workflow and evaluators to be run and
    format the results in a way that is useful for us.
    """

    def __init__(
        self,
        *,
        config: AgentConfig,
        resolver_factory: t.Callable[[AgentConfig], t.Awaitable[ResourceResolver]],
        evaluators: Evaluators | None = None,
        concurrent_evaluators: int = 5,
        concurrent_runs: int = 2,
        concurrent_reporting_requests: int = 2,
    ):
        self.config = config
        self.resolver_factory = resolver_factory
        self._evaluators: Evaluators = []
        self._eval_result_evalutors: list[EvalResultEvaluator] = []
        self._phoenix_client: VersionedAsyncClient | None = None
        self._evaluators_semaphore = asyncio.Semaphore(concurrent_evaluators)
        self._reporting_requests_semaphore = asyncio.Semaphore(
            concurrent_reporting_requests
        )
        self._run_semaphore = asyncio.Semaphore(concurrent_runs)

    def add_evaluator(
        self,
        func: t.Callable[..., t.Awaitable[EvaluationResult]],
        name: str = "",
        kind: AnnotatorKind = AnnotatorKind.CODE,
    ) -> None:
        """Add an evaluator to the experiment runner that can support receiving
        the result and post processed result of an EvalWorkflow run."""
        evaluator = EvalResultEvaluator.create(func=func, name=name, kind=kind)
        self._eval_result_evalutors.append(evaluator)

    def _setup_instrumented_workflow(
        self,
        resolver: ResourceResolver,
        workflow_cls: type[MixableWorkflow],
        **kwargs: t.Any,
    ) -> EvalWorkflow:
        """Set up the instrumented workflow for the experiment."""

        workflow = type(
            "Instrumented" + workflow_cls.__name__,
            (
                EvalWorkflow,
                workflow_cls,
            ),
            {},
        )(resolver=resolver, **kwargs)
        return workflow

    async def run_workflow(
        self,
        *,
        main_thread_resolver: ResourceResolver,
        experiment: Experiment,
        workflow: EvalWorkflow,
        example: Example,
        input_generator: t.Callable[[ExampleInput], t.Dict[str, t.Any]],
        post_process_result: t.Callable[
            [Example, EvalWorkflowResult, ResourceResolver], t.Awaitable[t.Any]
        ]
        | None = None,
    ) -> _ExperimentWorkflowResult:
        """Run the experiment with the given workflow and return the results."""

        logger.debug(
            f"waiting for semaphore to run experiment for example {example.id} in experiment {experiment.id}"
        )
        async with self._run_semaphore:
            logger.info(
                f"Running experiment for example {example.id} in experiment {experiment.id}"
            )
            start_time = datetime.now()
            try:
                eval_workflow_result, span = await self._run_workflow(
                    experiment=experiment,
                    workflow=workflow,
                    input=example.input,
                    input_processor=input_generator,
                )
                end_time = datetime.now()
            except Exception as e:
                logger.error(
                    f"Error running workflow for example {example.id} in experiment {experiment.id}: {e}"
                )
                raise e

            if not eval_workflow_result:
                logger.warning(
                    f"No result for example {example.id} in experiment {experiment.id}. Skipped"
                )
                raise Exception("No result for example in experiment")

            post_processed = None
            if post_process_result:
                logger.info(
                    f"Post processing result for example {example.id} in experiment {experiment.id}"
                )
                post_processed = await post_process_result(
                    example, eval_workflow_result, main_thread_resolver
                )

            response_text = (
                eval_workflow_result.final_result.response
                if eval_workflow_result.final_result
                else ""
            )

            output = (
                f"{post_processed.actual_sql_query}\n\n{'=' * 120}\n\n{response_text}"
                if post_processed
                and isinstance(post_processed, ExampleResult)
                and post_processed.actual_sql_query
                else response_text
            )

            error = None
            if isinstance(eval_workflow_result.final_result, ErrorResponse):
                logger.info(f"Error in experiment run: {error}")
                error = eval_workflow_result.final_result.message

            span_context = span.get_span_context()
            trace_id = None
            if span_context is not None:
                trace_id = _str_trace_id(span_context.trace_id)

            exp_run = ExperimentRun(
                start_time=start_time,
                end_time=end_time,
                experiment_id=experiment.id,
                dataset_example_id=example.id,
                repetition_number=1,
                output=str(output),
                error=error,
                trace_id=trace_id,
            )

            try:
                logger.info(
                    f"Creating experiment run for example {example.id} in experiment {experiment.id}"
                )
                resp = await self.phoenix_request(
                    f"/v1/experiments/{experiment.id}/runs",
                    exp_run,
                )
                exp_run = replace(exp_run, id=resp["data"]["id"])
            except HTTPStatusError as e:
                if e.response.status_code == 409:
                    raise Exception("error submitting experiment run: already exists")
                raise
        return _ExperimentWorkflowResult(
            example=example,
            experiment=experiment,
            experiment_run=exp_run,
            eval_workflow_result=eval_workflow_result,
            post_processed_result=post_processed,
            output=output,
        )

    async def run_evals_for_workflow(
        self,
        *,
        workflow_result: _ExperimentWorkflowResult,
    ) -> None:
        # Release the semaphore as we can now proceed with the evaluations which
        # run in parallel process pools
        example = workflow_result.example
        input = example.input
        expected = example.output
        metadata = example.metadata if hasattr(example, "metadata") else {}
        experiment = workflow_result.experiment
        logger.debug(
            f"beginning evaluations for example {example.id} in experiment {experiment.id}"
        )

        # Evaluate the result using registered evaluators
        evaluation_results: t.Iterable[asyncio.Task[ExperimentEvaluationRun]] = []

        evaluators_by_name = dict(_evaluators_by_name(self._evaluators))
        more_evaluators_by_name = _evaluators_by_name(self._eval_result_evalutors)
        evaluators_by_name.update(more_evaluators_by_name)

        for name, evaluator in evaluators_by_name.items():
            logger.info(
                f"running evaluator {name} for example {example.id} in experiment {experiment.id}"
            )

            evaluation_result = asyncio.create_task(
                self._evaluate_results(
                    name=name,
                    kind=AnnotatorKind.CODE,
                    experiment=experiment,
                    example=example,
                    evaluator=evaluator,
                    experiment_run=workflow_result.experiment_run,
                    output=str(workflow_result.output),
                    input=input,
                    expected=expected,
                    metadata=metadata,
                    result=workflow_result.eval_workflow_result,
                    post_processed=workflow_result.post_processed_result,
                )
            )
            evaluation_results.append(evaluation_result)

        reporting_tasks = []

        async def _report_eval_to_phoenix(eval_run: ExperimentEvaluationRun):
            """Handle the reporting response from the evaluation run."""
            # attempt to post this to phoenix
            resp = await self.phoenix_request("/v1/experiment_evaluations", eval_run)
            eval_run = replace(eval_run, id=resp["data"]["id"])
            return eval_run

        for completed in asyncio.as_completed(evaluation_results):
            try:
                eval_workflow_result = await completed
                reporting_tasks.append(
                    asyncio.create_task(_report_eval_to_phoenix(eval_workflow_result))
                )
            except Exception as e:
                logger.error(f"Error during evaluation: {e}")
                # Handle the error, e.g., log it or raise a custom exception
                continue

        for completed in asyncio.as_completed(reporting_tasks):
            try:
                eval_workflow_result = await completed
                logger.info(
                    f"Experiment evaluation run submitted to Phoenix: {eval_workflow_result.id}"
                )
            except Exception as e:
                logger.error(f"Error during reporting: {e}")
                # Handle the error, e.g., log it or raise a custom exception
                continue

    async def _run_workflow(
        self,
        *,
        experiment: Experiment,
        workflow: EvalWorkflow,
        input: ExampleInput,
        input_processor: t.Callable[[ExampleInput], t.Dict[str, t.Any]],
    ) -> tuple[EvalWorkflowResult | None, Span]:
        """Run the workflow with the given input and return the result."""
        tracer, resource = _get_tracer(experiment.project_name)
        root_span_name = f"experiment_run_{experiment.id}"
        # root_span_kind = "CHAIN"

        with ExitStack() as stack:
            span = t.cast(
                Span,
                stack.enter_context(
                    tracer.start_as_current_span(root_span_name, context=Context())
                ),
            )
            stack.enter_context(capture_spans(resource))
            try:
                result = await workflow.run_for_evals(**input_processor(input))
            except Exception as e:
                logger.error(
                    f"Error running workflow for experiment {experiment.id}: {e}"
                )
                raise e
        return result, span

    async def _evaluate_results(
        self,
        *,
        name: str,
        kind: AnnotatorKind,
        evaluator: Evaluator,
        experiment_run: ExperimentRun,
        experiment: Experiment,
        example: Example,
        output: str,
        input: ExampleInput,
        expected: ExampleOutput,
        metadata: ExampleMetadata,
        result: EvalWorkflowResult,
        post_processed: t.Any | None = None,
    ) -> ExperimentEvaluationRun:
        start_time = datetime.now()
        try:
            eval_result = await evaluator.async_evaluate(
                output=output,
                expected=expected,
                metadata=metadata,
                input=input,
                result=result,
                post_processed=post_processed,
            )
        except Exception as e:
            logger.error(f"Error running evaluator {name}: {e}")
            eval_result = EvaluationResult(
                score=0.0,
                label=name,
                explanation=str(e),
                metadata={},
            )
        end_time = datetime.now()

        return ExperimentEvaluationRun(
            experiment_run_id=experiment_run.id,
            start_time=start_time,
            end_time=end_time,
            name=name,
            annotator_kind=kind.value,
            error=None,
            result=eval_result,
        )

    async def phoenix_request(self, endpoint, data: t.Any):
        """Asynchronously call the phoenix client by queuing requests"""
        async with self._reporting_requests_semaphore:
            resp = await self.phoenix_client.post(
                endpoint,
                json=jsonify(data),
            )
            resp.raise_for_status()
            return resp.json()

    async def run(
        self,
        *,
        dataset: Dataset,
        workflow_cls: type[MixableWorkflow],
        post_process_result: t.Callable[
            [Example, EvalWorkflowResult, ResourceResolver], t.Awaitable[t.Any]
        ]
        | None = None,
        input_generator: t.Callable[[ExampleInput], t.Dict[str, t.Any]] = lambda x: {
            "input": x["question"]
        },
        experiment_name: t.Optional[str] = None,
        experiment_description: t.Optional[str] = None,
        experiment_metadata: t.Optional[t.Mapping[str, t.Any]] = None,
        timeout: int = 600,
    ):
        """Run the experiment on the given dataset."""

        main_thread_resolver = await self.resolver_factory(self.config)

        # Create the eval workflow
        workflow = self._setup_instrumented_workflow(
            workflow_cls=workflow_cls,
            resolver=main_thread_resolver,
            timeout=timeout,
        )

        # Create the experiment in Phoenix

        # Copied from phoenix.experiments.functions.run_experiment
        repetitions = 1
        payload = {
            "version_id": dataset.version_id,
            "name": experiment_name,
            "description": experiment_description,
            "metadata": experiment_metadata,
            "repetitions": 1,
        }

        exp_json = await self.phoenix_request(
            f"/v1/datasets/{dataset.id}/experiments",
            payload,
        )
        exp_data = exp_json["data"]
        project_name = exp_data["project_name"]
        logger.info(f"Found project name: {project_name}")

        experiment = Experiment(
            dataset_id=dataset.id,
            dataset_version_id=dataset.version_id,
            repetitions=repetitions,
            id=exp_data["id"],
            project_name=project_name,
        )

        workflow_results_tasks: list[asyncio.Task[_ExperimentWorkflowResult]] = []

        # Load the dataset
        for example in dataset:
            # Run the workflow for each example in the dataset
            workflow_results_tasks.append(
                asyncio.create_task(
                    self.run_workflow(
                        main_thread_resolver=main_thread_resolver,
                        experiment=experiment,
                        workflow=workflow,
                        example=example,
                        input_generator=input_generator,
                        post_process_result=post_process_result,
                    )
                )
            )

        # For each example in the dataset, run the experiment and collect results

        workflow_results: list[_ExperimentWorkflowResult] = []

        for completed in asyncio.as_completed(workflow_results_tasks):
            try:
                workflow_result = await completed
                workflow_results.append(workflow_result)

            except Exception as e:
                logger.error(f"Error during experiment run: {e}")
                # Handle the error, e.g., log it or raise a custom exception
                continue

        # Run the evaluations for each workflow result
        for workflow_result in workflow_results:
            await self.run_evals_for_workflow(
                workflow_result=workflow_result,
            )
        return experiment

    @property
    def phoenix_client(self):
        if not self._phoenix_client:
            self._phoenix_client = VersionedAsyncClient(
                base_url=self.config.arize_phoenix_base_url,
                # api_key=self.config.arize_phoenix_api_key.get_secret_value(),
            )
        return self._phoenix_client
