import logging
from typing import List

from llama_index.core.tools import FunctionTool

logger = logging.getLogger(__name__)

def multiply(a: float, b: float) -> float:
    """Multiplies two numbers together."""
    logger.debug(f"Multiplying {a} and {b}")
    return a * b

def create_multiply_tool() -> List[FunctionTool]:
    return [ FunctionTool.from_defaults(multiply) ]