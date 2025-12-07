from oso_core.sql.macros.to_unix_timestamp import (
    str_to_unix_timestamp as imported_str_to_unix_timestamp,
)
from oso_core.sql.macros.to_unix_timestamp import (
    to_unix_timestamp as imported_to_unix_timestamp,
)
from sqlmesh import macro

macro(name="str_to_unix_timestamp")(imported_str_to_unix_timestamp)
macro(name="to_unix_timestamp")(imported_to_unix_timestamp)
