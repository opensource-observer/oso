"""
Copyright 2024 Tobiko Data Inc

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.

Notice:

Originally derived from sqlmesh.utils.pandas in the sqlmesh project
"""

from __future__ import annotations

import typing as t
from functools import lru_cache

from sqlglot import exp

if t.TYPE_CHECKING:
    import pandas as pd


@lru_cache()
def get_pandas_type_mappings() -> t.Dict[t.Any, exp.DataType]:
    import numpy as np
    import pandas as pd

    mappings = {
        np.dtype("int8"): exp.DataType.build("tinyint"),
        np.dtype("int16"): exp.DataType.build("smallint"),
        np.dtype("int32"): exp.DataType.build("int"),
        np.dtype("int64"): exp.DataType.build("bigint"),
        np.dtype("float16"): exp.DataType.build("float"),
        np.dtype("float32"): exp.DataType.build("float"),
        np.dtype("float64"): exp.DataType.build("double"),
        np.dtype("O"): exp.DataType.build("text"),
        np.dtype("bool"): exp.DataType.build("boolean"),
        np.dtype("datetime64"): exp.DataType.build("timestamp"),
        np.dtype("datetime64[ns]"): exp.DataType.build("timestamp"),
        np.dtype("datetime64[us]"): exp.DataType.build("timestamp"),
        pd.Int8Dtype(): exp.DataType.build("tinyint"),
        pd.Int16Dtype(): exp.DataType.build("smallint"),
        pd.Int32Dtype(): exp.DataType.build("int"),
        pd.Int64Dtype(): exp.DataType.build("bigint"),
        pd.Float32Dtype(): exp.DataType.build("float"),
        pd.Float64Dtype(): exp.DataType.build("double"),
        pd.StringDtype(): exp.DataType.build("text"),  # type: ignore
        pd.BooleanDtype(): exp.DataType.build("boolean"),
    }
    try:
        import pyarrow  # type: ignore  # noqa

        # Only add this if pyarrow is installed
        mappings[pd.StringDtype("pyarrow")] = exp.DataType.build("text")
    except ImportError:
        pass

    return mappings


def columns_to_types_from_df(df: pd.DataFrame) -> t.Dict[str, exp.DataType]:
    return columns_to_types_from_dtypes(df.dtypes.items())


def columns_to_types_from_dtypes(
    dtypes: t.Iterable[t.Tuple[t.Hashable, t.Any]],
) -> t.Dict[str, exp.DataType]:
    import pandas as pd

    result = {}
    for column_name, column_type in dtypes:
        exp_type: t.Optional[exp.DataType] = None
        if hasattr(pd, "DatetimeTZDtype") and isinstance(
            column_type, pd.DatetimeTZDtype
        ):
            exp_type = exp.DataType.build("timestamptz")
        else:
            exp_type = get_pandas_type_mappings().get(column_type)
        if not exp_type:
            raise ValueError(f"Unsupported pandas type '{column_type}'")
        result[str(column_name)] = exp_type
    return result
