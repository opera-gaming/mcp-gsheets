#!/usr/bin/env python
"""
mcp-gsheets Server
Comprehensive Google Sheets MCP server covering the complete API v4 surface
"""

import base64
import os
from typing import List, Dict, Any, Optional, Union
import json
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

# MCP imports
from mcp.server.fastmcp import FastMCP, Context

# Google API imports
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import google.auth

# Constants
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
CREDENTIALS_CONFIG = os.environ.get('CREDENTIALS_CONFIG')
TOKEN_PATH = os.environ.get('TOKEN_PATH', 'token.json')
CREDENTIALS_PATH = os.environ.get('CREDENTIALS_PATH', 'credentials.json')
SERVICE_ACCOUNT_PATH = os.environ.get('SERVICE_ACCOUNT_PATH', 'service_account.json')
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID', '')

@dataclass
class SpreadsheetContext:
    """Context for Google Spreadsheet service"""
    sheets_service: Any
    drive_service: Any
    folder_id: Optional[str] = None


@asynccontextmanager
async def spreadsheet_lifespan(server: FastMCP) -> AsyncIterator[SpreadsheetContext]:
    """Manage Google Spreadsheet API connection lifecycle"""
    creds = None

    if CREDENTIALS_CONFIG:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(base64.b64decode(CREDENTIALS_CONFIG)),
            scopes=SCOPES
        )

    # Check for service account authentication
    if not creds and SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH,
                scopes=SCOPES
            )
            print("Using service account authentication")
            print(f"Working with Google Drive folder ID: {DRIVE_FOLDER_ID or 'Not specified'}")
        except Exception as e:
            print(f"Error using service account authentication: {e}")
            creds = None

    # Fall back to OAuth flow
    if not creds:
        print("Trying OAuth authentication flow")
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, 'r') as token:
                creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                    creds = flow.run_local_server(port=0)

                    with open(TOKEN_PATH, 'w') as token:
                        token.write(creds.to_json())
                    print("Successfully authenticated using OAuth flow")
                except Exception as e:
                    print(f"Error with OAuth flow: {e}")
                    creds = None

    # Try Application Default Credentials
    if not creds:
        try:
            print("Attempting to use Application Default Credentials (ADC)")
            creds, project = google.auth.default(scopes=SCOPES)
            print(f"Successfully authenticated using ADC for project: {project}")
        except Exception as e:
            print(f"Error using Application Default Credentials: {e}")
            raise Exception("All authentication methods failed. Please configure credentials.")

    # Build the services
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    try:
        yield SpreadsheetContext(
            sheets_service=sheets_service,
            drive_service=drive_service,
            folder_id=DRIVE_FOLDER_ID if DRIVE_FOLDER_ID else None
        )
    finally:
        pass


# Initialize the MCP server
mcp = FastMCP(
    "mcp-gsheets",
    dependencies=["google-auth", "google-auth-oauthlib", "google-api-python-client"],
    lifespan=spreadsheet_lifespan
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_sheet_id(sheets_service: Any, spreadsheet_id: str, sheet_name: str) -> Optional[int]:
    """Get the sheet ID from sheet name"""
    spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in spreadsheet.get('sheets', []):
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    return None


def parse_a1_notation(a1_range: str) -> Dict[str, int]:
    """Parse A1 notation range to grid coordinates"""
    import re

    match = re.match(r'([A-Z]+)(\d+):([A-Z]+)(\d+)', a1_range)
    if not match:
        return None

    def col_to_index(col: str) -> int:
        index = 0
        for char in col:
            index = index * 26 + (ord(char) - ord('A') + 1)
        return index - 1

    start_col, start_row, end_col, end_row = match.groups()

    return {
        'startRowIndex': int(start_row) - 1,
        'endRowIndex': int(end_row),
        'startColumnIndex': col_to_index(start_col),
        'endColumnIndex': col_to_index(end_col) + 1
    }


# ============================================================================
# CORE CRUD OPERATIONS
# ============================================================================

@mcp.tool()
def get_sheet_data(
    spreadsheet_id: str,
    sheet: str,
    range: Optional[str] = None,
    include_grid_data: bool = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get data from a specific sheet in a Google Spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet (found in the URL)
        sheet: The name of the sheet
        range: Optional cell range in A1 notation (e.g., 'A1:C10')
        include_grid_data: Include formatting metadata (default: False for efficiency)

    Returns:
        Sheet data with values
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    if range:
        full_range = f"{sheet}!{range}"
    else:
        full_range = sheet

    if include_grid_data:
        result = sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            ranges=[full_range],
            includeGridData=True
        ).execute()
    else:
        values_result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=full_range
        ).execute()

        result = {
            'spreadsheetId': spreadsheet_id,
            'valueRanges': [{
                'range': full_range,
                'values': values_result.get('values', [])
            }]
        }

    return result


@mcp.tool()
def get_sheet_formulas(
    spreadsheet_id: str,
    sheet: str,
    range: Optional[str] = None,
    ctx: Context = None
) -> List[List[Any]]:
    """
    Get formulas from a specific sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        range: Optional cell range in A1 notation

    Returns:
        2D array of formulas
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    if range:
        full_range = f"{sheet}!{range}"
    else:
        full_range = sheet

    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=full_range,
        valueRenderOption='FORMULA'
    ).execute()

    return result.get('values', [])


@mcp.tool()
def update_cells(
    spreadsheet_id: str,
    sheet: str,
    range: str,
    data: List[List[Any]],
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Update cells in a Google Spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        range: Cell range in A1 notation (e.g., 'A1:C10')
        data: 2D array of values to update

    Returns:
        Result of the update operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    full_range = f"{sheet}!{range}"

    value_range_body = {
        'values': data
    }

    result = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=full_range,
        valueInputOption='USER_ENTERED',
        body=value_range_body
    ).execute()

    return result


@mcp.tool()
def batch_update_cells(
    spreadsheet_id: str,
    sheet: str,
    ranges: Dict[str, List[List[Any]]],
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Batch update multiple ranges in a spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        ranges: Dictionary mapping range strings to 2D arrays
               e.g., {'A1:B2': [[1, 2], [3, 4]], 'D1:E2': [['a', 'b'], ['c', 'd']]}

    Returns:
        Result of the batch update operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    data = []
    for range_str, values in ranges.items():
        full_range = f"{sheet}!{range_str}"
        data.append({
            'range': full_range,
            'values': values
        })

    batch_body = {
        'valueInputOption': 'USER_ENTERED',
        'data': data
    }

    result = sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=batch_body
    ).execute()

    return result


@mcp.tool()
def append_values(
    spreadsheet_id: str,
    sheet: str,
    range: str,
    data: List[List[Any]],
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Append values to a sheet (adds rows at the end).

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        range: Starting range in A1 notation (e.g., 'A1')
        data: 2D array of values to append

    Returns:
        Result of the append operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    full_range = f"{sheet}!{range}"

    value_range_body = {
        'values': data
    }

    result = sheets_service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=full_range,
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body=value_range_body
    ).execute()

    return result


@mcp.tool()
def clear_range(
    spreadsheet_id: str,
    sheet: str,
    range: str,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Clear values from a range (keeps formatting).

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        range: Cell range in A1 notation

    Returns:
        Result of the clear operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    full_range = f"{sheet}!{range}"

    result = sheets_service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=full_range,
        body={}
    ).execute()

    return result


@mcp.tool()
def batch_clear_ranges(
    spreadsheet_id: str,
    sheet: str,
    ranges: List[str],
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Clear multiple ranges at once.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        ranges: List of ranges in A1 notation

    Returns:
        Result of the batch clear operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    full_ranges = [f"{sheet}!{r}" for r in ranges]

    batch_clear_body = {
        'ranges': full_ranges
    }

    result = sheets_service.spreadsheets().values().batchClear(
        spreadsheetId=spreadsheet_id,
        body=batch_clear_body
    ).execute()

    return result


# ============================================================================
# SHEET MANAGEMENT
# ============================================================================

@mcp.tool()
def list_sheets(spreadsheet_id: str, ctx: Context = None) -> List[str]:
    """
    List all sheets in a spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet

    Returns:
        List of sheet names
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_names = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]

    return sheet_names


@mcp.tool()
def create_sheet(
    spreadsheet_id: str,
    title: str,
    rows: int = 1000,
    cols: int = 26,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Create a new sheet tab in an existing spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        title: The title for the new sheet
        rows: Number of rows (default: 1000)
        cols: Number of columns (default: 26)

    Returns:
        Information about the newly created sheet
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    request_body = {
        "requests": [
            {
                "addSheet": {
                    "properties": {
                        "title": title,
                        "gridProperties": {
                            "rowCount": rows,
                            "columnCount": cols
                        }
                    }
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    new_sheet_props = result['replies'][0]['addSheet']['properties']

    return {
        'sheetId': new_sheet_props['sheetId'],
        'title': new_sheet_props['title'],
        'index': new_sheet_props.get('index'),
        'spreadsheetId': spreadsheet_id
    }


@mcp.tool()
def rename_sheet(
    spreadsheet_id: str,
    sheet: str,
    new_name: str,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Rename a sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: Current sheet name
        new_name: New sheet name

    Returns:
        Result of the operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    request_body = {
        "requests": [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "title": new_name
                    },
                    "fields": "title"
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


@mcp.tool()
def delete_sheet(
    spreadsheet_id: str,
    sheet: str,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Delete a sheet from a spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: Name of the sheet to delete

    Returns:
        Result of the delete operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    request_body = {
        "requests": [
            {
                "deleteSheet": {
                    "sheetId": sheet_id
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


@mcp.tool()
def copy_sheet(
    src_spreadsheet: str,
    src_sheet: str,
    dst_spreadsheet: str,
    dst_sheet: str,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Copy a sheet from one spreadsheet to another.

    Args:
        src_spreadsheet: Source spreadsheet ID
        src_sheet: Source sheet name
        dst_spreadsheet: Destination spreadsheet ID
        dst_sheet: Destination sheet name

    Returns:
        Result of the operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    src_sheet_id = get_sheet_id(sheets_service, src_spreadsheet, src_sheet)
    if src_sheet_id is None:
        return {"error": f"Source sheet '{src_sheet}' not found"}

    copy_result = sheets_service.spreadsheets().sheets().copyTo(
        spreadsheetId=src_spreadsheet,
        sheetId=src_sheet_id,
        body={
            "destinationSpreadsheetId": dst_spreadsheet
        }
    ).execute()

    if 'title' in copy_result and copy_result['title'] != dst_sheet:
        copy_sheet_id = copy_result['sheetId']

        rename_request = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": copy_sheet_id,
                            "title": dst_sheet
                        },
                        "fields": "title"
                    }
                }
            ]
        }

        rename_result = sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=dst_spreadsheet,
            body=rename_request
        ).execute()

        return {
            "copy": copy_result,
            "rename": rename_result
        }

    return {"copy": copy_result}


# ============================================================================
# ROW/COLUMN DIMENSION OPERATIONS
# ============================================================================

@mcp.tool()
def add_rows(
    spreadsheet_id: str,
    sheet: str,
    count: int,
    start_row: Optional[int] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Add rows to a sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        count: Number of rows to add
        start_row: 0-based row index to start adding (default: beginning)

    Returns:
        Result of the operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    request_body = {
        "requests": [
            {
                "insertDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": start_row if start_row is not None else 0,
                        "endIndex": (start_row if start_row is not None else 0) + count
                    },
                    "inheritFromBefore": start_row is not None and start_row > 0
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


@mcp.tool()
def add_columns(
    spreadsheet_id: str,
    sheet: str,
    count: int,
    start_column: Optional[int] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Add columns to a sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        count: Number of columns to add
        start_column: 0-based column index to start adding (default: beginning)

    Returns:
        Result of the operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    request_body = {
        "requests": [
            {
                "insertDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": start_column if start_column is not None else 0,
                        "endIndex": (start_column if start_column is not None else 0) + count
                    },
                    "inheritFromBefore": start_column is not None and start_column > 0
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


@mcp.tool()
def delete_rows(
    spreadsheet_id: str,
    sheet: str,
    start_row: int,
    end_row: int,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Delete rows from a sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        start_row: 0-based start row index (inclusive)
        end_row: 0-based end row index (exclusive)

    Returns:
        Result of the operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    request_body = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": start_row,
                        "endIndex": end_row
                    }
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


@mcp.tool()
def delete_columns(
    spreadsheet_id: str,
    sheet: str,
    start_column: int,
    end_column: int,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Delete columns from a sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        start_column: 0-based start column index (inclusive)
        end_column: 0-based end column index (exclusive)

    Returns:
        Result of the operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    request_body = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": start_column,
                        "endIndex": end_column
                    }
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


@mcp.tool()
def auto_resize_dimensions(
    spreadsheet_id: str,
    sheet: str,
    dimension: str,
    start_index: int,
    end_index: int,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Auto-resize rows or columns to fit content.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        dimension: 'ROWS' or 'COLUMNS'
        start_index: 0-based start index (inclusive)
        end_index: 0-based end index (exclusive)

    Returns:
        Result of the operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    request_body = {
        "requests": [
            {
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": sheet_id,
                        "dimension": dimension.upper(),
                        "startIndex": start_index,
                        "endIndex": end_index
                    }
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


# ============================================================================
# CHART OPERATIONS
# ============================================================================

@mcp.tool()
def add_chart(
    spreadsheet_id: str,
    sheet: str,
    chart_type: str,
    data_range: str,
    title: Optional[str] = None,
    position_row: int = 0,
    position_col: int = 0,
    y_axis_min: Optional[float] = None,
    y_axis_max: Optional[float] = None,
    use_first_row_as_headers: bool = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Add a chart to a sheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        chart_type: Chart type (BAR, COLUMN, LINE, AREA, SCATTER, PIE, etc.)
        data_range: Data range in A1 notation (e.g., 'A1:B10')
        title: Optional chart title
        position_row: Row position for chart (default: 0)
        position_col: Column position for chart (default: 0)
        y_axis_min: Optional minimum value for Y-axis
        y_axis_max: Optional maximum value for Y-axis
        use_first_row_as_headers: Use first row of data as column headers (default: False)

    Returns:
        Result including chart ID
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    coords = parse_a1_notation(data_range)
    if coords is None:
        return {"error": f"Invalid range format: {data_range}. Use A1 notation like 'A1:B10'"}

    num_columns = coords['endColumnIndex'] - coords['startColumnIndex']

    series = []
    for i in range(1, num_columns):
        series.append({
            "series": {
                "sourceRange": {
                    "sources": [
                        {
                            "sheetId": sheet_id,
                            "startRowIndex": coords['startRowIndex'],
                            "endRowIndex": coords['endRowIndex'],
                            "startColumnIndex": coords['startColumnIndex'] + i,
                            "endColumnIndex": coords['startColumnIndex'] + i + 1
                        }
                    ]
                }
            },
            "targetAxis": "LEFT_AXIS"
        })

    left_axis = {"position": "LEFT_AXIS"}
    if y_axis_min is not None or y_axis_max is not None:
        left_axis["viewWindowOptions"] = {}
        if y_axis_min is not None:
            left_axis["viewWindowOptions"]["viewWindowMin"] = y_axis_min
        if y_axis_max is not None:
            left_axis["viewWindowOptions"]["viewWindowMax"] = y_axis_max

    basic_chart = {
        "chartType": chart_type.upper(),
        "legendPosition": "RIGHT_LEGEND",
        "axis": [
            {"position": "BOTTOM_AXIS"},
            left_axis
        ],
        "domains": [
            {
                "domain": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": sheet_id,
                                "startRowIndex": coords['startRowIndex'],
                                "endRowIndex": coords['endRowIndex'],
                                "startColumnIndex": coords['startColumnIndex'],
                                "endColumnIndex": coords['startColumnIndex'] + 1
                            }
                        ]
                    }
                }
            }
        ],
        "series": series
    }

    if use_first_row_as_headers:
        basic_chart["headerCount"] = 1

    chart_spec = {
        "title": title or "Chart",
        "basicChart": basic_chart
    }

    request_body = {
        "requests": [
            {
                "addChart": {
                    "chart": {
                        "spec": chart_spec,
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheet_id,
                                    "rowIndex": position_row,
                                    "columnIndex": position_col
                                }
                            }
                        }
                    }
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


@mcp.tool()
def delete_chart(
    spreadsheet_id: str,
    chart_id: int,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Delete a chart from a spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        chart_id: The ID of the chart to delete

    Returns:
        Result of the deletion
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    request_body = {
        "requests": [
            {
                "deleteEmbeddedObject": {
                    "objectId": chart_id
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


# ============================================================================
# CELL FORMATTING OPERATIONS
# ============================================================================

@mcp.tool()
def merge_cells(
    spreadsheet_id: str,
    sheet: str,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
    merge_type: str = "MERGE_ALL",
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Merge cells in a range.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        start_row: Start row index (0-based)
        end_row: End row index (exclusive)
        start_col: Start column index (0-based)
        end_col: End column index (exclusive)
        merge_type: MERGE_ALL, MERGE_COLUMNS, or MERGE_ROWS

    Returns:
        Result of the merge operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    request_body = {
        "requests": [
            {
                "mergeCells": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": start_row,
                        "endRowIndex": end_row,
                        "startColumnIndex": start_col,
                        "endColumnIndex": end_col
                    },
                    "mergeType": merge_type
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


@mcp.tool()
def format_cells(
    spreadsheet_id: str,
    sheet: str,
    range: str,
    background_color: Optional[Dict[str, float]] = None,
    text_color: Optional[Dict[str, float]] = None,
    bold: Optional[bool] = None,
    italic: Optional[bool] = None,
    font_size: Optional[int] = None,
    font_family: Optional[str] = None,
    horizontal_alignment: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Format cells in a range.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        range: Cell range in A1 notation
        background_color: RGB dict for background color (e.g., {"red": 1.0, "green": 0.0, "blue": 0.0})
        text_color: RGB dict for text color
        bold: Make text bold
        italic: Make text italic
        font_size: Font size in points
        font_family: Font family name (e.g., "Courier New", "Arial")
        horizontal_alignment: LEFT, CENTER, or RIGHT

    Returns:
        Result of the formatting operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    coords = parse_a1_notation(range)
    if coords is None:
        return {"error": f"Invalid range format: {range}. Use A1 notation like 'A1:B10'"}

    cell_format = {}
    fields = []

    if background_color:
        cell_format["backgroundColor"] = background_color
        fields.append("backgroundColor")

    text_format = {}
    if text_color:
        text_format["foregroundColor"] = text_color
    if bold is not None:
        text_format["bold"] = bold
    if italic is not None:
        text_format["italic"] = italic
    if font_size is not None:
        text_format["fontSize"] = font_size
    if font_family is not None:
        text_format["fontFamily"] = font_family

    if text_format:
        cell_format["textFormat"] = text_format
        fields.append("textFormat")

    if horizontal_alignment:
        cell_format["horizontalAlignment"] = horizontal_alignment.upper()
        fields.append("horizontalAlignment")

    if not fields:
        return {"error": "No formatting options specified"}

    request_body = {
        "requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": coords['startRowIndex'],
                        "endRowIndex": coords['endRowIndex'],
                        "startColumnIndex": coords['startColumnIndex'],
                        "endColumnIndex": coords['endColumnIndex']
                    },
                    "cell": {
                        "userEnteredFormat": cell_format
                    },
                    "fields": "userEnteredFormat(" + ",".join(fields) + ")"
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


@mcp.tool()
def unmerge_cells(
    spreadsheet_id: str,
    sheet: str,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Unmerge cells in a range.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        start_row: Start row index (0-based)
        end_row: End row index (exclusive)
        start_col: Start column index (0-based)
        end_col: End column index (exclusive)

    Returns:
        Result of the unmerge operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    request_body = {
        "requests": [
            {
                "unmergeCells": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": start_row,
                        "endRowIndex": end_row,
                        "startColumnIndex": start_col,
                        "endColumnIndex": end_col
                    }
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


@mcp.tool()
def set_number_format(
    spreadsheet_id: str,
    sheet: str,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
    format_type: str,
    pattern: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Set number format for a range of cells.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        start_row: Start row index (0-based)
        end_row: End row index (exclusive)
        start_col: Start column index (0-based)
        end_col: End column index (exclusive)
        format_type: NUMBER, CURRENCY, PERCENT, DATE, TIME, etc.
        pattern: Optional custom pattern (e.g., "$#,##0.00")

    Returns:
        Result of the formatting operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    number_format = {
        "type": format_type.upper()
    }
    if pattern:
        number_format["pattern"] = pattern

    request_body = {
        "requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": start_row,
                        "endRowIndex": end_row,
                        "startColumnIndex": start_col,
                        "endColumnIndex": end_col
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": number_format
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat"
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


# ============================================================================
# DATA VALIDATION
# ============================================================================

@mcp.tool()
def add_data_validation(
    spreadsheet_id: str,
    sheet: str,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
    validation_type: str,
    values: Optional[List[str]] = None,
    strict: bool = True,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Add data validation (dropdowns, checkboxes, etc.) to cells.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        start_row: Start row index (0-based)
        end_row: End row index (exclusive)
        start_col: Start column index (0-based)
        end_col: End column index (exclusive)
        validation_type: ONE_OF_LIST, BOOLEAN, NUMBER_BETWEEN, etc.
        values: List of valid values (for ONE_OF_LIST)
        strict: Reject invalid input

    Returns:
        Result of the operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    validation_rule = {
        "condition": {
            "type": validation_type.upper()
        },
        "strict": strict,
        "showCustomUi": True
    }

    if validation_type == "ONE_OF_LIST" and values:
        validation_rule["condition"]["values"] = [{"userEnteredValue": v} for v in values]

    request_body = {
        "requests": [
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": start_row,
                        "endRowIndex": end_row,
                        "startColumnIndex": start_col,
                        "endColumnIndex": end_col
                    },
                    "rule": validation_rule
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


# ============================================================================
# CONDITIONAL FORMATTING
# ============================================================================

@mcp.tool()
def add_conditional_format_rule(
    spreadsheet_id: str,
    sheet: str,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
    condition_type: str,
    condition_values: List[str],
    background_color: Optional[Dict[str, float]] = None,
    text_color: Optional[Dict[str, float]] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Add a conditional formatting rule.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        start_row: Start row index (0-based)
        end_row: End row index (exclusive)
        start_col: Start column index (0-based)
        end_col: End column index (exclusive)
        condition_type: NUMBER_GREATER, NUMBER_LESS, TEXT_CONTAINS, etc.
        condition_values: Values for the condition
        background_color: RGB dict for background color
        text_color: RGB dict for text color

    Returns:
        Result of the operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    cell_format = {}
    if background_color:
        cell_format["backgroundColor"] = background_color
    if text_color:
        cell_format["textFormat"] = {"foregroundColor": text_color}

    boolean_rule = {
        "condition": {
            "type": condition_type.upper(),
            "values": [{"userEnteredValue": v} for v in condition_values]
        },
        "format": cell_format
    }

    request_body = {
        "requests": [
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [
                            {
                                "sheetId": sheet_id,
                                "startRowIndex": start_row,
                                "endRowIndex": end_row,
                                "startColumnIndex": start_col,
                                "endColumnIndex": end_col
                            }
                        ],
                        "booleanRule": boolean_rule
                    },
                    "index": 0
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


# ============================================================================
# FILTERING AND SORTING
# ============================================================================

@mcp.tool()
def sort_range(
    spreadsheet_id: str,
    sheet: str,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
    sort_column: int,
    ascending: bool = True,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Sort a range by a specific column.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet
        start_row: Start row index (0-based)
        end_row: End row index (exclusive)
        start_col: Start column index (0-based)
        end_col: End column index (exclusive)
        sort_column: Column index to sort by (0-based)
        ascending: Sort ascending (True) or descending (False)

    Returns:
        Result of the sort operation
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}

    request_body = {
        "requests": [
            {
                "sortRange": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": start_row,
                        "endRowIndex": end_row,
                        "startColumnIndex": start_col,
                        "endColumnIndex": end_col
                    },
                    "sortSpecs": [
                        {
                            "dimensionIndex": sort_column,
                            "sortOrder": "ASCENDING" if ascending else "DESCENDING"
                        }
                    ]
                }
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


# ============================================================================
# FIND AND REPLACE
# ============================================================================

@mcp.tool()
def find_replace(
    spreadsheet_id: str,
    sheet: Optional[str] = None,
    find: str = "",
    replacement: str = "",
    match_case: bool = False,
    match_entire_cell: bool = False,
    search_by_regex: bool = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Find and replace text in a sheet or entire spreadsheet.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: Optional sheet name (if None, searches entire spreadsheet)
        find: Text to find
        replacement: Replacement text
        match_case: Case-sensitive search
        match_entire_cell: Match entire cell content
        search_by_regex: Use regex for search

    Returns:
        Result with number of replacements made
    """
    sheets_service = ctx.request_context.lifespan_context.sheets_service

    find_replace_spec = {
        "find": find,
        "replacement": replacement,
        "matchCase": match_case,
        "matchEntireCell": match_entire_cell,
        "searchByRegex": search_by_regex
    }

    if sheet:
        sheet_id = get_sheet_id(sheets_service, spreadsheet_id, sheet)
        if sheet_id is None:
            return {"error": f"Sheet '{sheet}' not found"}
        find_replace_spec["sheetId"] = sheet_id

    request_body = {
        "requests": [
            {
                "findReplace": find_replace_spec
            }
        ]
    }

    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body
    ).execute()

    return result


# ============================================================================
# SPREADSHEET MANAGEMENT
# ============================================================================

@mcp.tool()
def create_spreadsheet(
    title: str,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Create a new Google Spreadsheet.

    Args:
        title: The title of the new spreadsheet

    Returns:
        Information about the newly created spreadsheet including its ID
    """
    drive_service = ctx.request_context.lifespan_context.drive_service
    folder_id = ctx.request_context.lifespan_context.folder_id

    file_body = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.spreadsheet',
    }
    if folder_id:
        file_body['parents'] = [folder_id]

    spreadsheet = drive_service.files().create(
        supportsAllDrives=True,
        body=file_body,
        fields='id, name, parents'
    ).execute()

    spreadsheet_id = spreadsheet.get('id')
    parents = spreadsheet.get('parents')

    return {
        'spreadsheetId': spreadsheet_id,
        'title': spreadsheet.get('name', title),
        'folder': parents[0] if parents else 'root',
    }


@mcp.tool()
def list_spreadsheets(ctx: Context = None) -> List[Dict[str, str]]:
    """
    List all spreadsheets in the configured Google Drive folder.

    Returns:
        List of spreadsheets with their ID and title
    """
    drive_service = ctx.request_context.lifespan_context.drive_service
    folder_id = ctx.request_context.lifespan_context.folder_id

    query = "mimeType='application/vnd.google-apps.spreadsheet'"

    if folder_id:
        query += f" and '{folder_id}' in parents"

    results = drive_service.files().list(
        q=query,
        spaces='drive',
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        fields='files(id, name)',
        orderBy='modifiedTime desc'
    ).execute()

    spreadsheets = results.get('files', [])

    return [{'id': sheet['id'], 'title': sheet['name']} for sheet in spreadsheets]


@mcp.tool()
def share_spreadsheet(
    spreadsheet_id: str,
    recipients: List[Dict[str, str]],
    send_notification: bool = True,
    ctx: Context = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Share a Google Spreadsheet with users via email.

    Args:
        spreadsheet_id: The ID of the spreadsheet to share
        recipients: List of dicts with 'email_address' and 'role' (reader/writer/commenter)
        send_notification: Send notification email to users

    Returns:
        Dictionary with lists of successes and failures
    """
    drive_service = ctx.request_context.lifespan_context.drive_service
    successes = []
    failures = []

    for recipient in recipients:
        email_address = recipient.get('email_address')
        role = recipient.get('role', 'writer')

        if not email_address:
            failures.append({'recipient': recipient, 'error': 'Missing email_address'})
            continue

        permission_body = {
            'type': 'user',
            'role': role,
            'emailAddress': email_address
        }

        try:
            permission = drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission_body,
                sendNotificationEmail=send_notification,
                supportsAllDrives=True
            ).execute()

            successes.append({
                'email': email_address,
                'role': role,
                'permissionId': permission.get('id')
            })
        except Exception as e:
            failures.append({
                'email': email_address,
                'role': role,
                'error': str(e)
            })

    return {
        'successes': successes,
        'failures': failures
    }
