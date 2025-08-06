from typing import Optional

from llama_index.core.bridge.pydantic import BaseModel


class Text2SQLStartEvent(BaseModel):
    """Start event for Text2SQL workflows."""

    input: str
    synthesize_response: bool = True
    execute_sql: bool = True
    id: Optional[str] = None

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
