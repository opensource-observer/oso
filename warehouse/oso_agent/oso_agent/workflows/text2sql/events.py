from typing import Optional

from llama_index.core.workflow.events import StartEvent


class Text2SQLStartEvent(StartEvent):
    """Start event for Text2SQL workflows."""

    input: str
    synthesize_response: bool = True
    execute_sql: bool = True
    id: Optional[str] = None
