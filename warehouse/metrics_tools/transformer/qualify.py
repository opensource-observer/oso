from typing import List
from metrics_tools.transformer.base import Transform
from sqlglot.optimizer.qualify import qualify
from sqlglot.expressions import Expression


class QualifyTransform(Transform):
    def __call__(self, query: List[Expression]) -> List[Expression]:
        return list(map(qualify, query))
