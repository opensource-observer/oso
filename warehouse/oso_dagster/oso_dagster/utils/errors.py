class UnsupportedTableColumn(Exception):
    """
    This is thrown when we have a database column type that we don't support
    """

    pass


class MalformedUrl(Exception):
    """
    This is thrown when we have a malformed URL
    """

    pass


class AssertionError(Exception):
    """
    Fails an assertion
    """

    pass


class NullOrUndefinedValueError(Exception):
    """
    This is thrown when we have a null or undefined value
    """

    pass
