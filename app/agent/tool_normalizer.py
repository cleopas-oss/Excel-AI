from typing import Dict
from pathlib import Path
from agent.workspace_manager import workspace, WorkspaceError


ALIAS_MAP = {
    "workbook": "filepath",
    "workbook_name": "filepath",
    "file": "filepath",

    "old_file": "old_filepath",
    "new_file": "new_filepath",

    "worksheet": "sheet_name",
    "worksheet_name": "sheet_name",
    "sheet": "sheet_name",

    "sheets": "sheet_names",
    "worksheets": "sheet_names",
    "names": "sheet_names",
}


def normalize_arguments(args: Dict, agent_state, tool_name: str = None) -> Dict:
    """
    Normalize argument keys and resolve workspace files.

    Important:
    create_workbook skips file resolution so new files can be created.
    """

    normalized = {}

    # ---------------------------
    # Canonicalize argument keys
    # ---------------------------

    for key, value in args.items():
        canonical_key = ALIAS_MAP.get(key, key)
        normalized[canonical_key] = value

    # ---------------------------
    # Normalize sheet list input
    # ---------------------------

    if "sheet_names" in normalized:

        if isinstance(normalized["sheet_names"], str):
            normalized["sheet_names"] = [
                name.strip()
                for name in normalized["sheet_names"].split(",")
                if name.strip()
            ]

        cleaned = []
        for name in normalized["sheet_names"]:
            name = str(name).strip("[]'\" ")
            if name:
                cleaned.append(name)

        normalized["sheet_names"] = cleaned

    # ---------------------------
    # Resolve primary file
    # ---------------------------

    if tool_name != "create_workbook" and "filepath" in normalized:

        filepath_value = normalized["filepath"]

        if filepath_value is not None:
            normalized["filepath"] = str(
                workspace.resolve_file(filepath_value)
            )

    # ---------------------------
    # Resolve rename inputs
    # ---------------------------

    if "old_filepath" in normalized:

        old_value = normalized["old_filepath"]

        if old_value is not None:
            normalized["old_filepath"] = str(
                workspace.resolve_file(old_value)
            )

    if "new_filepath" in normalized:

        new_value = normalized["new_filepath"]

        if new_value is not None:
            # Only canonicalize — DO NOT resolve
            # This is a new name that may not exist yet
            new_value = Path(new_value).name
            normalized["new_filepath"] = workspace._canonical_name(new_value)

    return normalized







