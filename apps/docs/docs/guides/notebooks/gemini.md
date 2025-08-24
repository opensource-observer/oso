# Gemini

Open Source Observer (OSO) provides comprehensive Web3 and crypto ecosystem
datasets through an AI-powered interface. This tutorial shows how to use Gemini
CLI with OSO's Model Context Protocol (MCP) server to generate data analysis
notebooks.

In this tutorial, we will walk through the process of setting up and using
Gemini with OSO in 5 minutes.

## What OSO Exposes to Gemini

OSO provides access to curated datasets covering:

- **20+ OP Stack chains** - Transaction data, gas usage, contract deployments
- **Developer activity** - GitHub repos, commits, dependencies for 1000+ crypto
  projects
- **DeFi protocols** - TVL, transaction volumes, user activity across chains
- **Funding flows** - Gitcoin grants, Optimism RetroPGF, other ecosystem funding
- **Social data** - Farcaster, Lens protocol activity and social graphs
- **Address labeling** - Bot detection, MEV identification, user categorization

Through our MCP server, Gemini can:

- Query these datasets with natural language
- Generate SQL automatically using our semantic layer
- Create Jupyter notebooks with data visualizations
- Provide full data provenance for reproducible analysis

## Example Use Cases

```
Analyze World Chain mini-app user retention rates over the first 30 days
```

```
Compare TVL growth across Arbitrum vs Optimism over the last 6 months
```

```
Show me the top 10 most active developers in the Ethereum ecosystem
```

## Installing Gemini CLI

Gemini CLI is Google's open-source command line interface that provides access
to Gemini directly in your terminal.

1. **Prerequisites**: You need Node.js version 18 or higher installed on your
   machine.

2. **Install Gemini CLI**:

```bash
npm install -g @google/gemini-cli
```

3. **Verify installation**:

```bash
gemini --version
```

4. **Launch Gemini CLI**:

```bash
gemini
```

## Authentication

When you first run Gemini CLI, it will prompt you to select a theme and then
authenticate.

1. **Interactive Authentication**: You'll be prompted to sign in via Google.
   Complete the OAuth flow in your browser to authenticate.

2. **Authentication Options**:

   - **Login with Google** (Recommended): Provides access to the free tier of
     Gemini CLI, which allows for 60 requests/minute, 1000 model requests per
     day
   - **API Key**: For higher rate limits, get your API key from
     [Google AI Studio](https://aistudio.google.com/app/apikey)
   - **Vertex AI**: For enterprise use with Google Cloud projects

3. **Using API Key** (if needed):

```bash
# Set environment variable
export GEMINI_API_KEY="your-api-key-here"

# Or create ~/.gemini/.env file with:
# GEMINI_API_KEY=your-api-key-here
```

4. **Switch Authentication**: You can use `/auth` in the Gemini CLI to switch
   the authentication method as needed.

## Setting Up OSO MCP Server

The OSO MCP server runs in Docker and uses STDIO transport, which means Gemini
CLI will automatically start and manage the Docker container when needed.

1. **Set your OSO API key as an environment variable**:

```bash
export OSO_API_KEY="your-oso-api-key-here"
```

Get your API key from [OSO Dashboard](https://www.opensource.observer/).

**Or create `~/.gemini/.env` file**:

```
OSO_API_KEY=your-oso-api-key-here
```

2. **Configure Gemini CLI**: Create or edit `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "oso": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "MCP_OSO_API_KEY=$OSO_API_KEY",
        "ghcr.io/opensource-observer/oso-mcp",
        "--verbose",
        "serve"
      ],
      "env": {
        "OSO_API_KEY": "$OSO_API_KEY"
      },
      "timeout": 60000,
      "trust": false
    }
  }
}
```

**Note**: Gemini CLI will automatically start the Docker container when you use
OSO tools and stop it when done.

## Testing the Connection

Verify everything is working by launching Gemini CLI and checking the MCP server
connection.

1. **Launch Gemini CLI**:

```bash
gemini
```

2. **Check MCP server status**:

```
/mcp
```

You should see the OSO server listed. Gemini CLI will automatically start the
Docker container when needed. Try this test prompt:

```
List the available OSO datasets and tell me what World Chain data you have access to
```

If successful, Gemini should respond with information about OSO's datasets
including World Chain user operation data.

## Generating Your First Notebook

Now you're ready to generate analysis notebooks! Try this example:

```
Analyze World Chain mini-app user retention rates over the first 30 days. Create a Jupyter notebook that:
1. Queries World Chain user operation data
2. Calculates daily, weekly, and monthly retention rates
3. Creates a retention curve visualization
4. Exports the notebook to Google Colab format
```

Gemini will:

- Generate the necessary SQL queries using OSO's semantic layer
- Create Python code for data analysis and visualization
- Package everything into a Jupyter notebook
- Provide data provenance information showing exactly which datasets were used

## Expected Output

You should receive:

- A complete `.ipynb` file ready to run in Google Colab
- Clear documentation of data sources and methodology
- Visualizations showing retention trends
- Instructions for uploading to Colab and running the analysis

## Troubleshooting

**MCP server not found:**

- Check the server status: `/mcp` inside Gemini CLI
- Verify Docker is installed and running: `docker --version`
- Ensure your OSO API key environment variable is set: `echo $OSO_API_KEY`
- Check that the Docker image can be pulled:
  `docker pull ghcr.io/opensource-observer/oso-mcp`

**OSO MCP server won't start:**

- Verify Docker is installed and running
- Check that your OSO API key is valid
- Ensure Docker has permission to run containers
- Try pulling the image manually first:
  `docker pull ghcr.io/opensource-observer/oso-mcp`

**Connection errors:**

- Verify Docker daemon is running: `docker ps`
- Check Docker logs if the container fails to start
- Ensure no firewall is blocking Docker operations

**Authentication errors:**

- Verify your OSO API key environment variable is set: `echo $OSO_API_KEY`
- Check you're logged into Gemini CLI: use `/auth` command
- Verify your API key is valid on the OSO Dashboard

**Data access issues:**

- Verify your OSO account has access to the requested datasets
- Some datasets may require additional permissions

**Installation issues:**

- Ensure npm global folder is in PATH
- Run `npm install -g @google/gemini-cli` to update if you get version issues

## Next Steps

Once you have a working notebook:

1. Upload it to Google Colab
2. Run the analysis to verify results
3. Try variations with different time periods or mini-apps
4. Explore other OSO datasets like DeFi protocols or developer activity
