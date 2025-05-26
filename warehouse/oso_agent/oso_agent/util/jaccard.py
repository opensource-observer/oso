from difflib import SequenceMatcher

from pandas import DataFrame
from sklearn.metrics import jaccard_score


def similarity_str(output: str, expected: str) -> float:
    return SequenceMatcher(None, output.lower(), expected.lower()).ratio()

def jaccard_similarity_str(output: str, expected: str) -> float:
    # https://en.wikipedia.org/wiki/Jaccard_index
    actual_words = set(output.lower().split(" "))
    expected_words = set(expected.lower().split(" "))
    words_in_common = actual_words.intersection(expected_words)
    all_words = actual_words.union(expected_words)
    return len(words_in_common) / len(all_words)

def jaccard_similarity_pandas(output: DataFrame, expected: DataFrame):
    return jaccard_score(output, expected)