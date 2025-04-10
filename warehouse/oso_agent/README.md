# OSO Agents

A multi-agent framework that can answer questions from the OSO data lake.

> [!WARNING]
> This is a work in progress and is not yet ready for production use yet.

## Installation

Install dependencies from the root

```bash
uv sync --all-packages
```

Get an OSO API key from
[Open Source Observer](https://www.opensource.observer). Follow the
instructions in the [Getting OSO API Key](#getting-oso-api-key) section to
obtain your key.

Add this to the `.env` file in `warehouse/oso_mcp/`

## Run the agent

First run the MCP server in a separate terminal:

```bash
uv run warehouse/oso_mcp/main.py
```

For now, in another separate terminal run arize phoenix in a docker container (this command is intentionally ephemeral):

```bash
docker run -it --rm -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest
```

Then run the agent:

```bash
uv run warehouse/oso_agent/main.py
```
