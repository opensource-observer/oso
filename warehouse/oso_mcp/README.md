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
- Convert natural-language questions into SQL
- Resolve project / collection / metric entities from user text
- Search the data lake for projects, collections, chains, metrics, models, and artifacts

OSO tracks metrics about open-source projects, including GitHub stats, funding
data, and on-chain activity.

## Installation

1. Install dependencies:

   ```bash
   uv sync --all-packages
   ```

2. Get an OSO API key from
   [Open Source Observer](https://www.opensource.observer). Follow the
   instructions in the [Getting OSO API Key](#getting-oso-api-key) section to
   obtain your key.

## Running the MCP server

```bash
uv run mcp serve
```

## Setting Up with Claude Desktop

1. Open Claude Desktop settings (**Claude → Settings**)

2. Choose **Developer**, click **Edit Config**

3. Insert:

   ```jsonc
   {
     "mcpServers": {
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

4. Replace the paths and API key

5. Restart Claude Desktop

---

## **Connecting the MCP Server to Cursor**

### 1 · Copy environment variables

Add the block below (from `.env.example`) to your local `.env`, then fill values:

```env
# MCP + Text2SQL Agent
AGENT_VECTOR_STORE__TYPE=local
AGENT_VECTOR_STORE__DIR=/path/to/your/vector/storage/directory

AGENT_LLM__TYPE=google_genai
AGENT_LLM__GOOGLE_API_KEY=your_google_genai_api_key_here

AGENT_OSO_API_KEY=your_oso_api_key_here
AGENT_ARIZE_PHOENIX_USE_CLOUD=0
```

### 2 · Configure Cursor

Create or edit `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "oso": {
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

### 3 · Start the server

```bash
uv run oso_mcp serve
```

### 4 · Enable inside Cursor

_Cursor → Settings → Tools & Integrations → MCP_
Toggle **oso** on (and any individual tools you care about).

> **Note:** If you add/remove tools later, **close and reopen Cursor**.
> Cursor only connects to each MCP at startup.

---

## Available Tools

| Tool                   | Purpose (one-liner)                              |
| ---------------------- | ------------------------------------------------ |
| `query_oso`            | Execute custom SQL against the OSO data lake     |
| `list_tables`          | List every table available                       |
| `get_table_schema`     | Show columns & types for a table                 |
| `get_sample_queries`   | Retrieve curated example queries                 |
| `query_text2sql_agent` | Convert plain English to SQL via OSO Text2SQL    |
| `generate_sql`         | Smarter NLQ → SQL (entity resolution + Text2SQL) |
| `gather_all_entities`  | Extract & resolve entities from a NLQ            |
| `search_project`       | Find matching rows in `projects_v1`              |
| `search_collection`    | Find matching rows in `collections_v1`           |
| `search_chain`         | Find matching rows in `int_chainlist`            |
| `search_metric`        | Find matching rows in `metrics_v0`               |
| `search_model`         | Find matching rows in `models_v1`                |
| `search_artifact`      | Find matching rows in `artifacts_v1`             |

Below are fuller details and examples.

### `query_oso`

Run any **SELECT** query.

```text
Parameters
- sql   (string, required)
- limit (integer, optional)
```

Example
`query_oso("SELECT * FROM collections_v1", ctx, limit=5)`

### `list_tables`

No parameters.

Example
`list_tables(ctx)`

### `get_table_schema`

```text
Parameters
- table_name (string, required)
```

Example
`get_table_schema("projects_v1", ctx)`

### `get_sample_queries`

Returns a JSON list of pre-built queries and explanations.

### `query_text2sql_agent`

Translate NLQ to SQL directly.

```text
Parameters
- natural_language_query (string, required)
```

### `generate_sql`

Uses **entity extraction** → **Text2SQL** for better accuracy.

```text
Parameters
- natural_language_query (string, required)
```

### `gather_all_entities`

Resolve all projects / collections / metrics etc. mentioned in an NLQ.

```text
Parameters
- nl_query (string, required)
```

---

### Entity-Search Helpers

All entity search tools support two modes:

| Arg          | Values                       | Default   |
| ------------ | ---------------------------- | --------- |
| `match_type` | `"exact"` \| `"fuzzy"`       | `"exact"` |
| `nl_query`   | original NLQ for LLM context | ""        |

Each returns matching rows from its table.

_Examples_

```text
search_project("Uniswap", ctx, match_type="fuzzy")
search_collection("ethereum-github", ctx)
search_metric("GITHUB_commits_daily", ctx)
```

---

## Resources

- **help\://getting-started** — in-app quick-start guide

## Example Usage

1. “Generate SQL to list the top 10 funded projects.” (`generate_sql`)
2. “What tables exist?” (`list_tables`)
3. “Show the schema for `metrics_v0`.” (`get_table_schema`)
4. “Find a project named Optimism.” (`search_project`)
5. “Convert ‘total gas fees per collection last month’ to SQL.” (`query_text2sql_agent`)

## Getting OSO API Key

1. Sign up at **[www.opensource.observer](http://www.opensource.observer)**
2. Visit **Settings → Profile → API**
3. Click **+ New**, label your key, **save** it
