# mcp-gsheets

A comprehensive MCP server for Google Sheets API v4 with full formatting, charts, validation, and automation support.

## Features

- Full CRUD operations (read, write, update, append, clear)
- Charts and visualizations (bar, column, line, pie, scatter, area)
- Cell formatting (colors, fonts, bold, italic, alignment)
- Conditional formatting and data validation
- Merge/unmerge cells, find/replace with regex
- Row/column operations, sheet management
- 40+ tools covering the complete Google Sheets API
- Native MCP OAuth authentication using FastMCP OAuthProxy
- Simple single-container Docker deployment

## Deployment

The server uses FastMCP's native OAuth proxy to provide transparent Google OAuth authentication for MCP clients.

**1. Google Cloud Setup**

Create OAuth 2.0 credentials:

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project and enable Google Sheets API & Google Drive API
- Go to APIs & Services → Credentials → Create OAuth 2.0 Client ID
- Choose "Web application" (not Desktop)
- Add authorized redirect URI: `http://localhost:8080/auth/callback` (or your production URL)
- Download credentials and note the Client ID and Secret

**2. Setup Environment**

```bash
git clone https://github.com/opera-gaming/mcp-gsheets.git
cd mcp-gsheets
cp .env.example .env
```

Edit `.env` and add your Google OAuth credentials:

```bash
# Google OAuth (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Server Configuration
BASE_URL=http://localhost:8080  # Change to your production URL for deployment
PORT=8080
```

**3. Start Server**

```bash
docker-compose up -d
```

**4. Configure MCP Client**

Add to your MCP client configuration (e.g., Claude Desktop's `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mcp-gsheets": {
      "type": "http",
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

**5. Authenticate**

- Your MCP client will automatically discover OAuth support
- When prompted, authorize access to Google Sheets in your browser
- Authentication is handled seamlessly through the OAuth flow

**How it works:**

1. MCP client discovers OAuth support via `/.well-known/oauth-authorization-server`
2. Client dynamically registers itself and initiates authorization flow
3. Server proxies to Google OAuth using your configured credentials
4. User completes Google consent flow in browser
5. Server exchanges authorization code for Google access token
6. Client receives access token and uses it for all subsequent MCP requests
7. FastMCP validates tokens using Google's tokeninfo endpoint

**Architecture:**

- **FastMCP OAuthProxy**: Transparent OAuth proxy to Google
- **Single Container**: No database required
- **Token Validation**: Google tokeninfo endpoint validates access tokens
- **Per-request Authentication**: Each MCP call uses the authenticated user's Google credentials

## Available Tools (40+)

**Data Operations:** get_sheet_data, update_cells, batch_update_cells, append_values, clear_range, batch_clear_ranges, get_sheet_formulas

**Sheet Management:** list_sheets, create_sheet, rename_sheet, delete_sheet, copy_sheet

**Formatting:** format_cells, merge_cells, unmerge_cells, set_number_format

**Charts:** add_chart, delete_chart

**Validation:** add_data_validation, add_conditional_format_rule

**Operations:** sort_range, find_replace, add_rows, add_columns, delete_rows, delete_columns, auto_resize_dimensions

**Spreadsheet Management:** create_spreadsheet, list_spreadsheets, share_spreadsheet

## Troubleshooting

**Server won't start:**

- Check Docker is running: `docker ps`
- Check logs: `docker-compose logs -f`
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in `.env`
- Ensure `BASE_URL` matches your redirect URI in Google Cloud Console

**"Authentication failed" or "No valid session":**

- Clear authentication in your MCP client and re-authenticate
- Verify your Google OAuth redirect URI matches `{BASE_URL}/auth/callback`
- Check that Google Sheets API and Google Drive API are enabled in your GCP project
- Ensure the OAuth consent screen is configured in Google Cloud Console

**Tools not showing up:**

- Restart your MCP client
- Verify the server URL in your MCP client configuration
- Check server is running: `curl http://localhost:8080/.well-known/oauth-authorization-server`

**Permission denied accessing spreadsheet:**

- The authenticated Google account must have access to the spreadsheet
- Ensure you've completed the OAuth authorization flow
- Check that the required scopes (spreadsheets, drive.file) were granted

## Links

- [Google Sheets API](https://developers.google.com/sheets/api)
- [MCP Specification](https://modelcontextprotocol.io)
- [FastMCP](https://gofastmcp.com)

## License

MIT
