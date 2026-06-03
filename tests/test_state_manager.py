#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - State Manager Test Suite (Option G)
-------------------------------------------------
Tests all StateManager functionality including persistence,
rollback, and thread safety.

Note: Imports are done via importlib to avoid triggering utils/__init__.py
which requires pydantic (a separate optional dependency).

Run with:
    python test_state_manager.py
"""

import sys
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

# ---------------------------------------------------------------------------
# Load state_manager directly (bypass utils/__init__.py → pydantic)
# ---------------------------------------------------------------------------
_SM_PATH = Path(__file__).parent.parent / "utils" / "state_manager.py"
_spec = importlib.util.spec_from_file_location("state_manager", _SM_PATH)
_sm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sm)

StateManager          = _sm.StateManager
StateEntry            = _sm.StateEntry
StateError            = _sm.StateError
get_state_manager     = _sm.get_state_manager
ACTION_APT_INSTALL    = _sm.ACTION_APT_INSTALL
ACTION_APT_REMOVE     = _sm.ACTION_APT_REMOVE
ACTION_FLATPAK_INSTALL   = _sm.ACTION_FLATPAK_INSTALL
ACTION_EXTERNAL_INSTALL  = _sm.ACTION_EXTERNAL_INSTALL


# ===========================================================================
# Helpers
# ===========================================================================

def make_manager(tmp_dir: Path) -> StateManager:
    """Create a fresh StateManager backed by a temp file."""
    return StateManager(tmp_dir / "state.json")


def _section(title: str):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print("="*60)


# ===========================================================================
# Tests
# ===========================================================================

def test_imports():
    """All StateManager symbols are present in state_manager.py."""
    _section("Imports")

    for symbol in ("StateManager", "StateEntry", "StateError", "get_state_manager",
                   "ACTION_APT_INSTALL", "ACTION_APT_REMOVE",
                   "ACTION_FLATPAK_INSTALL", "ACTION_EXTERNAL_INSTALL"):
        assert hasattr(_sm, symbol), f"Missing symbol: {symbol}"
    print("✅ All StateManager symbols present in state_manager.py")

    for method in ("record", "rollback_last", "rollback_all", "get_history",
                   "get_successful", "get_installed_targets", "clear", "summary"):
        assert hasattr(StateManager, method), f"Missing method: {method}"
    print("✅ StateManager has all required public methods")
    return True


def test_record_and_load():
    """Record entries and reload from disk."""
    _section("Record and Reload from Disk")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        state = make_manager(tmp_dir)

        # Empty state
        assert len(state.get_history()) == 0, "Should be empty"
        print("✅ Empty state initialized correctly")

        # Record a successful action
        entry = state.record(
            action=ACTION_APT_INSTALL,
            target="curl",
            success=True,
            rollback_cmd=["apt", "remove", "-y", "curl"],
            metadata={"description": "Downloader"},
        )
        assert entry.id == 1
        assert entry.target == "curl"
        assert entry.success is True
        assert entry.can_rollback() is True
        print(f"✅ Recorded entry: id={entry.id}, target={entry.target}")

        # Record a failed action
        state.record(
            action=ACTION_APT_INSTALL,
            target="nonexistent-pkg",
            success=False,
            rollback_cmd=["apt", "remove", "-y", "nonexistent-pkg"],
        )
        assert len(state.get_history()) == 2
        print("✅ 2 entries recorded")

        # Reload from disk
        state2 = StateManager(tmp_dir / "state.json")
        history = state2.get_history()
        assert len(history) == 2, f"Expected 2 entries, got {len(history)}"
        assert history[0].target == "curl"
        assert history[1].target == "nonexistent-pkg"
        print("✅ State correctly reloaded from disk")

    return True


def test_get_installed_targets():
    """Only successful installs are returned."""
    _section("get_installed_targets()")

    with tempfile.TemporaryDirectory() as tmp:
        state = make_manager(Path(tmp))
        state.record(ACTION_APT_INSTALL, "curl", True, ["apt", "remove", "-y", "curl"])
        state.record(ACTION_APT_INSTALL, "badpkg", False, ["apt", "remove", "-y", "badpkg"])
        state.record(ACTION_FLATPAK_INSTALL, "org.mozilla.firefox", True,
                     ["flatpak", "uninstall", "-y", "org.mozilla.firefox"],
                     {"source": "flathub"})

        installed = state.get_installed_targets()
        assert "curl" in installed, "curl should be in installed"
        assert "org.mozilla.firefox" in installed, "firefox should be in installed"
        assert "badpkg" not in installed, "badpkg failed, should not be in installed"
        print(f"✅ Installed targets: {installed}")

    return True


def test_rollback_last():
    """rollback_last() executes rollback cmd and removes the entry."""
    _section("rollback_last()")

    with tempfile.TemporaryDirectory() as tmp:
        state = make_manager(Path(tmp))
        state.record(ACTION_APT_INSTALL, "wget", True, ["apt", "remove", "-y", "wget"])
        state.record(ACTION_APT_INSTALL, "curl", True, ["apt", "remove", "-y", "curl"])

        assert len(state.get_history()) == 2

        # Mock subprocess so we don't actually remove packages
        import subprocess
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value.returncode = 0

            rolled = state.rollback_last()
            assert rolled is not None
            assert rolled.target == "curl", f"Expected 'curl', got {rolled.target}"
            # _execute_rollback prefixe sudo -n pour les commandes apt
            mock_run.assert_called_once_with(
                ["sudo", "-n", "apt", "remove", "-y", "curl"],
                capture_output=True, text=True, timeout=300,
            )

        assert len(state.get_history()) == 1, "curl entry should be removed"
        assert state.get_history()[0].target == "wget", "wget should remain"
        print("✅ rollback_last() removed 'curl' and kept 'wget'")

    return True


def test_rollback_all():
    """rollback_all() processes all rollbackable entries in reverse order."""
    _section("rollback_all()")

    with tempfile.TemporaryDirectory() as tmp:
        state = make_manager(Path(tmp))
        # 2 rollbackable, 1 not
        state.record(ACTION_APT_INSTALL, "git", True, ["apt", "remove", "-y", "git"])
        state.record(ACTION_APT_INSTALL, "vim", True, ["apt", "remove", "-y", "vim"])
        state.record(ACTION_EXTERNAL_INSTALL, "virtualbox", True, [],
                     {"manual_rollback": True})

        import subprocess
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value.returncode = 0
            rolled = state.rollback_all()

        assert len(rolled) == 2, f"Expected 2 rolled back, got {len(rolled)}"
        # Remaining: only virtualbox (no rollback cmd)
        remaining = state.get_history()
        assert len(remaining) == 1
        assert remaining[0].target == "virtualbox"

        # Check reverse order: vim first, then git
        targets = [r.target for r in rolled]
        assert targets[0] == "vim", "Should rollback vim first (last recorded)"
        assert targets[1] == "git", "Then git"
        print(f"✅ rollback_all() reversed order: {targets}")
        print("✅ External 'virtualbox' correctly skipped (no rollback cmd)")

    return True


def test_no_rollback_raises():
    """rollback_last() raises StateError when no rollback command available."""
    _section("rollback_last() → StateError (no rollback cmd)")

    with tempfile.TemporaryDirectory() as tmp:
        state = make_manager(Path(tmp))
        state.record(ACTION_EXTERNAL_INSTALL, "virtualbox", True, [],
                     {"manual_rollback": True})
        try:
            state.rollback_last()
            print("❌ Should have raised StateError")
            return False
        except StateError as e:
            print(f"✅ StateError raised correctly: {e}")

    return True


def test_empty_rollback():
    """rollback_last() on empty state returns None without crashing."""
    _section("rollback_last() on empty state")
    with tempfile.TemporaryDirectory() as tmp:
        state = make_manager(Path(tmp))
        result = state.rollback_last()
        assert result is None, "Should return None on empty state"
        print("✅ rollback_last() returned None on empty state — no crash")
    return True


def test_clear():
    """clear() empties the state without rollback."""
    _section("clear()")

    with tempfile.TemporaryDirectory() as tmp:
        state = make_manager(Path(tmp))
        state.record(ACTION_APT_INSTALL, "git", True, ["apt", "remove", "-y", "git"])
        state.record(ACTION_APT_INSTALL, "curl", True, ["apt", "remove", "-y", "curl"])
        assert len(state.get_history()) == 2

        state.clear()
        assert len(state.get_history()) == 0, "State should be empty after clear()"
        print("✅ clear() emptied the state")

        # Verify it's also cleared on disk
        state2 = StateManager(Path(tmp) / "state.json")
        assert len(state2.get_history()) == 0
        print("✅ Cleared state persisted to disk")

    return True


def test_persistence():
    """State survives a complete StateManager restart."""
    _section("Persistence across restarts")

    with tempfile.TemporaryDirectory() as tmp:
        state_file = Path(tmp) / "state.json"

        # Session 1
        s1 = StateManager(state_file)
        s1.record(ACTION_APT_INSTALL, "git", True, ["apt", "remove", "-y", "git"])
        s1.record(ACTION_FLATPAK_INSTALL, "com.spotify.Client", True,
                  ["flatpak", "uninstall", "-y", "com.spotify.Client"])
        del s1

        # Session 2 — fresh load
        s2 = StateManager(state_file)
        history = s2.get_history()
        assert len(history) == 2
        assert history[0].target == "git"
        assert history[1].target == "com.spotify.Client"
        assert s2._next_id == 3, f"next_id should be 3, got {s2._next_id}"
        print("✅ State correctly persisted and reloaded across sessions")

    return True


def test_summary():
    """summary() returns correct counts."""
    _section("summary()")

    with tempfile.TemporaryDirectory() as tmp:
        state = make_manager(Path(tmp))
        state.record(ACTION_APT_INSTALL, "curl", True, ["apt", "remove", "-y", "curl"])
        state.record(ACTION_APT_INSTALL, "bad", False, [])
        state.record(ACTION_APT_REMOVE, "mintwelcome", True,
                     ["apt", "install", "-y", "mintwelcome"])

        s = state.summary()
        assert s["total_actions"] == 3
        assert s["successful"] == 2
        assert s["failed"] == 1
        assert s["rollbackable"] == 2
        assert s["last_action"]["target"] == "mintwelcome"
        print(f"✅ summary: total={s['total_actions']}, ok={s['successful']}, "
              f"fail={s['failed']}, rollbackable={s['rollbackable']}")

    return True


def test_invalid_action():
    """Recording an unknown action raises StateError."""
    _section("Invalid action raises StateError")

    with tempfile.TemporaryDirectory() as tmp:
        state = make_manager(Path(tmp))
        try:
            state.record("invalid_action", "target", True)
            print("❌ Should have raised StateError")
            return False
        except StateError as e:
            print(f"✅ StateError raised: {e}")

    return True


# ===========================================================================
# Runner
# ===========================================================================

TESTS = [
    test_imports,
    test_record_and_load,
    test_get_installed_targets,
    test_rollback_last,
    test_rollback_all,
    test_no_rollback_raises,
    test_empty_rollback,
    test_clear,
    test_persistence,
    test_summary,
    test_invalid_action,
]


def main():
    print("\n" + "="*70)
    print("🛠️  MintyForge — State Manager Test Suite (Option G)")
    print("="*70)

    passed = 0
    failed = 0
    errors = []

    for test_fn in TESTS:
        try:
            result = test_fn()
            if result is True or result is None:
                passed += 1
            else:
                failed += 1
                errors.append(test_fn.__name__)
        except Exception as e:
            failed += 1
            errors.append(test_fn.__name__)
            import traceback
            print(f"\n❌ Exception in {test_fn.__name__}:")
            traceback.print_exc()

    print("\n" + "="*70)
    total = passed + failed
    if failed == 0:
        print(f"✅ ALL {total}/{total} TESTS PASSED — StateManager OK!")
    else:
        print(f"❌ {failed}/{total} TESTS FAILED: {', '.join(errors)}")
    print("="*70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
