"""Filter mutations based on configurable patterns."""

import re
import typing as t

from .types import MutationFilter as BaseMutationFilter
from .types import MutationInfo


class RegexMutationFilter(BaseMutationFilter):
    """Filter mutations based on regex patterns in their descriptions."""

    def __init__(self, patterns: t.List[str]):
        """Initialize the regex mutation filter.

        Args:
            patterns: List of regex patterns to match against mutation descriptions
        """
        self.patterns = patterns

    def should_ignore(self, mutation: MutationInfo) -> bool:
        """Check if mutation should be ignored.

        Args:
            mutation: Mutation information

        Returns:
            True if mutation should be ignored, False otherwise
        """
        if not self.patterns:
            return False

        # Check if any pattern matches the mutation description
        for pattern in self.patterns:
            if self._matches_pattern(mutation.description, pattern):
                return True

        return False

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Regex pattern matching.

        Args:
            text: Text to search in
            pattern: Regex pattern to match

        Returns:
            True if pattern matches, False otherwise
        """
        try:
            return bool(re.search(pattern, text, re.IGNORECASE))
        except re.error:
            # Invalid regex pattern, ignore it
            return False
