from typing import List

from sqlglot.expressions import Expression
from sqlglot.optimizer.qualify import qualify

from .base import Transform


class QualifyTransform(Transform):
    def __init__(self, **options):
        self._options = options

    def __call__(self, query: List[Expression]) -> List[Expression]:
        return list(map(lambda q: qualify(q, **self._options), query))
