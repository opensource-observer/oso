#!/usr/bin/env python3
"""
Simple SQL query to count projects in the Optimism collection.

This script demonstrates the core SQL query to answer:
"How many projects are in the optimism collection?"

Based on analysis of the OSO schema, specifically the projects_by_collection_v1 table.
"""

# The SQL query that answers the question:
# "How many projects are in the optimism collection?"

SQL_QUERY = """
SELECT COUNT(DISTINCT project_id) as project_count
FROM projects_by_collection_v1 
WHERE LOWER(collection_name) LIKE '%optimism%'
"""

# Alternative queries for more detailed analysis:

SQL_QUERY_DETAILED = """
SELECT 
    collection_name,
    COUNT(DISTINCT project_id) as project_count
FROM projects_by_collection_v1 
WHERE LOWER(collection_name) LIKE '%optimism%'
GROUP BY collection_name
ORDER BY project_count DESC
"""

SQL_QUERY_WITH_PROJECT_NAMES = """
SELECT 
    c.collection_name,
    p.project_name,
    p.display_name,
    p.description
FROM projects_by_collection_v1 c
JOIN projects_v1 p ON c.project_id = p.project_id
WHERE LOWER(c.collection_name) LIKE '%optimism%'
ORDER BY c.collection_name, p.project_name
"""

if __name__ == "__main__":
    print("SQL Query to count projects in Optimism collection:")
    print("=" * 60)
    print(SQL_QUERY)
    print("=" * 60)
    
    print("\nTo run this query using pyoso:")
    print("```python")
    print("from pyoso import Client")
    print("import os")
    print("")
    print("client = Client(os.getenv('OSO_API_KEY'))")
    print("df = client.to_pandas('''")
    print(SQL_QUERY.strip())
    print("''')")
    print("print(f'Projects in Optimism collection: {df.iloc[0].project_count}')")
    print("```")
    
    print("\nAlternative queries available:")
    print("- SQL_QUERY_DETAILED: Groups by collection name (in case there are multiple optimism collections)")
    print("- SQL_QUERY_WITH_PROJECT_NAMES: Shows individual project details")