# OSO Agents

A multi-agent framework that can answer questions from the OSO data lake.

> [!WARNING]
> This is a work in progress and is not yet ready for production use yet.

## Installation

Install dependencies:

```bash
uv venv && uv sync
```

Get an OSO API key from
[Open Source Observer](https://www.opensource.observer). Follow the
instructions in the [Getting OSO API Key](#getting-oso-api-key) section to
obtain your key.

## Run the agent

First run the MCP server in a separate terminal:

```bash
cd warehouse/oso_mcp/
OSO_API_KEY=YOUR_API_KEY uv run main.py
```

Then run the agent:

```bash
cd warehouse/oso_agent/
uv run main.py
```
