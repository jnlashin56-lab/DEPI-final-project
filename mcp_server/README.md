# Cultural Recommender MCP Server

This MCP server exposes safe project tools for the Egypt cultural recommender.

## Tools

- `dataset_summary`: counts rows in the CSV datasets.
- `database_status`: checks local Postgres table counts.
- `search_places_by_name`: searches English and Arabic place names.
- `sample_places`: returns sample places, optionally by category.

## Setup

From the project root:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

Make sure the database is running:

```powershell
docker compose up -d postgres
```

Test the MCP server directly:

```powershell
python -m mcp_server.server
```

The command will keep running because MCP uses stdio. Stop it with `Ctrl+C`.

## MCP Client Config

Use this command from an MCP client that supports stdio servers:

```json
{
  "mcpServers": {
    "cultural-recommender": {
      "command": "C:\\Users\\X1\\Downloads\\Depi_project\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "cwd": "C:\\Users\\X1\\Downloads\\Depi_project",
      "env": {
        "DATABASE_URL": "postgresql://cultural_user:cultural_password@localhost:5432/cultural_recommender"
      }
    }
  }
}
```

If your MCP client does not support `cwd`, use the absolute module runner from the project terminal instead.
