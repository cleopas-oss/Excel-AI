from typing import Dict, Tuple, List


class ToolRegistry:
    """
    Central source of truth for all Excel MCP tools.
    Prevents hallucinated tool calls and enforces schemas.
    """

    TOOL_SCHEMAS: Dict[str, Dict] = {

        # --- Workbook ---
        "create_workbook": {"required": ["filepath"]},

        # ✅ NEW: explicit workbook rename (file-level, not worksheet-level)
        "rename_workbook": {
            "required": ["old_filepath", "new_filepath"]
        },

        "create_worksheet": {"required": ["filepath", "sheet_name"]},

        # ✅ NEW: batch worksheet creation (maps to natural language)
        "create_multiple_worksheets": {
            "required": ["filepath", "sheet_names"]
        },

        "get_workbook_metadata": {"required": ["filepath"]},

        # --- Data ---
        "write_data_to_excel": {
            "required": ["filepath", "sheet_name", "data"]
        },
        "read_data_from_excel": {
            "required": ["filepath", "sheet_name"]
        },

        # --- Formatting ---
        "format_range": {
            "required": ["filepath", "sheet_name", "start_cell"]
        },
        "merge_cells": {
            "required": ["filepath", "sheet_name", "start_cell", "end_cell"]
        },
        "unmerge_cells": {
            "required": ["filepath", "sheet_name", "start_cell", "end_cell"]
        },
        "get_merged_cells": {
            "required": ["filepath", "sheet_name"]
        },

        # --- Formulas ---
        "apply_formula": {
            "required": ["filepath", "sheet_name", "cell", "formula"]
        },
        "validate_formula_syntax": {
            "required": ["filepath", "sheet_name", "cell", "formula"]
        },

        # --- Charts ---
        "create_chart": {
            "required": [
                "filepath",
                "sheet_name",
                "data_range",
                "chart_type",
                "target_cell",
            ]
        },

        # --- Pivot ---
        "create_pivot_table": {
            "required": [
                "filepath",
                "sheet_name",
                "data_range",
                "target_cell",
                "rows",
                "values",
            ]
        },

        # --- Tables ---
        "create_table": {
            "required": ["filepath", "sheet_name", "data_range"]
        },

        # --- Worksheet ops ---
        "copy_worksheet": {
            "required": ["filepath", "source_sheet", "target_sheet"]
        },
        "delete_worksheet": {
            "required": ["filepath", "sheet_name"]
        },
        "rename_worksheet": {
            "required": ["filepath", "old_name", "new_name"]
        },

        # --- Range ops ---
        "copy_range": {
            "required": [
                "filepath",
                "sheet_name",
                "source_start",
                "source_end",
                "target_start",
            ]
        },
        "delete_range": {
            "required": ["filepath", "sheet_name", "start_cell", "end_cell"]
        },
        "validate_excel_range": {
            "required": ["filepath", "sheet_name", "start_cell"]
        },
        "get_data_validation_info": {
            "required": ["filepath", "sheet_name"]
        },

        # --- Rows/Columns ---
        "insert_rows": {
            "required": ["filepath", "sheet_name", "start_row"]
        },
        "insert_columns": {
            "required": ["filepath", "sheet_name", "start_col"]
        },
        "delete_sheet_rows": {
            "required": ["filepath", "sheet_name", "start_row"]
        },
        "delete_sheet_columns": {
            "required": ["filepath", "sheet_name", "start_col"]
        },
    }

    def get_tool_names(self) -> List[str]:
        return list(self.TOOL_SCHEMAS.keys())

    def validate_tool_call(self, tool_name: str, arguments: Dict) -> Tuple[bool, str]:

        if tool_name not in self.TOOL_SCHEMAS:
            return False, f"Unknown tool: {tool_name}"

        required = self.TOOL_SCHEMAS[tool_name]["required"]

        missing = [
            field for field in required
            if field not in arguments or arguments[field] is None
        ]

        if missing:
            return False, f"Missing required fields: {missing}"

        return True, ""
