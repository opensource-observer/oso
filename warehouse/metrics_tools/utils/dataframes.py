import pandas as pd
import typing as t


def as_pandas_df(v: t.Any) -> pd.DataFrame:
    return t.cast(pd.DataFrame, v)
