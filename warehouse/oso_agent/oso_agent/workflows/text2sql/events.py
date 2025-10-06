from typing import Optional

from oso_agent.workflows.common import GenericStartEvent


class Text2SQLStartEvent(GenericStartEvent):
    """Start event for Text2SQL workflows."""

    input: str
    synthesize_response: bool = True
    execute_sql: bool = True
    id: Optional[str] = None
