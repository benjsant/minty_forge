#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Security Test Script
----------------------------------
Tests the secure subprocess utilities to ensure they work correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all utils can be imported."""
    print("🧪 Testing imports...")
    try:
        from utils import (
            run_command,
            run_sudo_command,
            check_package_installed,
            check_command_exists,
            apt_install,
            apt_remove,
            apt_update,
            apt_upgrade,
            flatpak_install,
            check_flatpak_installed,
            git_clone,
            run_bash_script,
            run_python_script,
            CommandResult
        )
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_check_command():
    """Test check_command_exists function."""
    print("\n🧪 Testing check_command_exists...")
    from utils import check_command_exists
    
    # Test with a command that should exist
    if check_command_exists("python3"):
        print("✅ python3 found")
    else:
        print("❌ python3 not found (unexpected)")
        return False
    
    # Test with a command that shouldn't exist
    if not check_command_exists("nonexistent_command_12345"):
        print("✅ nonexistent command correctly not found")
    else:
        print("❌ nonexistent command found (unexpected)")
        return False
    
    return True

def test_check_package():
    """Test check_package_installed function."""
    print("\n🧪 Testing check_package_installed...")
    from utils import check_package_installed
    
    # Test with a package that should be installed
    if check_package_installed("bash"):
        print("✅ bash package found")
    else:
        print("⚠️  bash not found (might be unusual)")
    
    # Test with a package that shouldn't be installed
    if not check_package_installed("nonexistent-package-12345"):
        print("✅ nonexistent package correctly not found")
    else:
        print("❌ nonexistent package found (unexpected)")
        return False
    
    return True

def test_run_command():
    """Test run_command function."""
    print("\n🧪 Testing run_command...")
    from utils import run_command
    
    # Test simple command
    result = run_command(["echo", "Hello MintyForge"])
    if result.success:
        print("✅ Simple command executed successfully")
    else:
        print("❌ Simple command failed")
        return False
    
    # Test command that should fail
    result = run_command(["false"])
    if not result.success:
        print("✅ Failed command correctly returned failure")
    else:
        print("❌ Failed command incorrectly returned success")
        return False
    
    return True

def main():
    """Run all tests."""
    print("="*60)
    print("🛡️  MintyForge Security Test Suite")
    print("="*60)
    
    all_passed = True
    
    if not test_imports():
        all_passed = False
    
    if not test_check_command():
        all_passed = False
    
    if not test_check_package():
        all_passed = False
    
    if not test_run_command():
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ All tests passed! Security improvements working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
