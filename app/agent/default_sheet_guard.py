REQUIRES_SHEET = {
    "write_data_to_excel",
    "read_data_from_excel",
    "format_range",
    "merge_cells",
    "unmerge_cells",
    "apply_formula",
    "create_chart",
    "create_table",
}


def tool_requires_sheet(tool_name: str) -> bool:
    return tool_name in REQUIRES_SHEET
