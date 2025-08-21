import logging
import typing as t
from io import StringIO

import pandas as pd
from oso_agent.eval.valid_sql import is_valid_sql
from oso_agent.types.eval import ExampleResult
from oso_agent.util.jaccard import jaccard_similarity_set
from oso_agent.util.query import determine_query_type, determine_sql_models_used
from oso_agent.util.query_sim import result_eq_bool, result_eq_float_w_metadata
from phoenix.experiments.types import EvaluationResult

logger = logging.getLogger(__name__)


def df_info_str(rows: t.List[t.Tuple]):
    if not rows or len(rows) <= 1 or not isinstance(rows[0], tuple):
        return "Empty table (0 rows)"
    try:
        columns = rows[0]
        data = rows[1:]
        df = pd.DataFrame(data, columns=columns)
        buf = StringIO()
        df.info(buf=buf)
        return buf.getvalue()
    except Exception as e:
        return f"Error generating DataFrame info: {e}"


# eval 1: check valid SQL (this will populate ExampleResult, clean and prepare SQL, and return if valid SQL has passed)
async def sql_syntax_validation(post_processed: ExampleResult) -> EvaluationResult:
    """Check if the generated SQL query is syntactically valid."""
    return EvaluationResult(
        score=int(is_valid_sql(post_processed.actual_sql_query)),
        label="sql_syntax_valid",
        explanation="Whether the generated SQL query is syntactically valid and can be parsed by sqlglot",
        metadata={
            "cleaned_agent_query": post_processed.actual_sql_query,
        },
    )


# eval 2: if the above works then we will run check valid result (as metadata maybe print a .info())
async def sql_execution_success(post_processed: ExampleResult) -> EvaluationResult:
    """Check if the SQL query executes successfully and returns results."""
    info_str = ""
    if post_processed.is_valid_sql_result:
        info_str = df_info_str(post_processed.actual_results_to_list_tuple())
    else:
        # empty tables should at least have 1 row (column names) so if we get here then something failed
        info_str = "Query execution failed or table does not exist."
    return EvaluationResult(
        score=int(post_processed.is_valid_sql_result),
        label="sql_execution_success",
        explanation="Whether the SQL query executes successfully and returns a valid result set",
        metadata={"sql_result_info": info_str},
    )


# eval 3: query type comparison (metadata should be each set printed)
async def sql_function_types_match(
    post_processed: ExampleResult, metadata: dict[str, t.Any]
) -> EvaluationResult:
    """Measure similarity of SQL function types used in queries."""
    output_query_types = set(determine_query_type(post_processed.actual_sql_query))
    expected_query_types = set(metadata.get("query_type") or [])

    return EvaluationResult(
        score=jaccard_similarity_set(output_query_types, expected_query_types),
        label="sql_function_types_match",
        explanation="Similarity of SQL function types (SELECT, JOIN, etc.) between generated and expected queries",
        metadata={
            "output_query_types": sorted(output_query_types),
            "expected_query_types": sorted(expected_query_types),
        },
    )


# eval 4: oso models used (metadata should be each set printed)
async def oso_tables_match(
    post_processed: ExampleResult, metadata: dict[str, t.Any]
) -> EvaluationResult:
    """Measure similarity of OSO database tables used in queries."""
    output_oso_models_used = set(
        determine_sql_models_used(post_processed.actual_sql_query)
    )
    expected_oso_models_used = set(metadata.get("sql_models_used") or [])

    return EvaluationResult(
        score=jaccard_similarity_set(output_oso_models_used, expected_oso_models_used),
        label="oso_tables_match",
        explanation="Similarity of OSO database tables referenced between generated and expected queries",
        metadata={
            "output_oso_models_used": sorted(output_oso_models_used),
            "expected_oso_models_used": sorted(expected_oso_models_used),
        },
    )


# eval 5: result exact match (.info() of each df?)
async def results_exact_match(post_processed: ExampleResult) -> EvaluationResult:
    """Check if query results match exactly with expected results."""
    if post_processed.is_valid_sql_result:
        try:
            exact_match = result_eq_bool(
                post_processed.actual_results_to_list_tuple()[1:],
                post_processed.expected_results_to_list_tuple()[1:],
                order_matters=post_processed.order_matters,
            )
            score = 1.0 if exact_match else 0.0
        except Exception as e:
            logger.exception(f"Result comparison failed: {e}")
            score = 0.0
    else:
        score = 0.0

    return EvaluationResult(
        score=score,
        label="results_exact_match",
        explanation="Whether query results exactly match the expected results (1.0 = exact match, 0.0 = no match)",
        metadata={
            "agent_result_info": df_info_str(
                post_processed.actual_results_to_list_tuple()
            ),
            "expected_result_info": df_info_str(
                post_processed.expected_results_to_list_tuple()
            ),
        },
    )


# eval 6: result fuzzy match (.info() of each df?, maybe some info on why it's fuzzy)
async def results_similarity_score(post_processed: ExampleResult) -> EvaluationResult:
    """Calculate fuzzy similarity between query results and expected results."""
    fuzzy_metadata = {}

    if post_processed.is_valid_sql_result:
        try:
            score, fuzzy_metadata = result_eq_float_w_metadata(
                post_processed.actual_results_to_list_tuple()[1:],
                post_processed.expected_results_to_list_tuple()[1:],
                order_matters=post_processed.order_matters,
            )
            score = float(score)  # ensure it's a float
        except Exception as e:
            logger.exception(f"Result comparison failed: {e}")
            score = 0.0
            fuzzy_metadata = {"error": str(e)}
    else:
        score = 0.0
        fuzzy_metadata = {"execution_failed": True}

    return EvaluationResult(
        score=score,
        label="results_similarity_score",
        explanation="Similarity score between query results and expected results (0.0 = no match, 1.0 = exact match)",
        metadata={
            "agent_result_info": df_info_str(
                post_processed.actual_results_to_list_tuple()
            ),
            "expected_result_info": df_info_str(
                post_processed.expected_results_to_list_tuple()
            ),
            "fuzzy_match_info": fuzzy_metadata,
        },
    )
