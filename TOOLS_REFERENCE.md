# mcp-gsheets Tools Reference

Quick reference for all 30 MCP tools available in mcp-gsheets.

## Core Data Operations (7 tools)

### `get_sheet_data`
Read data from a specific sheet.
- **Args:** spreadsheet_id, sheet, range (optional), include_grid_data (optional)
- **Returns:** Sheet data with values
- **Example:** Get data from range A1:B10

### `get_sheet_formulas`
Extract formulas from cells instead of computed values.
- **Args:** spreadsheet_id, sheet, range (optional)
- **Returns:** 2D array of formulas
- **Example:** Get all formulas from a sheet

### `update_cells`
Update cell values in a range.
- **Args:** spreadsheet_id, sheet, range, data (2D array)
- **Returns:** Update result
- **Example:** Update A1:B2 with new values

### `batch_update_cells`
Update multiple ranges at once for efficiency.
- **Args:** spreadsheet_id, sheet, ranges (dict mapping ranges to data)
- **Returns:** Batch update result
- **Example:** Update A1:B2 and D1:E2 in one request

### `append_values`
Append rows to the end of a sheet.
- **Args:** spreadsheet_id, sheet, range, data
- **Returns:** Append result
- **Example:** Add new rows of data

### `clear_range`
Clear values from cells (keeps formatting).
- **Args:** spreadsheet_id, sheet, range
- **Returns:** Clear result
- **Example:** Clear data from A1:Z100

### `batch_clear_ranges`
Clear multiple ranges at once.
- **Args:** spreadsheet_id, sheet, ranges (list)
- **Returns:** Batch clear result
- **Example:** Clear A1:B10 and D1:E10

## Sheet Management (5 tools)

### `list_sheets`
List all sheet names in a spreadsheet.
- **Args:** spreadsheet_id
- **Returns:** List of sheet names
- **Example:** Get all tab names

### `create_sheet`
Create a new sheet tab.
- **Args:** spreadsheet_id, title, rows (optional), cols (optional)
- **Returns:** New sheet info with ID
- **Example:** Create "Q4 Report" sheet with 1000 rows

### `rename_sheet`
Rename an existing sheet.
- **Args:** spreadsheet_id, sheet, new_name
- **Returns:** Rename result
- **Example:** Rename "Sheet1" to "Sales Data"

### `delete_sheet`
Delete a sheet from spreadsheet.
- **Args:** spreadsheet_id, sheet
- **Returns:** Delete result
- **Example:** Remove unwanted sheet

### `copy_sheet`
Copy a sheet to another spreadsheet.
- **Args:** src_spreadsheet, src_sheet, dst_spreadsheet, dst_sheet
- **Returns:** Copy result
- **Example:** Copy "Template" to new spreadsheet

## Row/Column Operations (5 tools)

### `add_rows`
Insert rows at specified position.
- **Args:** spreadsheet_id, sheet, count, start_row (optional)
- **Returns:** Insert result
- **Example:** Insert 5 rows at position 10

### `add_columns`
Insert columns at specified position.
- **Args:** spreadsheet_id, sheet, count, start_column (optional)
- **Returns:** Insert result
- **Example:** Insert 3 columns at position 5

### `delete_rows`
Delete a range of rows.
- **Args:** spreadsheet_id, sheet, start_row, end_row
- **Returns:** Delete result
- **Example:** Delete rows 5-10 (0-indexed)

### `delete_columns`
Delete a range of columns.
- **Args:** spreadsheet_id, sheet, start_column, end_column
- **Returns:** Delete result
- **Example:** Delete columns 2-4

### `auto_resize_dimensions`
Auto-fit rows or columns to content.
- **Args:** spreadsheet_id, sheet, dimension ('ROWS'/'COLUMNS'), start_index, end_index
- **Returns:** Resize result
- **Example:** Auto-fit columns 0-10 to content width

## Charts & Visualizations (2 tools)

### `add_chart`
Create a chart from data.
- **Args:** spreadsheet_id, sheet, chart_type, data_range, title (optional), position_row, position_col
- **Chart types:** BAR, COLUMN, LINE, AREA, SCATTER, PIE
- **Returns:** Chart creation result with chart ID
- **Example:** Create column chart from A1:B10

### `delete_chart`
Remove a chart by ID.
- **Args:** spreadsheet_id, chart_id
- **Returns:** Delete result
- **Example:** Remove chart #123

## Cell Formatting (4 tools)

### `format_cells`
Apply formatting to cell range.
- **Args:** spreadsheet_id, sheet, range, background_color, text_color, bold, italic, font_size, horizontal_alignment
- **Colors:** RGB dict with 'red', 'green', 'blue' (0.0-1.0)
- **Alignment:** LEFT, CENTER, RIGHT
- **Returns:** Format result
- **Example:** Make A1:A10 bold with blue background

### `merge_cells`
Merge a range of cells.
- **Args:** spreadsheet_id, sheet, start_row, end_row, start_col, end_col, merge_type
- **Merge types:** MERGE_ALL, MERGE_COLUMNS, MERGE_ROWS
- **Returns:** Merge result
- **Example:** Merge A1:C1 for header

### `unmerge_cells`
Unmerge previously merged cells.
- **Args:** spreadsheet_id, sheet, start_row, end_row, start_col, end_col
- **Returns:** Unmerge result
- **Example:** Unmerge A1:C1

### `set_number_format`
Format numbers, currency, dates, percentages.
- **Args:** spreadsheet_id, sheet, start_row, end_row, start_col, end_col, format_type, pattern (optional)
- **Format types:** NUMBER, CURRENCY, PERCENT, DATE, TIME, SCIENTIFIC
- **Pattern:** Custom format string (e.g., "$#,##0.00")
- **Returns:** Format result
- **Example:** Format column as currency

## Data Validation (1 tool)

### `add_data_validation`
Add dropdowns, checkboxes, or custom validation.
- **Args:** spreadsheet_id, sheet, start_row, end_row, start_col, end_col, validation_type, values (optional), strict
- **Types:** ONE_OF_LIST, BOOLEAN, NUMBER_BETWEEN, NUMBER_GREATER, NUMBER_LESS, TEXT_CONTAINS, DATE_AFTER, DATE_BEFORE
- **Returns:** Validation result
- **Example:** Add dropdown with options ["High", "Medium", "Low"]

## Conditional Formatting (1 tool)

### `add_conditional_format_rule`
Apply conditional formatting rules.
- **Args:** spreadsheet_id, sheet, start_row, end_row, start_col, end_col, condition_type, condition_values, background_color, text_color
- **Condition types:** NUMBER_GREATER, NUMBER_LESS, NUMBER_BETWEEN, TEXT_CONTAINS, TEXT_STARTS_WITH, DATE_BEFORE, DATE_AFTER, CUSTOM_FORMULA
- **Returns:** Rule creation result
- **Example:** Highlight cells > 100 in green

## Filtering & Sorting (1 tool)

### `sort_range`
Sort a range by column.
- **Args:** spreadsheet_id, sheet, start_row, end_row, start_col, end_col, sort_column, ascending
- **Returns:** Sort result
- **Example:** Sort A1:C100 by column B descending

## Advanced Operations (1 tool)

### `find_replace`
Find and replace text with optional regex.
- **Args:** spreadsheet_id, sheet (optional), find, replacement, match_case, match_entire_cell, search_by_regex
- **Returns:** Result with replacement count
- **Example:** Replace all phone numbers with formatted version using regex

## Spreadsheet Management (3 tools)

### `create_spreadsheet`
Create a new Google Spreadsheet.
- **Args:** title
- **Returns:** New spreadsheet info with ID
- **Example:** Create "2025 Budget" spreadsheet

### `list_spreadsheets`
List all accessible spreadsheets.
- **Args:** None (uses folder_id from config if set)
- **Returns:** List of spreadsheets with IDs and titles
- **Example:** Get all spreadsheets in Drive

### `share_spreadsheet`
Share spreadsheet with users.
- **Args:** spreadsheet_id, recipients (list of dicts), send_notification
- **Recipients:** List of {'email_address': 'user@example.com', 'role': 'writer'}
- **Roles:** reader, writer, commenter
- **Returns:** Success/failure lists
- **Example:** Share with team members

## Usage Tips

### Batch Operations
Always prefer batch operations when possible:
- Use `batch_update_cells` instead of multiple `update_cells`
- Use `batch_clear_ranges` instead of multiple `clear_range`

### Color Format
Colors use RGB values from 0.0 to 1.0:
```python
{"red": 0.0, "green": 0.5, "blue": 1.0}  # Blue-ish color
{"red": 1.0, "green": 0.0, "blue": 0.0}  # Pure red
{"red": 0.0, "green": 1.0, "blue": 0.0}  # Pure green
```

### Index Format
Most operations use 0-based indexing:
- Row 1 in Sheets = index 0
- Column A in Sheets = index 0
- Ranges are inclusive at start, exclusive at end

### Range Notation
Support for A1 notation where applicable:
- "A1:B10" - Range from A1 to B10
- "A:A" - Entire column A
- "1:1" - Entire row 1

## Tool Categories by Use Case

### Data Entry & Manipulation
- `update_cells`, `batch_update_cells`, `append_values`
- `clear_range`, `batch_clear_ranges`
- `get_sheet_data`, `get_sheet_formulas`

### Sheet Organization
- `create_sheet`, `delete_sheet`, `rename_sheet`
- `add_rows`, `add_columns`, `delete_rows`, `delete_columns`
- `copy_sheet`

### Visualization
- `add_chart`, `delete_chart`

### Formatting & Styling
- `format_cells`, `set_number_format`
- `merge_cells`, `unmerge_cells`
- `auto_resize_dimensions`

### Data Quality
- `add_data_validation`
- `add_conditional_format_rule`
- `sort_range`

### Automation
- `find_replace`
- `batch_update_cells`
- `create_spreadsheet`, `share_spreadsheet`

## Quick Start Examples

### Create and Populate Spreadsheet
```
1. create_spreadsheet(title="Sales Report")
2. update_cells(spreadsheet_id, "Sheet1", "A1:C1", [["Product", "Q1", "Q2"]])
3. append_values(spreadsheet_id, "Sheet1", "A2", [[Product A", 100, 120]])
```

### Format Report
```
1. format_cells(..., bold=True, background_color={"red": 0.2, "green": 0.6, "blue": 0.9})
2. set_number_format(..., format_type="CURRENCY", pattern="$#,##0.00")
3. merge_cells(..., merge_type="MERGE_ALL")
```

### Add Chart
```
1. add_chart(..., chart_type="COLUMN", data_range="A1:B10", title="Quarterly Sales")
```

### Data Validation
```
1. add_data_validation(..., validation_type="ONE_OF_LIST", values=["Pending", "Complete"])
```

---

**Total: 30 comprehensive tools covering 60%+ of Google Sheets API v4**
