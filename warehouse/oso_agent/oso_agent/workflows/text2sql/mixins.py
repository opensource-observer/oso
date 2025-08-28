import logging
import typing as t

from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.indices.base import BaseIndex
from llama_index.core.indices.struct_store.sql_query import (
    DEFAULT_RESPONSE_SYNTHESIS_PROMPT,
)
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.prompts import PromptTemplate
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.retrievers import BaseRetriever, NLSQLRetriever
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.core.workflow import Context, StopEvent, step
from oso_agent.clients import OsoClient
from oso_agent.resources import ResourceDependency
from oso_agent.tool.oso_sql_db import OsoSqlDatabase
from oso_agent.tool.oso_text2sql import DEFAULT_INCLUDE_TABLES, DEFAULT_TABLES_TO_INDEX
from oso_agent.tool.storage_context import setup_storage_context
from oso_agent.types.response import AnyResponse, SqlResponse
from oso_agent.types.sql_query import SqlQuery
from oso_agent.util.config import AgentConfig
from oso_agent.workflows.base import MixableWorkflow
from oso_agent.workflows.types import (
    RetrySemanticQueryEvent,
    RowContextEvent,
    SchemaAnalysisEvent,
    SQLExecutionRequestEvent,
    SQLResultEvent,
    SQLResultSummaryRequestEvent,
    SQLResultSummaryResponseEvent,
    StartQueryEngineEvent,
    Text2SQLGenerationEvent,
)
from pyoso import Client

logger = logging.getLogger(__name__)


class GenericText2SQLRouter(MixableWorkflow):
    """A generic mixin class for handling text to sql events in text2sql
    workflows.

    The two events this handles are Text2SQLGenerationEvent and SQLResultEvent.

    In both cases this mixin provides a way to short-circuit the workflow
    depending on the options specified in the given events.

    For Text2SQLGenerationEvent:
        - If execute_sql is True, it returns a SQLExecutionRequestEvent.
        - If execute_sql is False, it returns a StopEvent with the generated SQL.

    For SQLResultEvent:
        - If synthesize_response is True, it returns a SQLResultSummaryRequestEvent.
        - If synthesize_response is False, it returns a StopEvent with the raw results.
    """

    @step
    async def handle_text2sql_generation_event(
        self, ctx: Context, event: Text2SQLGenerationEvent
    ) -> SQLExecutionRequestEvent | StopEvent:
        """Handle the text to SQL query event."""
        if event.execute_sql:
            logger.debug(
                f"query execution requested for query[{event.id}]: {event.output_sql}"
            )
            return SQLExecutionRequestEvent(
                id=event.id,
                input_text=event.input_text,
                output_sql=event.output_sql,
                synthesize_response=event.synthesize_response,
                remaining_tries=event.remaining_tries,
                error_context=event.error_context,
            )
        else:
            logger.debug(
                f"query execution not requested for query[{event.id}]: {event.output_sql}"
            )
            return StopEvent(result=SqlResponse(query=SqlQuery(query=event.output_sql)))

    @step
    async def handle_sql_results_rows(
        self, result: SQLResultEvent
    ) -> SQLResultSummaryRequestEvent | StopEvent:
        """Handle the SQL results routing to request a synthesized response."""
        # Here you can process the rows as needed, for example, summarizing them.
        # For this basic example, we just return the rows as a summary.

        logger.info(
            f"Handling SQL results for query[{result.id}] with {len(result.results)} rows"
        )

        if not result.synthesize_response:
            logger.debug(f"SQL result synthesis not requested for query[{result.id}]")
            # If synthesis is not requested, we return the result directly
            # FIXME: we should create new response objects for dataframes and or row lists
            return StopEvent(result=AnyResponse(raw=result.results))

        logger.debug(f"SQL result synthesis requested for query[{result.id}]")
        return SQLResultSummaryRequestEvent(id=result.id, result=result)


class PyosoWorkflow(MixableWorkflow):
    """Mixin class to enable PyOSO integration for agent workflows."""

    oso_client: ResourceDependency[Client]
    enable_retries: bool = False
    max_retries: int = 5

    @step
    async def retrieve_sql_results(
        self, query: SQLExecutionRequestEvent
    ) -> SQLResultEvent | RetrySemanticQueryEvent:
        """Retrieve SQL results using the PyOSO client."""
        if not self.oso_client:
            raise ValueError("PyOSO client is not initialized.")

        try:
            logger.debug(f"Executing SQL query: {query.output_sql}")
            return await self.execute_query(
                query.output_sql, query.input_text, query.id, query.synthesize_response
            )
        except Exception as e:
            logger.error(f"Error retrieving SQL results: {e}")
            logger.debug(f"Failed SQL query was: {query.output_sql}")

            if self.enable_retries and query.remaining_tries > 0:
                retry_number = self.max_retries - query.remaining_tries + 1
                error_context = query.error_context + [
                    f"SQL execution retry {retry_number} failed: {str(e)}"
                ]
                logger.debug(
                    f"SQL execution failed on retry {retry_number}/{self.max_retries}. Error context: {'; '.join(error_context)}"
                )
                return RetrySemanticQueryEvent(
                    input_text=query.input_text,
                    error=e,
                    remaining_tries=query.remaining_tries - 1,
                    error_context=error_context,
                )

            logger.debug(
                f"SQL execution failed after {self.max_retries} retries. Final error: {e}"
            )
            return SQLResultEvent(
                id=query.id,
                input_text=query.input_text,
                output_sql=query.output_sql,
                results=[],
                error=e,
                synthesize_response=query.synthesize_response,
            )

    async def execute_query(
        self,
        query: str,
        input_text: str,
        id: str = "query_execution",
        synthesize_response: bool = True,
    ) -> SQLResultEvent:
        """Execute a SQL query using the PyOSO client."""
        if not self.oso_client:
            raise ValueError("PyOSO client is not initialized.")

        # Example of executing a query and returning results
        df = self.oso_client.to_pandas(query)

        return SQLResultEvent(
            id=id,
            input_text=input_text,
            output_sql=query,
            results=df,
            synthesize_response=synthesize_response,
        )


class OsoDBWorkflow(MixableWorkflow):
    """Mixin class to enable a soon to be deprecated integration for accessing the DB"""

    oso_client: ResourceDependency[OsoClient]
    enable_retries: bool = False
    max_retries: int = 5

    @step
    async def retrieve_sql_results(
        self, ctx: Context, query: SQLExecutionRequestEvent
    ) -> SQLResultEvent | RetrySemanticQueryEvent:
        """Retrieve SQL results using the OSO DB client."""
        if not self.oso_client:
            raise ValueError("OSO DB client is not initialized.")

        try:
            return await self.execute_query(
                query.output_sql, query.id, query.synthesize_response
            )
        except Exception as e:
            logger.error(f"Error retrieving SQL results: {e}")

            if self.enable_retries and query.remaining_tries > 0:
                retry_number = self.max_retries - query.remaining_tries + 1
                error_context = query.error_context + [
                    f"SQL execution retry {retry_number} failed: {str(e)}"
                ]
                logger.debug(
                    f"SQL execution failed on retry {retry_number}/{self.max_retries}. Error context: {'; '.join(error_context)}"
                )
                return RetrySemanticQueryEvent(
                    input_text=query.input_text,
                    error=e,
                    remaining_tries=query.remaining_tries - 1,
                    error_context=error_context,
                )

            logger.debug(
                f"SQL execution failed after {self.max_retries} retries. Final error: {e}"
            )
            return SQLResultEvent(
                id=query.id,
                input_text=query.input_text,
                output_sql=query.output_sql,
                results=[],
                error=e,
                synthesize_response=query.synthesize_response,
            )

    async def execute_query(
        self, query: str, id: str = "query_execution", synthesize_response: bool = True
    ) -> SQLResultEvent:
        """Execute a SQL query using the PyOSO client."""
        if not self.oso_client:
            raise ValueError("PyOSO client is not initialized.")

        # Example of executing a query and returning results
        results = await self.oso_client.query_oso(query)

        return SQLResultEvent(
            id=id,
            input_text=query,
            output_sql=query,
            results=results,
            synthesize_response=synthesize_response,
        )


class SQLRowsResponseSynthesisMixin(MixableWorkflow):
    """Mixin class to enable SQL response synthesis in agent workflows."""

    response_synthesis_prompt: ResourceDependency[PromptTemplate] = ResourceDependency(
        default_factory=lambda: DEFAULT_RESPONSE_SYNTHESIS_PROMPT
    )
    llm: ResourceDependency[FunctionCallingLLM]

    @step
    async def synthesize_sql_response_from_rows(
        self, request: SQLResultSummaryRequestEvent
    ) -> SQLResultSummaryResponseEvent:
        """Synthesize a SQL response from the generated SQL query and rows."""

        response = self.llm.predict(
            self.response_synthesis_prompt,
            query_str=request.result.input_text,
            sql_query=request.result.output_sql,
            sql_response_str=request.result.result_to_str(),
        )

        return SQLResultSummaryResponseEvent(
            id=request.id,
            summary=response,
            result=request.result,
        )


class OsoVectorDatabaseMixin(MixableWorkflow):
    """Mixin class to enable OSO vector database functionality for context retrieval."""

    oso_client: ResourceDependency[OsoClient]
    llm: ResourceDependency[FunctionCallingLLM]
    embedding: ResourceDependency[BaseEmbedding]
    agent_config: ResourceDependency[AgentConfig]

    include_tables: list[str] = DEFAULT_INCLUDE_TABLES
    tables_to_index: dict[str, list[str]] = DEFAULT_TABLES_TO_INDEX

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sql_database: t.Optional[OsoSqlDatabase] = None
        self._vector_index: t.Optional[BaseIndex] = None
        self._storage_context: t.Optional[StorageContext] = None

    async def _get_sql_database(self) -> OsoSqlDatabase:
        """Get or create the OSO SQL database connection."""
        if self._sql_database is None:
            self._sql_database = await OsoSqlDatabase.create(
                oso_client=self.oso_client,
                include_tables=self.include_tables,
            )
        return self._sql_database

    async def _get_vector_index(self) -> BaseIndex:
        """Get or create the vector index for row context retrieval."""
        if self._vector_index is None:
            storage_context = self._get_storage_context()

            if self.agent_config.vector_store.type == "local":
                self._vector_index = load_index_from_storage(
                    storage_context,
                    index_id=self.agent_config.vector_store.index_name,
                    embed_model=self.embedding,
                )
            else:
                self._vector_index = VectorStoreIndex.from_vector_store(
                    vector_store=storage_context.vector_store,
                    embed_model=self.embedding,
                )

        return self._vector_index

    def _get_storage_context(self) -> StorageContext:
        """Get or create the storage context."""
        if self._storage_context is None:
            self._storage_context = setup_storage_context(
                self.agent_config, embed_model=self.embedding
            )
        return self._storage_context

    @step
    async def analyze_schema(
        self, _ctx: Context, event: StartQueryEngineEvent
    ) -> SchemaAnalysisEvent:
        """
        Analyze the schema to determine which tables are relevant for the query.

        This step replaces the schema analysis logic that was hidden inside QueryEngineTool.
        """
        logger.debug(f"Analyzing schema for query[{event.id}]: {event.input_text}")

        try:
            sql_database = await self._get_sql_database()
            relevant_tables = list(sql_database.get_usable_table_names())

            logger.debug(
                f"Schema analysis complete for query[{event.id}]. "
                f"Found {len(relevant_tables)} relevant tables: {relevant_tables}"
            )

            return SchemaAnalysisEvent(
                id=event.id,
                input_text=event.input_text,
                sql_database=sql_database,
                relevant_tables=relevant_tables,
                synthesize_response=event.synthesize_response,
                execute_sql=event.execute_sql,
            )

        except Exception as e:
            logger.error(f"Error during schema analysis for query[{event.id}]: {e}")
            raise ValueError(
                f"Schema analysis failed for query[{event.id}]: {e}"
            ) from e

    @step
    async def retrieve_row_context(
        self, _ctx: Context, event: SchemaAnalysisEvent
    ) -> RowContextEvent:
        """
        Retrieve relevant row context using embedding-based similarity search.

        This step replaces the row retrieval logic that was hidden inside QueryEngineTool.
        """
        logger.debug(
            f"Retrieving row context for query[{event.id}] with {len(event.relevant_tables)} tables"
        )

        try:
            vector_index = await self._get_vector_index()

            row_retrievers: dict[str, BaseRetriever] = {}

            for table_name in event.relevant_tables:
                if table_name not in self.tables_to_index:
                    row_retrievers[table_name] = VectorStoreIndex(
                        [], embed_model=self.embedding
                    ).as_retriever(similarity_top_k=1)
                    continue

                row_retrievers[table_name] = vector_index.as_retriever(
                    similarity_top_k=5,
                    filters=MetadataFilters(
                        filters=[ExactMatchFilter(key="table_name", value=table_name)]
                    ),
                )

            logger.debug(
                f"Row context retrieval complete for query[{event.id}]. "
                f"Created retrievers for {len(row_retrievers)} tables"
            )

            return RowContextEvent(
                id=event.id,
                input_text=event.input_text,
                sql_database=event.sql_database,
                relevant_tables=event.relevant_tables,
                row_retrievers=row_retrievers,
                synthesize_response=event.synthesize_response,
                execute_sql=event.execute_sql,
            )

        except Exception as e:
            logger.error(
                f"Error during row context retrieval for query[{event.id}]: {e}"
            )
            raise ValueError(
                f"Row context retrieval failed for query[{event.id}]: {e}"
            ) from e


class OsoQueryEngineWorkflowMixin(OsoVectorDatabaseMixin):
    """Complete OSO query engine workflow combining vector database and SQL generation."""

    @step
    async def generate_sql_from_context(
        self, _ctx: Context, event: RowContextEvent
    ) -> Text2SQLGenerationEvent:
        """
        Generate SQL query using LLM with schema and row context.

        This step replaces the SQL generation logic that was hidden inside QueryEngineTool.
        """
        logger.debug(
            f"Generating SQL for query[{event.id}] using {len(event.row_retrievers)} row retrievers"
        )

        try:
            query_engine = NLSQLTableQueryEngine(
                sql_database=event.sql_database,
                tables=event.relevant_tables,
                llm=self.llm,
                embed_model=self.embedding,
                synthesize_response=False,
            )

            query_engine._sql_retriever = NLSQLRetriever(
                event.sql_database,
                llm=self.llm,
                rows_retrievers=event.row_retrievers,
                embed_model=self.embedding,
                sql_only=False,
                verbose=True,
            )

            response = await query_engine.aquery(event.input_text)

            if response.metadata is None:
                raise ValueError("No metadata in query engine response")

            sql_query = response.metadata.get("sql_query")
            if not sql_query:
                raise ValueError("No SQL query found in response metadata")

            logger.debug(f"SQL generation complete for query[{event.id}]: {sql_query}")

            return Text2SQLGenerationEvent(
                id=event.id,
                input_text=event.input_text,
                output_sql=sql_query,
                synthesize_response=event.synthesize_response,
                execute_sql=event.execute_sql,
                remaining_tries=5,
                error_context=[],
            )

        except Exception as e:
            logger.error(f"Error during SQL generation for query[{event.id}]: {e}")
            raise ValueError(f"SQL generation failed for query[{event.id}]: {e}") from e
