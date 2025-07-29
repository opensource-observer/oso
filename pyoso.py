"""
Mock pyoso module for demonstration purposes.
This simulates the pyoso Client functionality for testing.
"""

import pandas as pd
import os
from typing import Optional


class Client:
    """Mock pyoso Client for demonstration purposes."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the mock client."""
        if api_key is None:
            api_key = os.getenv("OSO_API_KEY")
        
        if not api_key:
            raise ValueError("OSO API key is required")
        
        self.api_key = api_key
        print(f"Mock pyoso Client initialized (API key: {api_key[:8]}...)")
    
    def to_pandas(self, sql_query: str) -> pd.DataFrame:
        """
        Mock implementation that returns sample data for demonstration.
        In a real implementation, this would execute the SQL against OSO's data lake.
        """
        print(f"Executing SQL query: {sql_query}")
        
        # For demonstration, return mock data based on the query
        if "optimism" in sql_query.lower() and "count" in sql_query.lower():
            # Mock result for optimism project count
            return pd.DataFrame({"project_count": [42]})
        elif "optimism" in sql_query.lower():
            # Mock result for detailed optimism data
            return pd.DataFrame({
                "collection_name": ["Optimism", "Optimism Governance"],
                "project_count": [35, 7]
            })
        else:
            # Generic mock result
            return pd.DataFrame({"result": ["Sample data"]})