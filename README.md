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
- Multi-user support with web OAuth and JWT authentication
- Docker deployment with PostgreSQL backend

## Deployment

### MCP-Native OAuth Authentication (Recommended)

For MCP clients that support OAuth (like Claude Code), the server provides native OAuth 2.0 endpoints with dynamic client registration that conform to the MCP protocol specification.

**Quick Start:**

1. **Google Cloud Setup** - Create OAuth 2.0 credentials:

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project and enable Google Sheets API & Google Drive API
   - Go to APIs & Services → Credentials → Create OAuth 2.0 Client ID
   - Choose "Web application" (not Desktop)
   - Add authorized redirect URI: `http://localhost:8080/auth/callback` (or your production URL)
   - Download credentials and note the Client ID and Secret

2. **Setup Environment:**

```bash
git clone https://github.com/opera-gaming/mcp-gsheets.git
cd mcp-gsheets
cp .env.example .env
```

Edit `.env` and add your Google OAuth credentials:

```bash
# Database
DATABASE_URL=postgresql://mcpuser:mcppassword@localhost:5432/mcp_gsheets

# Google OAuth (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Server Configuration
BASE_URL=http://localhost:8080  # Change to your production URL for deployment
PORT=8080

# Generate secrets with these commands:
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

3. **Start Services:**

```bash
docker-compose up -d
```

4. **Configure MCP Client:**

Create or update `.mcp.json` in your project directory:

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

5. **Authenticate:**

   - Your MCP client will automatically discover OAuth support and initiate the authentication flow
   - When prompted, authorize access to Google Sheets in your browser
   - Authentication is handled seamlessly by the MCP client

**OAuth Endpoints:**

- `GET /.well-known/oauth-authorization-server` - OAuth server metadata discovery (RFC 8414)
- `GET /mcp/.well-known/openid-configuration` - OpenID Connect discovery
- `POST /mcp/oauth/register` - Dynamic client registration (RFC 7591)
- `GET /mcp/oauth/authorize` - Initiate OAuth authorization flow
- `POST /mcp/oauth/token` - Exchange authorization code for access token or refresh tokens
- `POST /mcp/oauth/revoke` - Revoke access tokens

**How it works:**

1. MCP client discovers OAuth support via well-known metadata endpoints
2. Client dynamically registers itself via `/mcp/oauth/register`
3. Client redirects user to `/mcp/oauth/authorize`
4. User completes Google OAuth consent flow
5. Server redirects back to client with authorization code
6. Client exchanges code for access token at `/mcp/oauth/token`
7. Client uses access token in `Authorization: Bearer <token>` header for all MCP requests

**Architecture:**

- **Web Service** (port 8080): OAuth flow, token generation, and MCP endpoint (`/mcp`)
- **PostgreSQL**: Encrypted credential storage (refresh tokens, access tokens)
- **FastMCP**: HTTP-based MCP server with JWT authentication middleware
- **Per-request authentication**: Each MCP call uses the user's stored Google credentials

### Alternative: Manual JWT Token Authentication

For MCP clients that don't support OAuth, you can obtain a JWT token manually via the web UI.

**Setup:**

1. Follow steps 1-3 from the OAuth setup above

2. **Authorize & Get Token:**

   - Open http://localhost:8080
   - Click "Sign in with Google"
   - Authorize access to Google Sheets
   - Copy your JWT token from the dashboard

3. **Configure MCP Client:**

Create or update `.mcp.json` in your project directory:

```json
{
  "mcpServers": {
    "mcp-gsheets": {
      "type": "http",
      "url": "http://localhost:8080/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_FROM_DASHBOARD"
      }
    }
  }
}
```

Replace `YOUR_TOKEN_FROM_DASHBOARD` with the JWT token shown on the dashboard after authentication.

**Note:** Both authentication methods (MCP-native OAuth and manual JWT) are supported and share the same backend infrastructure. Use OAuth if your MCP client supports it, otherwise fall back to manual token configuration.

## Available Tools (40+)

**Data Operations:** get_sheet_data, update_cells, batch_update_cells, append_values, clear_range, batch_clear_ranges, get_sheet_formulas

**Sheet Management:** list_sheets, create_sheet, rename_sheet, delete_sheet, copy_sheet

**Formatting:** format_cells, merge_cells, unmerge_cells, set_number_format

**Charts:** add_chart, delete_chart

**Validation:** add_data_validation, add_conditional_format_rule

**Operations:** sort_range, find_replace, add_rows, add_columns, delete_rows, delete_columns, auto_resize_dimensions

**Spreadsheet Management:** create_spreadsheet, list_spreadsheets, share_spreadsheet

## Troubleshooting

**Services won't start:**

- Check Docker is running: `docker ps`
- Check logs: `docker-compose logs app`
- Verify environment variables are set in `.env`

**"Authentication failed":**

- Ensure you've authorized via the web UI
- Check that your JWT token is correctly copied to `.mcp.json`
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct

**Tools not showing up:**

- Restart your MCP client (e.g., Claude Code)
- Verify your `.mcp.json` configuration
- Check server is running: `curl http://localhost:8080/health`

**Permission denied accessing spreadsheet:**

- The user must have access to the spreadsheet in Google Drive
- The user must authorize the application via OAuth flow

## Links

- [Google Sheets API](https://developers.google.com/sheets/api)
- [MCP Specification](https://modelcontextprotocol.io)
- [FastMCP](https://gofastmcp.com)

## License

MIT
