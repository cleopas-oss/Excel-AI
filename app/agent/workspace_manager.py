import os
import json
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict
import difflib

WORKSPACE_ROOT = Path("/excel_files")
STATE_FILE = WORKSPACE_ROOT / ".workspace_state.json"
LOG_FILE = WORKSPACE_ROOT / ".execution_log.jsonl"


class WorkspaceError(Exception):
    pass


class RecoverableWorkspaceError(WorkspaceError):
    pass


class FatalWorkspaceError(WorkspaceError):
    pass


class WorkspaceManager:

    def __init__(self):
        WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self.state = self._load_state()
        self._reconcile_filesystem()

    async def acquire_lock(self):
        await self._lock.acquire()

    def release_lock(self):
        if self._lock.locked():
            self._lock.release()

    # ---------------------------
    # State persistence
    # ---------------------------

    def _empty_state(self) -> Dict:
        return {
            "files": {},
            "active_file": None,
        }

    def _load_state(self) -> Dict:
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._empty_state()

        return self._empty_state()

    def _save_state(self):
        tmp = STATE_FILE.with_suffix(".tmp")

        with open(tmp, "w") as f:
            json.dump(self.state, f, indent=2)

        os.replace(tmp, STATE_FILE)

    # ---------------------------
    # Filesystem reconciliation
    # ---------------------------

    def _reconcile_filesystem(self):
        """
        Sync registry with actual disk.
        Auto-register any Excel files that exist.
        """

        existing = {p.name: str(p) for p in WORKSPACE_ROOT.glob("*.xlsx")}

        # Remove missing files
        for canon in list(self.state["files"].keys()):
            if canon not in existing:
                del self.state["files"][canon]

        # Add unregistered files
        for canon, path in existing.items():
            if canon not in self.state["files"]:
                self.state["files"][canon] = path

        self._save_state()

    # ---------------------------
    # File registration
    # ---------------------------

    def register_file(self, filename: str) -> Path:
        canonical = self._canonical_name(filename)
        full_path = WORKSPACE_ROOT / canonical

        self.state["files"][canonical] = str(full_path)
        self.state["active_file"] = canonical
        self._save_state()

        return full_path

    def rename_file(self, old_name: str, new_name: str) -> Path:
        # Convert absolute path to filename if needed
        old_name = Path(old_name).name  # Extract filename from path
        new_name = Path(new_name).name  # Extract filename from path

        old_canon = self._canonical_name(old_name)  # Normalize old filename
        new_canon = self._canonical_name(new_name)  # Normalize new filename

        if old_canon not in self.state["files"]:
            raise RecoverableWorkspaceError(
                f"File not tracked: {old_name}"
            )

        old_path = Path(self.state["files"][old_canon])  # Get current file path
        new_path = WORKSPACE_ROOT / new_canon  # Build new file path

        if not old_path.exists():
            raise FatalWorkspaceError(
                f"Physical file missing: {old_path}"
            )

        os.rename(old_path, new_path)  # Rename file on disk

        del self.state["files"][old_canon]  # Remove old entry
        self.state["files"][new_canon] = str(new_path)  # Add new entry
        self.state["active_file"] = new_canon  # Update active file

        self._save_state()  # Persist changes

        return new_path  # Return new path


    # ---------------------------
    # Resolution
    # ---------------------------

    def resolve_file(self, filename: Optional[str]) -> Path:

        # Normalize input: strip directory if full path was passed
        if filename:
            filename = Path(filename).name

        self._reconcile_filesystem()

        if not filename:
            active = self.get_active_file()
            if active:
                return active
            raise RecoverableWorkspaceError("No active workbook available")

        canon = self._canonical_name(filename)

        existing_files = {p.name.lower(): p for p in WORKSPACE_ROOT.glob("*.xlsx")}

        if canon.lower() not in existing_files:
            suggestion = self._suggest_filename(canon)
            msg = f"File '{filename}' not found"
            if suggestion:
                msg += f". Did you mean '{suggestion}'?"
            raise RecoverableWorkspaceError(msg)

        real_path = existing_files[canon.lower()]

        self.state["files"][real_path.name] = str(real_path)
        self.state["active_file"] = real_path.name
        self._save_state()

        return real_path



    def _canonical_name(self, filename: str) -> str:
        filename = filename.strip()
        filename = filename.replace("  ", " ")

        if not filename.lower().endswith(".xlsx"):
            filename += ".xlsx"

        return filename


    def _suggest_filename(self, name: str) -> Optional[str]:
        matches = difflib.get_close_matches(
            name,
            self.state["files"].keys(),
            n=1,
            cutoff=0.6,
        )
        return matches[0] if matches else None

    # ---------------------------
    # Logging
    # ---------------------------

    def log_execution(
        self,
        user_command: str,
        tool_name: str,
        filepath: Optional[str],
        args: Dict,
        result: str,
    ):
        entry = {
            "timestamp": time.time(),
            "command": user_command,
            "tool": tool_name,
            "file": filepath,
            "args": args,
            "result": result,
        }

        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    # ---------------------------
    # Active file
    # ---------------------------

    def get_active_file(self) -> Optional[Path]:
        active = self.state.get("active_file")
        if not active:
            return None
        return Path(self.state["files"][active])


workspace = WorkspaceManager()

