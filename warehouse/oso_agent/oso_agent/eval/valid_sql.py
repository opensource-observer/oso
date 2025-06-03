
import asyncio
from typing import Any, Sequence

from llama_index.core.evaluation.base import BaseEvaluator, EvaluationResult
from llama_index.core.prompts.mixin import PromptDictType
from sqlglot import parse_one


def is_valid_sql(query: str, dialect: str = "trino") -> bool:
    try:
        parse_one(query, dialect=dialect)
        return True
    except Exception:
        return False

class ValidSqlEvaluator(BaseEvaluator):
    """
    Valid SQL evaluator.

    Evaluates whether a response is a valid SQL query in the correct dialect
    This evaluator will only return pass or fail, since we expect the result to be
    fed directly into a SQL engine.

    Args:
        dialect(str): The SQL dialect to use for evaluation (e.g. "mysql", "postgres").
            https://github.com/tobymao/sqlglot/tree/main/sqlglot/dialects
        raise_error(bool): Whether to raise an error when the response is invalid.
            Defaults to False.
    """

    def __init__(
        self,
        dialect: str = "trino",
        raise_error: bool = False,
    ) -> None:
        """Init params."""
        self._dialect = dialect
        self._raise_error = raise_error

    def _get_prompts(self) -> PromptDictType:
        """Get prompts."""
        return {}

    def _update_prompts(self, prompts_dict: PromptDictType) -> None:
        """Update prompts."""

    async def aevaluate(
        self,
        query: str | None = None,
        response: str | None = None,
        contexts: Sequence[str] | None = None,
        sleep_time_in_seconds: int = 0,
        **kwargs: Any,
    ) -> EvaluationResult:
        """Evaluate whether the response is valid SQL."""
        del kwargs  # Unused
        await asyncio.sleep(sleep_time_in_seconds)

        if response is None:
            raise ValueError("response must be provided")

        try:
            parse_one(response, dialect=self._dialect)
            passing = True
            feedback = "Response is valid SQL."
        except Exception as e:
            passing = False
            feedback = f"Response is not valid SQL: {e}"
            if self._raise_error:
                raise ValueError(f"The response is invalid: {e}")

        return EvaluationResult(
            query=query,
            response=response,
            contexts=contexts,
            passing=passing,
            score=1.0 if passing else 0.0,
            feedback=feedback,
        )

