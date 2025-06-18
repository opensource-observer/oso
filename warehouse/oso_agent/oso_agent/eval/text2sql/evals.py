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
async def check_valid_sql(
    post_processed: ExampleResult
) -> EvaluationResult:
    return EvaluationResult(
        score=int(is_valid_sql(post_processed.actual_sql_query)),
        label="is_agent_response_valid_sql",
        explanation="Returns a boolean for if the agent's output query is valid (can be parsed by sqlglot)",
        metadata={
            "cleaned_agent_query": post_processed.actual_sql_query,
        },
    )



# eval 2: if the above works then we will run check valid result (as metadata maybe print a .info())
async def check_valid_sql_result(
    post_processed: ExampleResult
) -> EvaluationResult:
    info_str = ""
    if post_processed.is_valid_sql_result:
        info_str = df_info_str(post_processed.actual_results_to_list_tuple())
    else:
        # empty tables should at least have 1 row (column names) so if we get here then something failed
        info_str = "Query execution failed or table does not exist."
    return EvaluationResult(
        score=int(post_processed.is_valid_sql_result),
        label="does_agent_query_return_valid_result",
        explanation="Returns a boolean for if the agent's query returns a valid SQL table (empty table is considered equal)",
        metadata={"agent_sql_result_info": info_str},
    )


# eval 3: query type comparison (metadata should be each set printed)
async def sql_query_type_similarity(
    post_processed: ExampleResult, metadata: dict[str, t.Any]
) -> EvaluationResult:

    output_query_types = set(determine_query_type(post_processed.actual_sql_query))
    expected_query_types = set(metadata.get("query_type") or [])

    return EvaluationResult(
        score=jaccard_similarity_set(output_query_types, expected_query_types),
        label="query_type_similarity",
        explanation="Jaccard's similarity over the types of functions present in each SQL query",
        metadata={
            "output_query_types": sorted(output_query_types),
            "expected_query_types": sorted(expected_query_types),
        },
    )


# eval 4: oso models used (metadata should be each set printed)
async def sql_oso_models_used_similarity(
    post_processed: ExampleResult, metadata: dict[str, t.Any]
) -> EvaluationResult:

    output_oso_models_used = set(
        determine_sql_models_used(post_processed.actual_sql_query)
    )
    expected_oso_models_used = set(metadata.get("sql_models_used") or [])

    return EvaluationResult(
        score=jaccard_similarity_set(output_oso_models_used, expected_oso_models_used),
        label="sql_models_used_similarity",
        explanation="Jaccard's similarity over the tables each query uses",
        metadata={
            "output_oso_models_used": sorted(output_oso_models_used),
            "expected_oso_models_used": sorted(expected_oso_models_used),
        },
    )


# eval 5: result exact match (.info() of each df?)
async def result_exact_match(
    post_processed: ExampleResult
) -> EvaluationResult:

    if post_processed.is_valid_sql_result:
        try:
            score = int(
                result_eq_bool(
                    post_processed.actual_results_to_list_tuple()[1:],
                    post_processed.expected_results_to_list_tuple()[1:],
                    order_matters=post_processed.order_matters,
                )
            )
        except Exception as e:
            logger.exception(f"Result comparison failed: {e}")
            score = -1
    else:
        score = -1

    return EvaluationResult(
        score=score,
        label="sql_result_exact_match",
        explanation="A boolean that reflects if the pandas result of the agent's query EXACTLY matches the expected result",
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
async def result_fuzzy_match(
    post_processed: ExampleResult
) -> EvaluationResult:
    fuzzy_metadata = {}

    if post_processed.is_valid_sql_result:
        try:
            score, fuzzy_metadata = result_eq_float_w_metadata(
                post_processed.actual_results_to_list_tuple()[1:],
                post_processed.expected_results_to_list_tuple()[1:],
                order_matters=post_processed.order_matters,
            )
            score = float(score)  # just to be safe
        except Exception as e:
            logger.exception(f"Result comparison failed: {e}")
            score = -1
            fuzzy_metadata = {}
    else:
        score = -1

    return EvaluationResult(
        score=score,
        label="sql_result_fuzzy_match",
        explanation="A float value that reflects how similar the result of the agent's query is to the expected result | 0 = no similarities, 1 = exact match",
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
