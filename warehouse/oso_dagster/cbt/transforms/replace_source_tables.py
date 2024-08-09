from ..utils import replace_source_tables
from ..context import wrap_basic_transform


def context_query_replace_source_tables(*args, **kwargs):
    return wrap_basic_transform(replace_source_tables(*args, **kwargs))
