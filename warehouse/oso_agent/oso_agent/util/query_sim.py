### most of this comes from the SPIDER test-suite: https://github.com/taoyds/test-suite-sql-eval/blob/master/exec_eval.py

import random
import typing as t
from collections import defaultdict
from itertools import product

from .jaccard import jaccard_similarity_multiset


def permute_tuple(element: t.Tuple, perm: t.Tuple) -> t.Tuple:
    assert len(element) == len(perm)
    return tuple([element[i] for i in perm])


def unorder_row(row: t.Tuple) -> t.Tuple:
    return tuple(sorted(row, key=lambda x: str(x) + str(type(x))))


def row_order_similarity(l1: t.List[t.Tuple], l2: t.List[t.Tuple]) -> float:
    n = min(len(l1), len(l2))
    if n == 0:
        return 1.0 if len(l1) == len(l2) else 0.0
    matches = sum(1 for a, b in zip(l1, l2) if a == b)
    return matches / max(len(l1), len(l2))


def score_rows(result1: t.List[t.Tuple], result2: t.List[t.Tuple], order_matters: bool) -> float:
    if order_matters:
        return row_order_similarity(result1, result2)
    else:
        return jaccard_similarity_multiset(result1, result2)


# unorder each row in the table
# [result_1 and result_2 has the same bag of unordered row]
# is a necessary condition of
# [result_1 and result_2 are equivalent in denotation]
def quick_rej_float(result1: t.List[t.Tuple], result2: t.List[t.Tuple], order_matters: bool) -> float:
    s1 = [unorder_row(row) for row in result1]
    s2 = [unorder_row(row) for row in result2]
    return score_rows(s1, s2, order_matters)

def quick_rej_bool(result1: t.List[t.Tuple], result2: t.List[t.Tuple], order_matters: bool) -> bool:
    s1 = [unorder_row(row) for row in result1]
    s2 = [unorder_row(row) for row in result2]
    if order_matters:
        return s1 == s2
    else:
        return set(s1) == set(s2)


# return whether two bag of relations are equivalent
def multiset_eq(l1: t.List, l2: t.List) -> bool:
    if len(l1) != len(l2):
        return False
    d = defaultdict(int)
    for e in l1:
        d[e] = d[e] + 1
    for e in l2:
        d[e] = d[e] - 1
        if d[e] < 0:
            return False
    return True


def get_constraint_permutation(tab1_sets_by_columns: t.List[t.Set], result2: t.List[t.Tuple]):
    num_cols = len(result2[0])
    perm_constraints = [{i for i in range(num_cols)} for _ in range(num_cols)]
    if num_cols <= 3:
        return product(*perm_constraints)

    # we sample 20 rows and constrain the space of permutations
    for _ in range(20):
        random_tab2_row = random.choice(result2)

        for tab1_col in range(num_cols):
            for tab2_col in set(perm_constraints[tab1_col]):
                if random_tab2_row[tab2_col] not in tab1_sets_by_columns[tab1_col]:
                    perm_constraints[tab1_col].remove(tab2_col)
    return product(*perm_constraints)


# I'm maintaining these as 2 seperate functions (bool & float) just for now so we can ensure that the fuzzy works
# as I'm more confident in the boolean function, but down the line these can easily become 1 function

# check whether two denotations are correct
def result_eq_bool(result1: t.List[t.Tuple], result2: t.List[t.Tuple], order_matters: bool) -> bool:
    if len(result1) == 0 and len(result2) == 0:
        return True

    # if length is not the same, then they are definitely different bag of rows
    if len(result1) != len(result2):
        return False

    num_cols = len(result1[0])

    # if the results do not have the same number of columns, they are different
    if len(result2[0]) != num_cols:
        return False

    # unorder each row and compare whether the denotation is the same
    # this can already find most pair of denotations that are different
    if not quick_rej_bool(result1, result2, order_matters):
        return False

    # the rest of the problem is in fact more complicated than one might think
    # we want to find a permutation of column order and a permutation of row order,
    # s.t. result_1 is the same as result_2
    # we return true if we can find such column & row permutations
    # and false if we cannot
    tab1_sets_by_columns = [{row[i] for row in result1} for i in range(num_cols)]

    # on a high level, we enumerate all possible column permutations that might make result_1 == result_2
    # we decrease the size of the column permutation space by the function get_constraint_permutation
    # if one of the permutation make result_1, result_2 equivalent, then they are equivalent
    for perm in get_constraint_permutation(tab1_sets_by_columns, result2):
        if len(perm) != len(set(perm)):
            continue
        if num_cols == 1:
            result2_perm = result2
        else:
            result2_perm = [permute_tuple(element, perm) for element in result2]
        if order_matters:
            if result1 == result2_perm:
                return True
        else:
            # in fact the first condition must hold if the second condition holds
            # but the first is way more efficient implementation-wise
            # and we use it to quickly reject impossible candidates
            if set(result1) == set(result2_perm) and multiset_eq(result1, result2_perm):
                return True
    return False


# check whether two denotations are correct
def result_eq_float(result1: t.List[t.Tuple], result2: t.List[t.Tuple], order_matters: bool) -> float:
    if len(result1) == 0 and len(result2) == 0:
        return 1
    
    if len(result1) == 0 or len(result2) == 0:
        return 0

    num_cols = len(result1[0])

    if len(result2[0]) != num_cols:
        return 0

    #quick_check = quick_rej_float(result1, result2, order_matters)
    #if quick_check < 1:
    #    return quick_check

    tab1_sets_by_columns = [{row[i] for row in result1} for i in range(num_cols)]

    best_score = 0
    for perm in get_constraint_permutation(tab1_sets_by_columns, result2):
        if best_score == 1:
            return best_score
        if len(perm) != len(set(perm)):
            continue
        if num_cols == 1:
            result2_perm = result2
        else:
            result2_perm = [permute_tuple(element, perm) for element in result2]
        best_score = max(best_score, score_rows(result1, result2_perm, order_matters))
    return best_score


def result_eq_float_w_metadata(result1: t.List[t.Tuple], result2: t.List[t.Tuple], order_matters: bool) -> t.Tuple[float, dict]:
    metadata = {}

    # empty checks
    if len(result1) == 0 and len(result2) == 0:
        return 1, {"note": "both empty"}
    if len(result1) == 0 or len(result2) == 0:
        metadata["missing_result"] = "result1 empty" if len(result1) == 0 else "result2 empty"
        metadata["result1_row_count"] = len(result1)
        metadata["result2_row_count"] = len(result2)
        return 0, metadata

    num_cols1 = len(result1[0])
    num_cols2 = len(result2[0])

    if num_cols1 != num_cols2:
        metadata["column_mismatch"] = {
            "result1_num_cols": num_cols1, 
            "result2_num_cols": num_cols2
        }
        return 0, metadata

    # initial rejection check
    quick_check = quick_rej_float(result1, result2, order_matters)
    if quick_check < 1:
        metadata["quick_reject"] = True
        set1 = set(result1)
        set2 = set(result2)
        missing_in_1 = set2 - set1
        missing_in_2 = set1 - set2
        if missing_in_1:
            metadata["rows_only_in_result2"] = len(missing_in_1)
        if missing_in_2:
            metadata["rows_only_in_result1"] = len(missing_in_2)
        metadata["result1_row_count"] = len(result1)
        metadata["result2_row_count"] = len(result2)
        metadata["score"] = quick_check
        return quick_check, metadata

    tab1_sets_by_columns = [{row[i] for row in result1} for i in range(num_cols1)]
    best_score = 0
    best_diff_counts = {}

    for perm in get_constraint_permutation(tab1_sets_by_columns, result2):
        if best_score == 1:
            break
        if len(perm) != len(set(perm)):
            continue
        result2_perm = result2 if num_cols1 == 1 else [permute_tuple(element, perm) for element in result2]
        score = score_rows(result1, result2_perm, order_matters)
        if score > best_score:
            best_score = score
            if score < 1:
                set1 = set(result1)
                set2 = set(result2_perm)
                diff_1 = set1 - set2
                diff_2 = set2 - set1
                # only store if there's any diff
                if diff_1:
                    best_diff_counts["rows_only_in_result1"] = len(diff_1)
                if diff_2:
                    best_diff_counts["rows_only_in_result2"] = len(diff_2)

    if best_score < 1 and best_diff_counts:
        metadata["differences"] = best_diff_counts

    metadata["result1_row_count"] = len(result1)
    metadata["result2_row_count"] = len(result2)
    metadata["score"] = best_score

    return best_score, metadata