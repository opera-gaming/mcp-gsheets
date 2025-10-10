# Setup Guide for mcp-gsheets

This guide walks you through setting up mcp-gsheets for use with Claude Desktop or other MCP clients.

## Table of Contents

1. [Google Cloud Setup](#google-cloud-setup)
2. [Authentication Methods](#authentication-methods)
3. [Claude Desktop Configuration](#claude-desktop-configuration)
4. [Testing Your Setup](#testing-your-setup)
5. [Troubleshooting](#troubleshooting)

## Google Cloud Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name your project (e.g., "mcp-gsheets")
4. Click "Create"

### Step 2: Enable Required APIs

1. In the Cloud Console, go to "APIs & Services" → "Library"
2. Search for and enable:
   - **Google Sheets API**
   - **Google Drive API**

### Step 3: Set Up Authentication

#### Option A: Service Account (Recommended for Production)

1. **Create Service Account:**
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name it (e.g., "mcp-gsheets-sa")
   - Click "Create and Continue"
   - Skip optional steps, click "Done"

2. **Create and Download Key:**
   - Click on your new service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON"
   - Save the file securely (e.g., `~/mcp-gsheets-service-account.json`)

3. **Share Spreadsheets:**
   - Open the JSON key file
   - Copy the `client_email` value (looks like: `xxx@xxx.iam.gserviceaccount.com`)
   - In Google Sheets, share your spreadsheets with this email address
   - Grant "Editor" permission

#### Option B: OAuth 2.0 (For Personal Use)

1. **Create OAuth 2.0 Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app"
   - Name it (e.g., "mcp-gsheets-oauth")
   - Click "Create"

2. **Download Credentials:**
   - Click the download icon next to your OAuth client
   - Save as `credentials.json`

## Authentication Methods

### Method 1: Service Account (Recommended)

Set environment variables:

```bash
export SERVICE_ACCOUNT_PATH="/path/to/service-account-key.json"
export DRIVE_FOLDER_ID="optional_folder_id"  # Optional: limit to specific folder
```

**Pros:**
- No user interaction required
- Perfect for automation
- Works in server environments

**Cons:**
- Need to explicitly share spreadsheets with service account email

### Method 2: OAuth 2.0 Flow

Set environment variables:

```bash
export CREDENTIALS_PATH="/path/to/credentials.json"
export TOKEN_PATH="/path/to/token.json"  # Will be created automatically
```

**Pros:**
- Access to your personal spreadsheets automatically
- No sharing required

**Cons:**
- Requires browser interaction on first run
- Token may expire

### Method 3: Application Default Credentials

Use gcloud CLI:

```bash
gcloud auth application-default login
```

**Pros:**
- Easy for local development
- Works with gcloud CLI

**Cons:**
- Requires gcloud CLI installed
- Not suitable for production

### Method 4: Direct Credential Injection

```bash
export CREDENTIALS_CONFIG="base64_encoded_service_account_json"
```

Convert service account JSON to base64:

```bash
base64 -i service-account.json | tr -d '\n'
```

**Pros:**
- Works in containerized environments
- No file path dependencies

**Cons:**
- Environment variable with sensitive data

## Claude Desktop Configuration

### macOS

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gsheets": {
      "command": "uvx",
      "args": ["mcp-gsheets@latest"],
      "env": {
        "SERVICE_ACCOUNT_PATH": "/Users/yourname/mcp-gsheets-sa.json",
        "DRIVE_FOLDER_ID": ""
      }
    }
  }
}
```

### Windows

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gsheets": {
      "command": "uvx",
      "args": ["mcp-gsheets@latest"],
      "env": {
        "SERVICE_ACCOUNT_PATH": "C:\\Users\\yourname\\mcp-gsheets-sa.json",
        "DRIVE_FOLDER_ID": ""
      }
    }
  }
}
```

### Linux

Edit `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gsheets": {
      "command": "uvx",
      "args": ["mcp-gsheets@latest"],
      "env": {
        "SERVICE_ACCOUNT_PATH": "/home/yourname/mcp-gsheets-sa.json",
        "DRIVE_FOLDER_ID": ""
      }
    }
  }
}
```

## Testing Your Setup

### 1. Test Authentication

Run the server directly to verify authentication:

```bash
# Set environment variables first
export SERVICE_ACCOUNT_PATH="/path/to/service-account.json"

# Run server
uvx mcp-gsheets@latest
```

You should see:
```
Using service account authentication
Working with Google Drive folder ID: Not specified
```

### 2. Test with Claude Desktop

1. Restart Claude Desktop completely (quit and reopen)
2. Start a new conversation
3. Try asking Claude to:
   - "List my Google Spreadsheets"
   - "Create a new spreadsheet called 'Test'"
   - "Add some sample data to it"

### 3. Verify Tools Are Available

In Claude, you can check available tools by asking:
> "What Google Sheets operations can you perform?"

Claude should describe 40+ tools including:
- Basic CRUD operations
- Chart creation
- Cell formatting
- Conditional formatting
- Data validation
- And more...

## Troubleshooting

### Error: "Authentication failed"

**Solution:**
1. Verify your JSON key file path is correct
2. Check file permissions: `chmod 600 /path/to/service-account.json`
3. Ensure APIs are enabled in Google Cloud Console

### Error: "Permission denied" when accessing spreadsheet

**Solution:**
1. Share the spreadsheet with your service account email
2. Grant "Editor" permission (not just "Viewer")
3. Check the `client_email` field in your service account JSON

### Error: "Module not found"

**Solution:**
1. Ensure `uv` is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Try reinstalling: `uv cache clean && uvx mcp-gsheets@latest`

### Claude Desktop Not Recognizing Server

**Solution:**
1. Check JSON syntax in `claude_desktop_config.json` (use a JSON validator)
2. Restart Claude Desktop completely
3. Check Claude's logs:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`
   - Linux: `~/.config/Claude/logs/`

### Spreadsheets Not Showing Up

**Solution:**
1. If using Service Account: verify spreadsheet is shared with service account email
2. If using `DRIVE_FOLDER_ID`: ensure spreadsheets are in that folder
3. Try `list_spreadsheets` tool to see what's accessible

## Getting Folder ID

To limit mcp-gsheets to a specific Google Drive folder:

1. Open Google Drive in browser
2. Navigate to your folder
3. Copy the folder ID from URL:
   ```
   https://drive.google.com/drive/folders/FOLDER_ID_HERE
   ```
4. Set `DRIVE_FOLDER_ID` environment variable to this ID

## Security Best Practices

1. **Never commit credentials to git**
   - Add `*.json` to `.gitignore`
   - Use environment variables

2. **Restrict service account permissions**
   - Only grant necessary API access
   - Share only specific spreadsheets

3. **Rotate keys regularly**
   - Create new service account keys periodically
   - Delete old keys from Google Cloud Console

4. **Use folder restrictions**
   - Set `DRIVE_FOLDER_ID` to limit access scope

## Next Steps

Once setup is complete:

1. Check out the [README.md](README.md) for usage examples
2. Experiment with different tools via Claude
3. Build automation workflows
4. Integrate with your professional workflows

## Support

- GitHub Issues: [Report issues](https://github.com/yourusername/mcp-gsheets/issues)
- Google Sheets API Docs: [Official Documentation](https://developers.google.com/sheets/api)
- MCP Specification: [Learn about MCP](https://modelcontextprotocol.io)
