#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - State Manager (Option G)
--------------------------------------
Persistent state tracking for all MintyForge actions.
Records every installation/removal with its rollback command,
allowing resumption after failure and full rollback.

State is persisted in data/state.json.
"""

import json
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Supported action types
ACTION_APT_INSTALL = "apt_install"
ACTION_APT_REMOVE = "apt_remove"
ACTION_FLATPAK_INSTALL = "flatpak_install"
ACTION_EXTERNAL_INSTALL = "external_install"

VALID_ACTIONS = {
    ACTION_APT_INSTALL,
    ACTION_APT_REMOVE,
    ACTION_FLATPAK_INSTALL,
    ACTION_EXTERNAL_INSTALL,
}

# Default state file location
DEFAULT_STATE_FILE = Path(__file__).parent.parent / "data" / "state.json"


@dataclass
class StateEntry:
    """Represents a single recorded action."""
    id: int
    timestamp: str          # ISO 8601 string
    action: str             # One of VALID_ACTIONS
    target: str             # Package name, app ID, etc.
    success: bool           # Whether the action succeeded
    rollback_cmd: List[str] # Command to undo this action (empty = manual)
    metadata: Dict          # Extra info (description, source, etc.)

    def can_rollback(self) -> bool:
        """Returns True if an automatic rollback command is available."""
        return bool(self.rollback_cmd)

    def to_dict(self) -> Dict:
        """Serialize to dict for JSON storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "StateEntry":
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            action=data["action"],
            target=data["target"],
            success=data["success"],
            rollback_cmd=data.get("rollback_cmd", []),
            metadata=data.get("metadata", {}),
        )


class StateError(Exception):
    """Raised when a state operation fails."""
    pass


class StateManager:
    """
    Persistent state manager for MintyForge.

    Tracks every action performed and allows rollback.
    Thread-safe for use with Flask's threaded mode.

    Usage:
        state = StateManager()
        state.record(
            action="apt_install",
            target="curl",
            success=True,
            rollback_cmd=["apt", "remove", "-y", "curl"],
            metadata={"description": "Downloader"}
        )
        history = state.get_history()
        state.rollback_last()
    """

    def __init__(self, state_file: Optional[Path] = None):
        self.state_file = state_file or DEFAULT_STATE_FILE
        self._lock = threading.Lock()
        self._entries: List[StateEntry] = []
        self._next_id: int = 1
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(
        self,
        action: str,
        target: str,
        success: bool,
        rollback_cmd: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> StateEntry:
        """
        Record an action to the state file.

        Args:
            action:       Action type (use ACTION_* constants)
            target:       Package name or app ID
            success:      Whether the action succeeded
            rollback_cmd: Command list to undo this action (empty = no auto-rollback)
            metadata:     Optional extra info (description, source…)

        Returns:
            The created StateEntry

        Example:
            state.record(
                action=ACTION_APT_INSTALL,
                target="curl",
                success=True,
                rollback_cmd=["apt", "remove", "-y", "curl"],
                metadata={"description": "Downloader"}
            )
        """
        if action not in VALID_ACTIONS:
            raise StateError(f"Unknown action: '{action}'. Valid: {VALID_ACTIONS}")

        entry = StateEntry(
            id=self._next_id,
            timestamp=datetime.now().isoformat(),
            action=action,
            target=target,
            success=success,
            rollback_cmd=rollback_cmd or [],
            metadata=metadata or {},
        )

        with self._lock:
            self._entries.append(entry)
            self._next_id += 1
            self._save()

        return entry

    def get_history(self) -> List[StateEntry]:
        """
        Return all recorded entries, oldest first.

        Returns:
            List of StateEntry objects
        """
        with self._lock:
            return list(self._entries)

    def get_successful(self) -> List[StateEntry]:
        """
        Return only successful entries.

        Returns:
            List of StateEntry where success=True
        """
        with self._lock:
            return [e for e in self._entries if e.success]

    def get_installed_targets(self) -> List[str]:
        """
        Return target names for all successful installs.

        Useful for checking what MintyForge has installed.

        Returns:
            List of target names (str)
        """
        install_actions = {ACTION_APT_INSTALL, ACTION_FLATPAK_INSTALL, ACTION_EXTERNAL_INSTALL}
        with self._lock:
            return [
                e.target for e in self._entries
                if e.action in install_actions and e.success
            ]

    def rollback_last(self) -> Optional[StateEntry]:
        """
        Rollback the last recorded action (if it has a rollback command).

        Removes the entry from state after rollback.

        Returns:
            The entry that was rolled back, or None if nothing to rollback.

        Raises:
            StateError: If the rollback command fails.
        """
        with self._lock:
            if not self._entries:
                return None

            last = self._entries[-1]

            if not last.can_rollback():
                raise StateError(
                    f"No automatic rollback available for '{last.target}' "
                    f"(action: {last.action}). Manual intervention required."
                )

            self._execute_rollback(last)
            self._entries.pop()
            self._save()

        return last

    def rollback_all(self) -> List[StateEntry]:
        """
        Rollback all recorded actions in reverse chronological order.

        Skips entries without rollback commands (logs a warning).
        Clears all rolled-back entries from state afterward.

        Returns:
            List of entries that were successfully rolled back.
        """
        rolled_back = []
        skipped = []

        with self._lock:
            for entry in reversed(self._entries):
                if entry.can_rollback():
                    try:
                        self._execute_rollback(entry)
                        rolled_back.append(entry)
                    except StateError as e:
                        print(f"[WARN] Rollback failed for '{entry.target}': {e}")
                        skipped.append(entry)
                else:
                    print(
                        f"[WARN] Skipping '{entry.target}' (no rollback cmd, "
                        f"action={entry.action})"
                    )
                    skipped.append(entry)

            # Remove only the rolled-back entries
            rolled_back_ids = {e.id for e in rolled_back}
            self._entries = [e for e in self._entries if e.id not in rolled_back_ids]
            self._save()

        return rolled_back

    def clear(self) -> None:
        """
        Clear all state entries without performing any rollback.

        Use with caution — this does NOT undo any actions.
        """
        with self._lock:
            self._entries.clear()
            self._next_id = 1
            self._save()

    def summary(self) -> Dict:
        """
        Return a summary dict for the API / display.

        Returns:
            Dict with counts and last_action info.
        """
        with self._lock:
            total = len(self._entries)
            successful = sum(1 for e in self._entries if e.success)
            failed = total - successful
            rollbackable = sum(1 for e in self._entries if e.can_rollback())
            last = self._entries[-1] if self._entries else None

        return {
            "total_actions": total,
            "successful": successful,
            "failed": failed,
            "rollbackable": rollbackable,
            "last_action": last.to_dict() if last else None,
            "state_file": str(self.state_file),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _execute_rollback(self, entry: StateEntry) -> None:
        """Execute the rollback command for an entry (internal, no lock)."""
        import subprocess
        try:
            result = subprocess.run(
                entry.rollback_cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                raise StateError(
                    f"Rollback command failed (exit {result.returncode}): "
                    f"{' '.join(entry.rollback_cmd)}\n{result.stderr}"
                )
        except subprocess.TimeoutExpired:
            raise StateError(
                f"Rollback timed out for '{entry.target}': "
                f"{' '.join(entry.rollback_cmd)}"
            )
        except FileNotFoundError as e:
            raise StateError(f"Rollback command not found: {e}")

    def _load(self) -> None:
        """Load state from JSON file. Creates the file if it doesn't exist."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.state_file.exists():
            self._entries = []
            self._next_id = 1
            self._save()
            return

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._entries = [StateEntry.from_dict(e) for e in data.get("entries", [])]
            self._next_id = data.get("next_id", len(self._entries) + 1)

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"[WARN] StateManager: corrupted state file ({e}), resetting.")
            self._entries = []
            self._next_id = 1
            self._save()

    def _save(self) -> None:
        """Persist state to JSON file (internal, call within lock)."""
        try:
            data = {
                "version": 1,
                "next_id": self._next_id,
                "entries": [e.to_dict() for e in self._entries],
            }
            # Write atomically via temp file
            tmp = self.state_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp.replace(self.state_file)

        except OSError as e:
            print(f"[ERROR] StateManager: failed to save state: {e}")


# ------------------------------------------------------------------
# Convenience factory — shared singleton per process
# ------------------------------------------------------------------
_default_manager: Optional[StateManager] = None
_manager_lock = threading.Lock()


def get_state_manager(state_file: Optional[Path] = None) -> StateManager:
    """
    Get (or create) the default StateManager singleton.

    Using this ensures all scripts share the same state file.

    Args:
        state_file: Override default path (mainly for tests)

    Returns:
        StateManager instance
    """
    global _default_manager
    with _manager_lock:
        if _default_manager is None or state_file is not None:
            _default_manager = StateManager(state_file)
        return _default_manager
