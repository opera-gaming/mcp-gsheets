# mcp-gsheets

**Comprehensive MCP Server for Google Sheets API v4**

A professional-grade Model Context Protocol (MCP) server that provides complete coverage of the Google Sheets API, including charts, formatting, conditional formatting, data validation, pivot tables, and much more.

[![PyPI version](https://badge.fury.io/py/mcp-gsheets.svg)](https://badge.fury.io/py/mcp-gsheets)

## 🎯 Why mcp-gsheets?

While other Google Sheets MCP servers focus on basic CRUD operations, **mcp-gsheets** provides the **complete API surface** including:

- ✅ Full CRUD operations (read, write, update, append, clear)
- ✅ **Charts and visualizations** (bar, column, line, pie, scatter, area charts)
- ✅ **Cell formatting** (colors, fonts, alignment, number formats, borders)
- ✅ **Conditional formatting** rules
- ✅ **Data validation** (dropdowns, checkboxes, custom rules)
- ✅ **Filtering and sorting**
- ✅ **Merge/unmerge cells**
- ✅ **Find and replace** (with regex support)
- ✅ **Row/column operations** (add, delete, auto-resize)
- ✅ **Sheet management** (create, delete, rename, copy)
- ✅ **Spreadsheet management** (create, list, share)
- ✅ Formula support
- ✅ Batch operations for performance

## 🚀 Quick Start

### Installation

The easiest way to use mcp-gsheets is with `uvx`:

```bash
uvx mcp-gsheets@latest
```

Or install via pip:

```bash
pip install mcp-gsheets
```

### Prerequisites: Google Cloud Setup

Before using mcp-gsheets, you need to set up Google Cloud credentials:

1. **Create a Google Cloud Project**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Required APIs**

   - Enable the Google Sheets API
   - Enable the Google Drive API

3. **Create Service Account (Recommended)**

   - Go to IAM & Admin → Service Accounts
   - Create a new service account
   - Download the JSON key file
   - Share your spreadsheets with the service account email

4. **Set Environment Variables**

```bash
export SERVICE_ACCOUNT_PATH="/path/to/your/service-account-key.json"
export DRIVE_FOLDER_ID="your_drive_folder_id"  # Optional
```

### Using with Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "gsheets": {
      "command": "uvx",
      "args": ["mcp-gsheets@latest"],
      "env": {
        "SERVICE_ACCOUNT_PATH": "/path/to/your/service-account-key.json",
        "DRIVE_FOLDER_ID": "your_folder_id"
      }
    }
  }
}
```

## 📚 Available Tools

### Core Data Operations

- `get_sheet_data` - Read data from a sheet
- `get_sheet_formulas` - Get formulas from cells
- `update_cells` - Update cell values
- `batch_update_cells` - Update multiple ranges at once
- `append_values` - Append rows to a sheet
- `clear_range` - Clear cell values
- `batch_clear_ranges` - Clear multiple ranges

### Sheet Management

- `list_sheets` - List all sheets in a spreadsheet
- `create_sheet` - Create a new sheet tab
- `rename_sheet` - Rename a sheet
- `delete_sheet` - Delete a sheet
- `copy_sheet` - Copy a sheet to another spreadsheet

### Row/Column Operations

- `add_rows` - Insert rows
- `add_columns` - Insert columns
- `delete_rows` - Delete rows
- `delete_columns` - Delete columns
- `auto_resize_dimensions` - Auto-fit rows/columns to content

### Charts & Visualizations

- `add_chart` - Create charts (BAR, COLUMN, LINE, PIE, SCATTER, AREA)
- `delete_chart` - Remove charts

### Cell Formatting

- `format_cells` - Set colors, fonts, alignment, bold, italic
- `merge_cells` - Merge cell ranges
- `unmerge_cells` - Unmerge cells
- `set_number_format` - Format numbers, currency, dates, percentages

### Conditional Formatting

- `add_conditional_format_rule` - Add conditional formatting rules with custom colors

### Data Validation

- `add_data_validation` - Add dropdowns, checkboxes, and validation rules

### Filtering & Sorting

- `sort_range` - Sort data by column

### Advanced Operations

- `find_replace` - Find and replace text (with regex support)

### Spreadsheet Management

- `create_spreadsheet` - Create new spreadsheets
- `list_spreadsheets` - List all spreadsheets
- `share_spreadsheet` - Share spreadsheets with users

## 💡 Usage Examples

### Example 1: Create and Format a Report

```python
# Create a new spreadsheet
create_spreadsheet(title="Q4 Sales Report")

# Add data
update_cells(
    spreadsheet_id="...",
    sheet="Sheet1",
    range="A1:C1",
    data=[["Product", "Sales", "Growth"]]
)

# Format header row
format_cells(
    spreadsheet_id="...",
    sheet="Sheet1",
    range="A1:C1",
    background_color={"red": 0.2, "green": 0.6, "blue": 0.9},
    bold=True,
    horizontal_alignment="CENTER"
)

# Add a chart
add_chart(
    spreadsheet_id="...",
    sheet="Sheet1",
    chart_type="COLUMN",
    data_range="A1:C10",
    title="Q4 Sales by Product"
)
```

### Example 2: Data Validation

```python
# Add dropdown validation
add_data_validation(
    spreadsheet_id="...",
    sheet="Sheet1",
    start_row=1,
    end_row=100,
    start_col=3,
    end_col=4,
    validation_type="ONE_OF_LIST",
    values=["Pending", "In Progress", "Complete"]
)
```

### Example 3: Conditional Formatting

```python
# Highlight cells above threshold
add_conditional_format_rule(
    spreadsheet_id="...",
    sheet="Sheet1",
    start_row=1,
    end_row=100,
    start_col=2,
    end_col=3,
    condition_type="NUMBER_GREATER",
    condition_values=["1000"],
    background_color={"red": 0.0, "green": 0.9, "blue": 0.0}
)
```

### Example 4: Find and Replace

```python
# Replace all occurrences with regex
find_replace(
    spreadsheet_id="...",
    sheet="Sheet1",
    find=r"(\d{3})-(\d{3})-(\d{4})",
    replacement=r"($1) $2-$3",
    search_by_regex=True
)
```

## 🔧 Authentication Options

### 1. Service Account (Recommended for Production)

```bash
export SERVICE_ACCOUNT_PATH="/path/to/service-account.json"
```

### 2. OAuth Flow (Interactive)

```bash
export CREDENTIALS_PATH="/path/to/credentials.json"
export TOKEN_PATH="/path/to/token.json"
```

### 3. Application Default Credentials

Uses gcloud CLI authentication automatically.

### 4. Direct Credential Injection

```bash
export CREDENTIALS_CONFIG="base64_encoded_service_account_json"
```

## 🏗️ Architecture

mcp-gsheets is built with:

- **[FastMCP](https://gofastmcp.com)** - High-level MCP framework for Python
- **Google Sheets API v4** - Complete API coverage
- **Google Drive API v3** - For spreadsheet management

## 📊 Tool Count

**40+ tools** covering the complete Google Sheets API surface area

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License

## 🔗 Links

- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [FastMCP Documentation](https://gofastmcp.com)
- [MCP Specification](https://modelcontextprotocol.io)

## 🙏 Acknowledgments

Built with inspiration from [mcp-google-sheets](https://github.com/xing5/mcp-google-sheets) by Xing Wu, extending it with comprehensive API coverage for professional use.
