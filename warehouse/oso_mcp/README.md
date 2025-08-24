# OSO-MCP Server

A Model Context Protocol (MCP) server that connects your local IDE with the Open Source Observer's production text2sql agent.

## Overview

This MCP server allows you to connect your local IDE with our production text2sql agent, giving your IDE's AI assistant the ability to query and analyze data from the Open Source Observer (OSO) data lake using natural language. We have plans to add more connections to more agents down the line which will function similarly, and ultimately allow IDE LLMs to level up with our stack.

## Installation

### Prerequisites

1. **Clone the repository** (if you haven't already):

   ```bash
   git clone https://github.com/opensource-observer/oso.git
   cd oso
   ```

2. **Pull the latest changes** (if you already have the repo):

   ```bash
   git pull origin main
   ```

3. **Sync the latest packages**:

   ```bash
   uv sync --all-packages
   pnpm install
   ```

4. **Set up your environment**: Refer to the `.env.example` file in the `oso_mcp` folder, but here's essentially what you need (see the [Setting up your environment](#setting-up-your-environment) section below for details).


## Setting up your environment

You'll need to set up the following environment variables. You can create a `.env` file in the `warehouse/oso_mcp` directory:

- `MCP_OSO_API_KEY` (required) - Your OSO API key
- `MCP_HOST` (default: `127.0.0.1`) - The host to run the server on
- `MCP_PORT` (default: `8000`) - The port to run the server on
- `MCP_TRANSPORT` (default: `sse`) - Transport method (`sse` or `stdio`)
- `MCP_TEXT2SQL_ENDPOINT` (default: `https://www.opensource.observer/api/v1/text2sql`) - The OSO text2sql service endpoint
  - For local development: `http://localhost:8080/api/v1/text2sql`
  - For staging: `https://staging.opensource.observer/api/v1/text2sql`
### Getting your OSO API key

Navigate to [https://docs.opensource.observer/docs/get-started/python](https://docs.opensource.observer/docs/get-started/python) and follow the steps in the "Generate an API key" section.

## Running the server

To run the MCP server:

```bash
uv run oso_mcp serve
```

### Additional options

- **For help**: `uv run oso_mcp -h`
- **Verbose output**: `uv run oso_mcp -v serve` (use `-v` for info, `-vv` for debug)
  - None = only warnings
  - One `-v` = info level
  - Two `-vv` = debug info
- **View environment schema**: `uv run oso_mcp env-schema`

For any other help with the CLI, add the `-h` flag after any command to see details and steps.

## Connecting to your IDE

We currently support:

- Cursor
- VS Code with Copilot.

We're constantly updating things, but if you don't see your IDE supported, don't worry! It should be pretty easy to set things up - find their documentation on MCP servers and follow their steps (usually involves some sort of `mcp.json` in a proprietary folder). If you manage to figure it out, please open a PR and add it here!

### Cursor

1. **Create MCP configuration**: Make sure in the `.cursor` folder at your project root you have a `mcp.json` with the following format:

   ```json
   {
     "mcpServers": {
       "oso": {
         "url": "http://127.0.0.1:8000/sse"
       }
     }
   }
   ```

2. **Important**: Make sure you're in your project root when you do this or it won't work.

3. **Start the server**: Follow all the above steps to run the server.

4. **Enable in Cursor**: Once the server is running:
   - Navigate to Settings (top right) → Tools & Integrations → MCP
   - If you don't see the MCP server under "MCP tools" as an option (should say "oso"), there might be a problem with connecting your `mcp.json` to Cursor
   - To solve this: click "+ New MCP server", then paste the above `mcp.json` contents into the file
   - You should then see "oso" show the number of tools available
   - Click on it to select which tools you want Cursor to have access to

#### Troubleshooting Cursor

- **Yellow dot ("loading tools")**: Toggle the server on and off and it should update
- **Red dot**: There's a problem with your server - make sure it shows in the terminal as active and running. You should see:

  ```
  INFO:     Started server process [26321]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
  ```

- **Important note**: Cursor only connects to MCP servers once at app start. If you make changes and want to see them reflected, simply restarting the server won't work - you'll need to close and reopen Cursor, then rerun the server.

#### Using with Cursor

Now you should be good to go with Cursor! When you talk to Cursor, it will have the option to use the tools you selected.

**Note**: We have a `@working-with-pyoso-data.mdc` Cursor rule that briefly explains to Cursor how to work with our text2sql tool. This is set to 'always' be included by default, but for best results (since it doesn't always work automatically), it's best to specifically add it to your queries by writing `@` and then `working-with-pyoso-data.mdc`.

### VS Code + Copilot

1. **Create MCP configuration**: Put a `mcp.json` file in the `.vscode` folder (note the different format):

   ```json
   {
     "servers": {
       "oso": {
         "url": "http://127.0.0.1:8000/sse"
       }
     }
   }
   ```

2. **Set up settings.json** (optional but recommended): Open VS Code settings (Cmd + Shift + P → "Open User Settings (JSON)"). This is only necessary if you want Copilot to use the Cursor rules files for context.

   In this `settings.json`, paste the files you want it to use as context:

   ```json
   {
     "chat.instructionsFilesLocations": {
       ".cursor/rules/working-with-pyoso-data.mdc": true
     }
   }
   ```

   We have an example in `.vscode/settings.json`.

3. **Start the server**: Follow the above steps to run the server.

4. **Use in VS Code**: When you go to chat with Copilot:
   - Click "Add context" above the user input
   - In the dropdown, click "MCP resources"
   - If your server successfully connected, you should see it appear as an option
   - You can manually select this into the chat (this also indicates Copilot should see it and use it at its own discretion)

Now you're good to work with Copilot!
