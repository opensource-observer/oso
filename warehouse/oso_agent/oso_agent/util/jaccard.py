from collections import Counter
from difflib import SequenceMatcher

from pandas import DataFrame
from sklearn.metrics import jaccard_score


def similarity_str(output: str, expected: str) -> float:
    return SequenceMatcher(None, output.lower(), expected.lower()).ratio()


def jaccard_similarity_set(output: set, expected: set) -> float:
    if not output and not expected:
        return 1.0

    intersection = output.intersection(expected)
    union = output.union(expected)
    return len(intersection) / len(union)


def jaccard_similarity_multiset(l1: list, l2: list) -> float:
    c1, c2 = Counter(l1), Counter(l2)
    all_keys = set(c1) | set(c2)
    intersection = sum(min(c1[k], c2[k]) for k in all_keys)
    union = sum(max(c1[k], c2[k]) for k in all_keys)
    if union == 0:
        return 1.0
    return intersection / union


def jaccard_similarity_str(output: str, expected: str) -> float:
    # https://en.wikipedia.org/wiki/Jaccard_index
    actual_words = set(output.lower().split(" "))
    expected_words = set(expected.lower().split(" "))
    words_in_common = actual_words.intersection(expected_words)
    all_words = actual_words.union(expected_words)
    return len(words_in_common) / len(all_words)


def jaccard_similarity_pandas(output: DataFrame, expected: DataFrame):
    return jaccard_score(output, expected)