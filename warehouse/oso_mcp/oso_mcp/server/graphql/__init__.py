"""GraphQL tool generation for FastMCP.

This package provides utilities to automatically generate FastMCP tools from GraphQL schemas.
"""

from .generator import generate_from_schema

__all__ = ["generate_from_schema"]
