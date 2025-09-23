import typing as t

from llama_index.core.workflow import StartEvent


class GenericStartEvent(StartEvent):
    """Start event for generic workflows."""

    input: str
    id: t.Optional[str] = None

    @classmethod
    def create_from_kwargs(cls, **kwargs: t.Any) -> t.Self:
        """Create a GenericStartEvent from keyword arguments based on the
        annotations on the class

        You can have extra kwargs but they are ignored. Missing arguments will
        cause errors on the event's pydantic validation
        """

        fields = cls.model_fields
        input_kwargs = {k: v for k, v in kwargs.items() if k in fields}

        return cls(**input_kwargs)

    def __setattr__(self, name: str, value) -> None:
        """Prevent setting invalid attributes."""
        if (
            hasattr(self, "__pydantic_fields__")
            and name not in self.__pydantic_fields__
            and not name.startswith("_")
        ):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )
        super().__setattr__(name, value)
