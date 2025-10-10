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

## Quick Start

### 1. Google Cloud Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project

2. **Enable APIs**
   - Enable Google Sheets API
   - Enable Google Drive API

3. **Create Service Account**
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Name it (e.g., "mcp-gsheets")
   - Click "Create and Continue", then "Done"
   - Click on the service account → Keys tab
   - Add Key → Create new key → JSON
   - Save the JSON file securely

4. **Get the Service Account Email**
   - Open the JSON file
   - Copy the `client_email` value (e.g., `xxx@xxx.iam.gserviceaccount.com`)
   - Share your Google Sheets with this email address (Editor permission)

### 2. Install with Claude Code

Run this command in your terminal (update the paths to match your setup):

```bash
claude mcp add --transport stdio sheets \
  --env SERVICE_ACCOUNT_PATH=/path/to/your/service-account.json \
  --env DRIVE_FOLDER_ID=your_optional_folder_id \
  --scope user \
  -- uvx mcp-gsheets
```

**Note:** The `DRIVE_FOLDER_ID` is optional. If provided, the server will only list spreadsheets in that folder.

To get your folder ID:
1. Open the folder in Google Drive
2. Copy the ID from the URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`

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

### Service Account (Recommended)
```bash
export SERVICE_ACCOUNT_PATH="/path/to/service-account.json"
export DRIVE_FOLDER_ID="optional_folder_id"
```

### OAuth 2.0 Flow
```bash
export CREDENTIALS_PATH="/path/to/credentials.json"
export TOKEN_PATH="/path/to/token.json"
```

### Application Default Credentials
```bash
gcloud auth application-default login
```

### Direct Injection
```bash
export CREDENTIALS_CONFIG="base64_encoded_service_account_json"
```

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
