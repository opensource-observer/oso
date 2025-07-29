#!/usr/bin/env python3
"""
Complete example demonstrating OSO MCP server usage for Optimism collection analysis.

This script shows the full workflow described in .github/instructions:
1. Define pyoso client with OSO_API_KEY
2. Use query_text2sql_agent (simulated MCP tool call)
3. Run SQL query via pyoso client
4. Analyze results
"""

import os
import sys
from typing import Optional

def simulate_mcp_query_text2sql_agent(natural_language_query: str) -> str:
    """
    Simulates the MCP OSO server's query_text2sql_agent tool.
    
    In a real implementation, this would be called as an MCP tool.
    For demonstration, we return the SQL query that would be generated.
    
    Args:
        natural_language_query: User's question in natural language
        
    Returns:
        SQL query string
    """
    print(f"🤖 MCP Tool Call: query_text2sql_agent('{natural_language_query}')")
    
    # This simulates what the text2sql agent would return
    # for the query "How many projects are in the optimism collection?"
    
    sql_query = """
SELECT COUNT(DISTINCT project_id) as project_count
FROM projects_by_collection_v1 
WHERE LOWER(collection_name) LIKE '%optimism%'
"""
    
    print("✓ Generated SQL query from text2sql agent")
    return sql_query.strip()


def main():
    """
    Main function following the exact workflow from .github/instructions:
    
    #### 0. One-time setup
    Always start by defined the pyoso client with the OSO_API_KEY
    
    #### 1. Generate SQL
    Call the `query_text2sql_agent()` MCP tool and pass in the user's natural language query
    
    #### 2. Run the SQL query across the DB
    Pass in the sql_query gathered above into the pyoso client
    
    #### 3. (Optional) Analysis
    Continue working with the final dataframe and run any additional analysis
    """
    
    # #### 0. One-time setup
    print("=== Step 0: One-time setup ===")
    
    # Always start by defined the pyoso client with the OSO_API_KEY
    from pyoso import Client
    import os
    
    api_key = os.getenv("OSO_API_KEY")
    if not api_key:
        print("❌ OSO_API_KEY environment variable is required")
        print("Please set: export OSO_API_KEY='your_key_here'")
        return 1
    
    client = Client(os.getenv("OSO_API_KEY"))   # never hard-code keys
    print("✓ pyoso client initialized with OSO_API_KEY")
    
    # #### 1. Generate SQL
    print("\n=== Step 1: Generate SQL ===")
    
    # Call the `query_text2sql_agent()` MCP tool and pass in the user's natural language query
    user_query = "How many projects are in the optimism collection?"
    print(f"Natural language query: '{user_query}'")
    
    # Don't ever call the MCP tool in python code, just use it yourself to gather the proper SQL query.
    # Only the end result SQL query should be written into the code.
    sql_query = simulate_mcp_query_text2sql_agent(user_query)
    
    print(f"Generated SQL:")
    print("```sql")
    print(sql_query)
    print("```")
    
    # #### 2. Run the SQL query across the DB
    print("\n=== Step 2: Run the SQL query across the DB ===")
    
    try:
        # Pass in the sql_query gathered above into the pyoso client defined above with .to_pandas(),
        # which should return a dataframe result of the query across pyoso's data lake.
        df = client.to_pandas(sql_query)
        print("✓ Query executed successfully")
        
        print("\nQuery Results:")
        print(df.to_string(index=False))
        
        # #### 3. (Optional) Analysis
        print("\n=== Step 3: (Optional) Analysis ===")
        
        # Now, based on the user's request, you are free to continue working with 
        # the final dataframe and run any additional analysis they might want done on it.
        
        if 'project_count' in df.columns:
            count = df['project_count'].iloc[0]
            print(f"\n📊 Analysis Results:")
            print(f"• Total projects in Optimism collection: {count:,}")
            
            # Additional analysis example
            if count > 0:
                print(f"• This represents a significant ecosystem of {count} projects")
                print(f"• Data source: OSO data lake via pyoso client")
            else:
                print("• No projects found - might need to check collection naming")
        
        # You could add more analysis here, such as:
        # - Trend analysis over time
        # - Comparison with other collections
        # - Project categorization
        # - Activity metrics
        
        print("\n✅ Complete workflow demonstration finished successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error executing query: {e}")
        print("\nThis could be due to:")
        print("- Network connectivity issues")
        print("- Invalid API key")
        print("- Schema changes in OSO data lake")
        print("- Permission restrictions")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)