"""
mcp-gsheets: Comprehensive MCP server for Google Sheets API v4

This package provides complete coverage of the Google Sheets API including:
- Basic CRUD operations
- Charts and visualizations
- Cell formatting and styling
- Conditional formatting
- Data validation
- Filtering and sorting
- Pivot tables
- Protected ranges
- Named ranges
- And much more
"""

from . import server

def main():
    """Main entry point for the package."""
    server.mcp.run()

__version__ = "0.1.0"
__all__ = ['main', 'server']
