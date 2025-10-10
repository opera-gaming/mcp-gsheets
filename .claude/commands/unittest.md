---
description: Run comprehensive unit tests for mcp-gsheets MCP server
---

Run comprehensive unit tests for mcp-gsheets MCP server. Execute all tests systematically and report results.

## Test 1: Spreadsheet Management
1. List all Google Spreadsheets
2. Create spreadsheet "MCP Test Suite" (save the ID as TEST_SPREADSHEET_ID for later tests)

## Test 2: Sheet Management
1. List all sheets in TEST_SPREADSHEET_ID (expect ["Sheet1"])
2. Create sheet "Test Data"
3. Create sheets "Formatting Tests", "Chart Tests", "Validation Tests"
4. Rename "Sheet1" to "Main"
5. List sheets again (should show all 5 sheets)
6. Delete "Test Data" sheet

## Test 3: Basic Data Operations
In sheet "Main":
1. Update A1:C1 with ["Product", "Q1 Sales", "Q2 Sales"]
2. Batch update A2:C5 with 4 product rows (Widget A-D with sales data)
3. Read all data from sheet "Main"
4. Append 2 more rows (Widget E-F)
5. Clear cells B6:C6
6. Batch clear B6:C6 and A6

## Test 4: Cell Formatting
In sheet "Formatting Tests":
1. Update and format A1:D1 as bold, size 12, blue background, center aligned
2. Update A3 with "Monospace Text", format as Courier New, italic, size 14
3. Update A5 with "Red Text", format with red text color
4. Merge cells A7:D7, then unmerge
5. Update B10:B12 with [1000, 2500, 3750], format as CURRENCY "$#,##0.00"
6. Update C10:C12 with [0.15, 0.25, 0.089], format as PERCENT
7. Update D10:D12 with [45000, 45100, 45200], format as DATE

## Test 5: Row/Column Operations
In sheet "Main":
1. Insert 3 rows at position 2
2. Delete rows 2-4
3. Insert 2 columns at position 3
4. Delete columns 3-4
5. Auto-resize columns 0-2

## Test 6: Charts
In sheet "Chart Tests":
1. Create data: A1:C5 with Month/Sales/Target data (Jan-Apr)
2. Create COLUMN chart "Monthly Sales vs Target" at row 0, col 4, use first row as headers
3. Create LINE chart "Sales Trend" at row 10, col 4
4. Create data E1:F5 with Category/Amount (Desktop/Mobile/Tablet)
5. Create PIE chart "Device Distribution" at row 0, col 8

## Test 7: Data Validation
In sheet "Validation Tests":
1. Add dropdown to D2:D10 with values ["High", "Medium", "Low"]
2. Add checkboxes to E2:E10 (BOOLEAN validation)
3. Add number range 0-100 validation to F2:F10

## Test 8: Conditional Formatting
In sheet "Validation Tests":
1. Add data A1:B6 with Item/Score pairs
2. Add conditional format to B2:B6: highlight >70 in green
3. Add data G2:G5 with status values
4. Add conditional format: highlight cells containing "Complete" in light blue

## Test 9: Sorting
In sheet "Main":
1. Sort A2:C6 by column B ascending
2. Sort A2:C6 by column C descending

## Test 10: Find and Replace
1. In sheet "Main", replace "Widget" with "Product"
2. Test case-sensitive replace
3. Test regex replace (if applicable)

## Test 11: Formulas
In sheet "Main":
1. Update D1 with "Total"
2. Update D2 with formula "=B2+C2"
3. Get formulas from D2:D6 (should return formulas, not values)

## Test 12: Copy Sheet
1. Copy "Main" to same spreadsheet as "Main Backup"
2. Create new spreadsheet "Test Destination"
3. Copy "Main" to new spreadsheet as "Imported Data"

## Test 13: Advanced Scenarios

### Complete Report
1. Create spreadsheet "Q1 2025 Report"
2. Rename Sheet1 to "Summary"
3. Add headers ["Product", "Jan", "Feb", "Mar", "Total"]
4. Format headers: bold, blue background, center aligned
5. Add 5 product rows with sample data
6. Add SUM formulas in column E
7. Format B2:E6 as currency
8. Add conditional formatting: highlight totals >5000 in green
9. Create column chart
10. Auto-resize all columns

## Test 14: Error Handling
1. Try to update non-existent sheet "DoesNotExist" (expect error)
2. Try invalid range (expect error)
3. Try invalid color values (expect error)

## Results Template
For each test category, report:
- ✅ PASS: Works as expected
- ⚠️ PARTIAL: Works with minor issues
- ❌ FAIL: Doesn't work
- 📝 NOTES: Any observations

## Final Summary
Provide:
- Total tests run
- Pass/Fail/Partial counts
- Critical issues found
- Overall MCP functionality assessment
