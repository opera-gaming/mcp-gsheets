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
- **NEW:** Multi-user support with web OAuth and JWT authentication
- **NEW:** Docker deployment with PostgreSQL backend

## Deployment Options

### Option 1: Multi-User Hosted MCP Server (Current Implementation)

Run as a hosted MCP server with web-based OAuth authentication. Users authorize once via web UI and receive a JWT token to use with their MCP clients.

**Quick Start:**

1. **Google Cloud Setup** - Create OAuth 2.0 credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project and enable Google Sheets API & Google Drive API
   - Go to APIs & Services → Credentials → Create OAuth 2.0 Client ID
   - Choose "Web application" (not Desktop)
   - Add authorized redirect URI: `http://localhost:8080/auth/callback`
   - Download credentials and note the Client ID and Secret

2. **Setup Environment:**
```bash
git clone https://github.com/opera-emoller/mcp-gsheets.git
cd mcp-gsheets
cp .env.example .env
```

Edit `.env` and add your Google OAuth credentials:
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
BASE_URL=http://localhost:8080

# Generate secrets:
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

3. **Start Services:**
```bash
docker-compose up -d
```

4. **Authorize & Get Token:**
   - Open http://localhost:8080
   - Click "Sign in with Google"
   - Authorize access to Google Sheets
   - Copy your JWT token from the dashboard

5. **Configure MCP Client:**

Create or update `.mcp.json` in your project:
```json
{
  "mcpServers": {
    "mcp-gsheets": {
      "type": "http",
      "url": "http://localhost:8080/mcp/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_JWT_TOKEN_HERE"
      }
    }
  }
}
```

**Architecture:**
- Web Service (port 8080): OAuth flow, JWT token generation, and MCP endpoint
- PostgreSQL: Encrypted credential storage (refresh tokens, access tokens)
- FastMCP: HTTP-based MCP server with JWT authentication middleware
- Per-request authentication: Each MCP call uses the user's stored Google credentials

### Option 2: Single-User Local OAuth (Quick Start)

### 1. Google Cloud Setup (OAuth - Recommended)

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project

2. **Enable APIs**
   - Enable Google Sheets API
   - Enable Google Drive API

3. **Configure OAuth 2.0**
   - Go to APIs & Services → OAuth consent screen
   - Choose "External" user type
   - Fill in the required fields (app name, user support email, developer email)
   - Add scopes: `https://www.googleapis.com/auth/spreadsheets` and `https://www.googleapis.com/auth/drive.file`
   - Add your email as a test user
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app" as application type
   - Name it (e.g., "mcp-gsheets-oauth")
   - Download the JSON file and save it as `credentials.json`

**Why OAuth?** Runs under your own Google account with automatic access to all your spreadsheets. No need to share files individually. **Required for creating new spreadsheets** (service accounts have no Drive quota).

<details>
<summary><b>Alternative: Service Account Setup</b> (for automation/CI/CD only)</summary>

Only follow these steps if you need service account authentication instead of OAuth:

1. Go to IAM & Admin → Service Accounts
2. Click "Create Service Account"
3. Name it (e.g., "mcp-gsheets")
4. Click "Create and Continue", then "Done"
5. Click on the service account → Keys tab
6. Add Key → Create new key → JSON
7. Save the JSON file securely
8. Share each spreadsheet with the service account email (found in JSON as `client_email`)

**Limitations:** Cannot create new spreadsheets. Must share each file manually.
</details>

### 2. Install with Claude Code

**Using OAuth (Recommended):**

```bash
claude mcp add --transport stdio sheets \
  --env CREDENTIALS_PATH=/path/to/credentials.json \
  --env TOKEN_PATH=/path/to/token.json \
  --env DRIVE_FOLDER_ID=your_optional_folder_id \
  --scope user \
  -- uvx mcp-gsheets
```

On first run, the server will open a browser window for you to authorize access. After authorization, a `token.json` file will be created and the token will refresh automatically.

**Using Service Account (Alternative):**

```bash
claude mcp add --transport stdio sheets \
  --env SERVICE_ACCOUNT_PATH=/path/to/service-account.json \
  --env DRIVE_FOLDER_ID=your_optional_folder_id \
  --scope user \
  -- uvx mcp-gsheets
```

With a service account, you'll need to share each spreadsheet with the service account email (found in the JSON file as `client_email`). **Note:** Service accounts cannot create new spreadsheets due to Drive quota limitations - use OAuth if you need to create files.

**Notes:**
- The `DRIVE_FOLDER_ID` is optional. If provided, the server will only list spreadsheets in that folder.
- To get your folder ID: Open the folder in Google Drive and copy the ID from the URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`

### 3. Verify Installation

Restart Claude Code and try:
- "List my Google Spreadsheets"
- "Create a new spreadsheet called 'Test'"
- "Format cells A1:C1 to be bold with a blue background"

## Development Setup

### Install UV and Build Locally

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <your-repo-url>
cd mcp-gsheets

# Build the package
uv build
```

### Run Locally for Development

To run the MCP server locally and connect it to Claude Code:

```bash
claude mcp add --transport stdio sheets \
  --env SERVICE_ACCOUNT_PATH=/path/to/your/service-account.json \
  --env DRIVE_FOLDER_ID=your_optional_folder_id \
  --scope user \
  -- uvx --from . mcp-gsheets
```

**Note:** The `--from .` tells uvx to use your local development version.

### Development Workflow

If you're actively developing and testing:

1. Make your code changes
2. Clean the UV cache: `uv clean --force`
3. Rebuild: `uv build`
4. Reload the MCP in Claude Code: `/mcp` command or restart Claude Code
5. Test your changes

**Important:** When testing changes in Claude Code, you MUST run `uv clean --force` and rebuild before reloading the MCP server, otherwise Claude will use the cached version.

## Available Tools (40+)

**Data Operations:** get_sheet_data, update_cells, batch_update_cells, append_values, clear_range, get_sheet_formulas

**Sheet Management:** list_sheets, create_sheet, rename_sheet, delete_sheet, copy_sheet

**Formatting:** format_cells, merge_cells, unmerge_cells, set_number_format

**Charts:** add_chart, delete_chart

**Validation:** add_data_validation, add_conditional_format_rule

**Operations:** sort_range, find_replace, add_rows, add_columns, delete_rows, delete_columns, auto_resize_dimensions

**Spreadsheet Management:** create_spreadsheet, list_spreadsheets, share_spreadsheet

## Authentication Methods

The server supports multiple authentication methods, checked in this order:

### 1. OAuth 2.0 Flow (Recommended)
```bash
export CREDENTIALS_PATH="/path/to/credentials.json"
export TOKEN_PATH="/path/to/token.json"
export DRIVE_FOLDER_ID="optional_folder_id"
```

Best for personal use. Runs under your Google account with automatic access to all your spreadsheets. On first run, opens a browser for authorization and saves a refresh token. **Required for creating new spreadsheets.**

### 2. Service Account
```bash
export SERVICE_ACCOUNT_PATH="/path/to/service-account.json"
export DRIVE_FOLDER_ID="optional_folder_id"
```

Best for automation and CI/CD. Requires sharing each spreadsheet with the service account email. **Cannot create new spreadsheets** (service accounts have no Drive quota).

### 3. Application Default Credentials
```bash
gcloud auth application-default login
```

Uses gcloud CLI credentials if available.

### 4. Direct Injection
```bash
export CREDENTIALS_CONFIG="base64_encoded_service_account_json"
```

For containerized environments where file paths are impractical.

## Troubleshooting

**"Permission denied" accessing spreadsheet:**
- Share the spreadsheet with your service account email
- Grant "Editor" permission (not just "Viewer")

**"Authentication failed":**
- Verify your JSON key file path is correct
- Ensure APIs are enabled in Google Cloud Console

**Tools not showing up:**
- Restart Claude Code completely
- Verify your MCP configuration with: `claude mcp list`

## Links

- [Google Sheets API](https://developers.google.com/sheets/api)
- [MCP Specification](https://modelcontextprotocol.io)
- [FastMCP](https://gofastmcp.com)

## License

MIT
