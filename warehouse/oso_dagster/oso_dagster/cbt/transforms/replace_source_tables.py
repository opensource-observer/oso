from ..context import wrap_basic_transform
from ..utils import replace_source_tables


def context_query_replace_source_tables(*args, **kwargs):
    return wrap_basic_transform(replace_source_tables(*args, **kwargs))
