#!/usr/bin/env python3
"""
Query script to count projects in the Optimism collection using OSO data.

This script demonstrates how to:
1. Use the pyoso client to connect to OSO's data lake
2. Generate a SQL query using natural language via the text2sql agent
3. Execute the query to count projects in the Optimism collection
4. Display the results

Requirements:
- OSO_API_KEY environment variable must be set
- pyoso package must be installed
"""

import os
import sys
from typing import Optional

import pandas as pd
import requests
from pyoso import Client


def query_text2sql_agent(nl_query: str, api_key: str) -> str:
    """
    Convert a natural language question into a SQL query using the OSO text2sql agent.
    
    This function mimics the MCP OSO server's query_text2sql_agent tool.
    
    Args:
        nl_query: The user's question in plain English
        api_key: OSO API key for authentication
    
    Returns:
        Generated SQL string
    
    Raises:
        requests.RequestException: If the API call fails
    """
    import uuid
    
    url = "https://www.opensource.observer/api/v1/text2sql"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    data = {
        "id": str(uuid.uuid4()),
        "messages": [{"role": "user", "content": nl_query}],
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()["sql"]
    except requests.RequestException as e:
        print(f"Error calling text2sql agent: {e}")
        raise


def main():
    """Main function to demonstrate querying Optimism collection projects."""
    
    # Step 0: Setup - Define the pyoso client with the OSO_API_KEY
    api_key = os.getenv("OSO_API_KEY")
    if not api_key:
        print("Error: OSO_API_KEY environment variable is required")
        print("Please set your OSO API key: export OSO_API_KEY='your_key_here'")
        print("Get your API key from: https://docs.opensource.observer/docs/get-started/python")
        sys.exit(1)
    
    # Initialize the pyoso client (never hard-code keys)
    client = Client(api_key)
    print("✓ Connected to OSO data lake")
    
    # Step 1: Generate SQL using the text2sql agent
    natural_language_query = "How many projects are in the optimism collection?"
    
    print(f"\n🔍 Converting natural language query to SQL...")
    print(f"Query: '{natural_language_query}'")
    
    try:
        # Call the text2sql agent (equivalent to MCP tool call)
        sql_query = query_text2sql_agent(natural_language_query, api_key)
        print(f"\n📝 Generated SQL query:")
        print(f"```sql\n{sql_query}\n```")
        
    except Exception as e:
        print(f"❌ Failed to generate SQL query: {e}")
        print("\n💡 Falling back to manually crafted SQL query...")
        
        # Fallback SQL query based on schema understanding
        sql_query = """
        SELECT COUNT(DISTINCT project_id) as project_count
        FROM projects_by_collection_v1 
        WHERE LOWER(collection_name) LIKE '%optimism%'
        """
        print(f"```sql\n{sql_query}\n```")
    
    # Step 2: Run the SQL query across the DB
    print(f"\n🚀 Executing query against OSO data lake...")
    
    try:
        # Pass the sql_query into the pyoso client with .to_pandas()
        df = client.to_pandas(sql_query)
        
        # Step 3: Display results
        print(f"\n📊 Results:")
        print("=" * 50)
        
        if not df.empty:
            if 'project_count' in df.columns:
                count = df['project_count'].iloc[0]
                print(f"Number of projects in Optimism collection: {count}")
            else:
                print("Query results:")
                print(df.to_string(index=False))
        else:
            print("No results found")
            
        print("=" * 50)
        
        # Optional: Show additional details if available
        if len(df.columns) > 1:
            print(f"\n📋 Additional details:")
            print(df.to_string(index=False))
            
    except Exception as e:
        print(f"❌ Error executing query: {e}")
        print("This might be due to:")
        print("- Invalid SQL syntax")
        print("- Missing permissions")
        print("- Network issues")
        print("- Schema changes in the OSO data lake")
        sys.exit(1)
    
    print(f"\n✅ Query completed successfully!")


if __name__ == "__main__":
    main()