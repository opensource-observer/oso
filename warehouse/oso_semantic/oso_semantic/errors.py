import typing as t

if t.TYPE_CHECKING:
    from .definition import AttributePath

class InvalidAttributeReferenceError(Exception):
    """Exception raised when an invalid attribute reference is encountered."""

    def __init__(self, reference: "AttributePath", message: str = "intermediate attributes must be relationship"):
        super().__init__(f"Invalid attribute reference `{reference}`: {message}")
        self.reference = reference