# MCP-GSHEETS TODO

## Issues Found During Unit Testing

### High Priority

1. **PIE Chart Support**
   - Status: PIE chart type fails with "Invalid value" error
   - Issue: basicChart spec doesn't support PIE type in Google Sheets API
   - Solution needed: Implement PieChart spec instead of BasicChart for PIE type
   - File: `src/mcp_gsheets/server.py` (add_chart function)

2. **format_cells Range Requirement**
   - Status: Single cell formatting requires "A1:A1" notation, not "A1"
   - Issue: Inconsistent with update_cells which accepts "A1" for single cells
   - Solution: Add logic to auto-convert single cell "A1" to "A1:A1" format
   - File: `src/mcp_gsheets/server.py` (format_cells function)

3. **Storage Quota Error Handling**
   - Status: create_spreadsheet fails with quota exceeded error
   - Issue: User gets cryptic 403 error instead of helpful message
   - Solution: Add better error handling and user-friendly message for quota issues
   - File: `src/mcp_gsheets/server.py` (create_spreadsheet function)

### Medium Priority

4. **Number Range Validation**
   - Status: Not tested in unit tests (Test 7 only tested dropdowns and checkboxes)
   - Task: Implement and test NUMBER_BETWEEN validation type
   - File: `src/mcp_gsheets/server.py` (add_data_validation function)

5. **Copy Sheet Function**
   - Status: Missing implementation
   - Task: Implement copy_sheet functionality for both same and different spreadsheets
   - File: `src/mcp_gsheets/server.py` (new function needed)

6. **Regex Find/Replace**
   - Status: Not tested
   - Task: Test and verify search_by_regex parameter works correctly
   - File: Verify in `src/mcp_gsheets/server.py` (find_replace function)

### Low Priority

7. **Color Value Validation**
   - Status: API accepts out-of-range RGB values (5.0 accepted instead of clamping to 1.0)
   - Task: Add client-side validation to clamp RGB values to 0.0-1.0 range
   - File: `src/mcp_gsheets/server.py` (format_cells, add_conditional_format_rule functions)

8. **Delete Chart Implementation**
   - Status: Function exists but not tested
   - Task: Add unit test for delete_chart functionality
   - File: Test coverage for `delete_chart`

9. **Share Spreadsheet**
   - Status: Not tested
   - Task: Add unit test for share_spreadsheet functionality
   - File: Test coverage for `share_spreadsheet`

## Documentation Needs

10. **README Updates**
    - Document format_cells range requirement
    - Document PIE chart limitation (until fixed)
    - Add troubleshooting section for quota errors
    - Add examples for all major operations

11. **Error Handling Guide**
    - Document common error scenarios
    - Provide solutions for quota issues
    - Explain API limitations

## Testing Improvements

12. **Add Integration Tests**
    - Create test suite that doesn't depend on user's Drive quota
    - Mock Google Sheets API responses
    - Test edge cases more thoroughly

13. **Add Performance Tests**
    - Test batch operations with large datasets
    - Measure response times for various operations

## Feature Requests

14. **Batch Format Operations**
    - Add ability to format multiple ranges in single call
    - Similar to batch_update_cells

15. **Template Support**
    - Add function to create spreadsheets from templates
    - Useful for report generation

## Investigation Needed

16. **Google Drive Quota Issue**
    - Investigate user's quota status
    - Determine if quota can be increased
    - Document quota limits and how to check current usage
    - Consider implementing quota checking before operations
