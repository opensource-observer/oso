# OSO-MCP Server

A Model Context Protocol (MCP) server for interacting with the Open Source
Observer (OSO) data lake.

> [!WARNING]
> This is a work in progress and is not yet ready for production use. Yet.

## Overview

This MCP server provides tools for exploring and analyzing the Open Source
Observer (OSO) data lake, allowing you to:

- Run SQL queries against the OSO data lake
- Explore available tables and their schemas
- Access sample queries to help you get started

OSO tracks metrics about open source projects, including GitHub stats, funding
data, and on-chain activity.

## Installation

1. Install dependencies:

```bash
uv venv && uv sync
```

2. Get an OSO API key from
   [Open Source Observer](https://www.opensource.observer). Follow the
   instructions in the [Getting OSO API Key](#getting-oso-api-key) section to
   obtain your key.

## Setting Up with Claude Desktop

1. Open Claude Desktop settings by clicking on the Claude menu and selecting
   "Settings"
2. Select "Developer" in the sidebar and click "Edit Config"
3. Add the following configuration to the `claude_desktop_config.json`:

```jsonc
{
  "mcpServers": {
    // other MCP servers...
    "oso-data-lake": {
      "command": "uv",
      "args": ["run", "/path/to/your/oso/warehouse/oso_mcp/main.py"],
      "env": {
        "OSO_API_KEY": "your_api_key_here",
        "VIRTUAL_ENV": "/path/to/your/oso/warehouse/oso_mcp/.venv",
      },
    },
  },
}
```

4. Replace `/path/to/your/oso_mcp/` with the actual path to your repository
5. Replace `your_api_key_here` with your OSO API key
6. Restart Claude Desktop

## Available Tools

### query_oso

Run SQL queries against the OSO data lake.

**Parameters:**

- `sql` (string): SQL query to execute (SELECT statements only)
- `limit` (integer, optional): Limit to apply to the query results

**Example:**

```
Can you run this SQL query against the OSO data lake: SELECT * FROM collections_v1 LIMIT 5
```

### list_tables

List all available tables in the OSO data lake.

**Example:**

```
What tables are available in the OSO data lake?
```

### get_table_schema

Get the schema for a specific table in the OSO data lake.

**Parameters:**

- `table_name` (string): Name of the table to get schema for

**Example:**

```
Show me the schema for the projects_v1 table
```

### get_sample_queries

Get a set of sample queries to help users get started with the OSO data lake.

**Example:**

```
Show me some sample queries for the OSO data lake
```

## Resources

- **help://getting-started**: Basic guide to using the OSO data lake explorer

## Example Usage

Here are some examples of how you might use this MCP server with Claude:

1. "Show me the available tables in the OSO data lake"
2. "What's the schema for the projects_v1 table?"
3. "Can you run a query to find the top 10 most funded open source projects?"
4. "Analyze the funding history of the Uniswap project"
5. "Show me all the projects in the ethereum-github collection"
6. "Do a deep dive on the contribution patterns for the ethereum project"

## Getting OSO API Key

1. Go to [www.opensource.observer](https://www.opensource.observer) and create
   an account
2. Go to [Account settings](https://www.opensource.observer/settings/profile)
3. In the "API" section, click "+ New"
4. Give your key a label and save the key when it's generated
