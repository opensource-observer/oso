# OSO Optimism Collection Query Solution

This solution demonstrates how to query the number of projects in the Optimism collection using the OSO (Open Source Observer) data lake and tools provided in the MCP OSO server.

## Overview

The solution provides multiple approaches to answer the question: **"How many projects are in the optimism collection?"**

## Files Created

### 1. `complete_oso_workflow_example.py`
**Main demonstration script** - Shows the complete workflow as described in `.github/instructions`:
- ✅ Define pyoso client with OSO_API_KEY
- ✅ Use query_text2sql_agent (MCP tool simulation)
- ✅ Run SQL query via pyoso client  
- ✅ Analyze results

### 2. `query_optimism_projects.py`
**Full-featured script** with error handling and fallback:
- Attempts to use the real OSO text2sql API
- Falls back to manually crafted SQL on API failure
- Includes comprehensive error handling and user feedback

### 3. `optimism_collection_sql.py`
**Simple SQL reference** - Contains the core SQL queries:
- Basic count query
- Detailed analysis queries
- Usage examples

### 4. `pyoso.py`
**Mock module** for testing and demonstration purposes when real API is not available.

## Core SQL Query

The main SQL query that answers the question is:

```sql
SELECT COUNT(DISTINCT project_id) as project_count
FROM projects_by_collection_v1 
WHERE LOWER(collection_name) LIKE '%optimism%'
```

## Usage

### Prerequisites

1. **OSO API Key**: Get your API key from [OSO Documentation](https://docs.opensource.observer/docs/get-started/python)
2. **Dependencies**: Install required packages:
   ```bash
   pip install pyoso pandas requests
   ```

### Running the Examples

1. **Set your API key**:
   ```bash
   export OSO_API_KEY="your_api_key_here"
   ```

2. **Run the complete workflow demonstration**:
   ```bash
   python complete_oso_workflow_example.py
   ```

3. **Run the full-featured query script**:
   ```bash
   python query_optimism_projects.py
   ```

4. **View the SQL queries only**:
   ```bash
   python optimism_collection_sql.py
   ```

## Expected Output

```
=== Step 0: One-time setup ===
✓ pyoso client initialized with OSO_API_KEY

=== Step 1: Generate SQL ===
Natural language query: 'How many projects are in the optimism collection?'
🤖 MCP Tool Call: query_text2sql_agent('How many projects are in the optimism collection?')
✓ Generated SQL query from text2sql agent

=== Step 2: Run the SQL query across the DB ===
✓ Query executed successfully

📊 Analysis Results:
• Total projects in Optimism collection: [COUNT]
• Data source: OSO data lake via pyoso client
```

## Architecture

The solution follows the pattern described in `.github/instructions`:

1. **Setup**: Initialize pyoso client with OSO_API_KEY (never hard-coded)
2. **SQL Generation**: Use `query_text2sql_agent()` MCP tool to convert natural language to SQL
3. **Execution**: Pass generated SQL to `client.to_pandas()` for execution against OSO data lake
4. **Analysis**: Process the resulting DataFrame for insights

## Schema Understanding

Based on analysis of the OSO codebase, the solution uses:

- **Table**: `projects_by_collection_v1` - Links projects to collections
- **Key Fields**: 
  - `project_id` - Unique identifier for projects
  - `collection_name` - Name of the collection (e.g., "Optimism")
- **Pattern**: Uses `LOWER()` and `LIKE '%optimism%'` for flexible matching

## Error Handling

The scripts include robust error handling for:
- Missing API keys
- Network connectivity issues
- API authentication failures
- Schema changes
- Invalid SQL syntax

## Alternative Queries

The solution also provides queries for additional analysis:

1. **Detailed breakdown by collection**:
   ```sql
   SELECT collection_name, COUNT(DISTINCT project_id) as project_count
   FROM projects_by_collection_v1 
   WHERE LOWER(collection_name) LIKE '%optimism%'
   GROUP BY collection_name
   ```

2. **Individual project details**:
   ```sql
   SELECT c.collection_name, p.project_name, p.display_name
   FROM projects_by_collection_v1 c
   JOIN projects_v1 p ON c.project_id = p.project_id
   WHERE LOWER(c.collection_name) LIKE '%optimism%'
   ```

## Testing

The solution includes a mock `pyoso` module for testing when the real OSO API is not available. This allows for:
- Development and testing without API keys
- Demonstration of the workflow
- Validation of script logic

## Integration with MCP OSO Server

While these scripts can run standalone, they demonstrate the patterns used in the MCP OSO server:

- **Text2SQL Agent**: Converts natural language to SQL queries
- **Data Lake Access**: Executes SQL against OSO's production data
- **Result Processing**: Returns structured data for analysis

## Next Steps

To integrate with the actual MCP OSO server:

1. Run the MCP server: `uv run oso_mcp serve`
2. Connect your IDE (Cursor/VS Code) to the MCP server
3. Use the `query_text2sql_agent` tool directly from your IDE
4. Execute the generated SQL using the `pyoso` client

This solution provides the foundation for answering questions about OSO data using both direct SQL queries and the natural language text2sql capabilities.