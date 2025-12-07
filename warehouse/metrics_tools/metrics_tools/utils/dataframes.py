import typing as t

import pandas as pd


def as_pandas_df(v: t.Any) -> pd.DataFrame:
    return t.cast(pd.DataFrame, v)
