import typing as t

if t.TYPE_CHECKING:
    from .definition import AttributePath


class InvalidAttributeReferenceError(Exception):
    """Exception raised when an invalid attribute reference is encountered."""

    def __init__(
        self,
        reference: "AttributePath",
        message: str = "intermediate attributes must be relationship",
        suggestions: list[str] | None = None,
    ):
        super().__init__(f"Invalid attribute reference `{reference}`: {message}")
        self.reference = reference
        self.suggestions = suggestions or []


class ModelHasNoJoinPathError(Exception):
    """Exception raised when no join path exists between two models."""

    def __init__(
        self,
        from_model: str,
        to_model: str,
        message: str | None = None,
        available_models: list[str] | None = None,
    ):
        self.from_model = from_model
        self.to_model = to_model
        self.available_models = available_models or []

        if not message:
            message = (
                f"No join path found between models '{from_model}' and '{to_model}'"
            )

        super().__init__(message)


class ModelHasAmbiguousJoinPathError(Exception):
    """Exception raised when multiple join paths exist between models."""

    def __init__(
        self,
        from_model: str,
        to_model: str,
        possible_paths: list[str] | None = None,
        message: str | None = None,
    ):
        self.from_model = from_model
        self.to_model = to_model
        self.possible_paths = possible_paths or []

        if not message:
            message = (
                f"Ambiguous join path between models '{from_model}' and '{to_model}'"
            )

        super().__init__(message)


class AttributeNotFoundError(Exception):
    """Exception raised when a referenced attribute does not exist in a model."""

    def __init__(
        self,
        model_name: str,
        attribute_name: str,
        available_attributes: dict[str, list[str]] | None = None,
    ):
        self.model_name = model_name
        self.attribute_name = attribute_name
        self.available_attributes = available_attributes or {}

        message = f"Attribute '{attribute_name}' not found in model '{model_name}'"
        super().__init__(message)


class SemanticQueryValidationError(Exception):
    """Exception raised when a semantic query fails validation."""

    def __init__(
        self,
        query: str,
        validation_errors: list[str],
        suggestions: list[str] | None = None,
    ):
        self.query = query
        self.validation_errors = validation_errors
        self.suggestions = suggestions or []

        message = f"Query validation failed: {'; '.join(validation_errors)}"
        super().__init__(message)
