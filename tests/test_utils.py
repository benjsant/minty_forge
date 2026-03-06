#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Utils Module Test Script
-------------------------------------
Tests all utility functions (logging, file operations, subprocess).
"""

import sys
from pathlib import Path
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_logging_utils():
    """Test logging functions."""
    print("\n" + "="*60)
    print("🧪 Testing Logging Utils")
    print("="*60)
    
    try:
        from utils import info, success, warn, error, debug, step, header, Logger
        
        # Test global functions
        info("This is an info message")
        success("This is a success message")
        warn("This is a warning message")
        error("This is an error message")
        debug("This is a debug message")
        step("This is a step message")
        header("This is a header")
        
        # Test Logger class
        logger = Logger("TestLogger")
        logger.info("Logger instance test")
        
        print("✅ All logging tests passed")
        return True
    except Exception as e:
        print(f"❌ Logging tests failed: {e}")
        return False


def test_file_utils():
    """Test file utilities."""
    print("\n" + "="*60)
    print("🧪 Testing File Utils")
    print("="*60)
    
    try:
        from utils import (
            load_json, save_json, load_package_list,
            ensure_directory, safe_read_file, safe_write_file,
            get_user_home, ConfigManager, ConfigError
        )
        
        # Test directory creation
        temp_dir = Path(tempfile.gettempdir()) / "mintyforge_test"
        ensure_directory(temp_dir)
        assert temp_dir.exists(), "Directory not created"
        print("✅ ensure_directory works")
        
        # Test JSON operations
        test_data = {"packages": [{"name": "test", "description": "test package"}]}
        test_file = temp_dir / "test.json"
        save_json(test_data, test_file)
        assert test_file.exists(), "JSON file not created"
        print("✅ save_json works")
        
        loaded_data = load_json(test_file)
        assert loaded_data == test_data, "JSON data mismatch"
        print("✅ load_json works")
        
        # Test load_package_list
        packages = load_package_list(test_file)
        assert len(packages) == 1, "Package list incorrect"
        assert packages[0]["name"] == "test", "Package name incorrect"
        print("✅ load_package_list works")
        
        # Test safe file operations
        content = "Hello MintyForge"
        text_file = temp_dir / "test.txt"
        assert safe_write_file(text_file, content), "safe_write_file failed"
        assert safe_read_file(text_file) == content, "Content mismatch"
        print("✅ safe_read_file and safe_write_file work")
        
        # Test get_user_home
        home = get_user_home()
        assert home.exists(), "User home not found"
        print(f"✅ get_user_home works: {home}")
        
        # Test ConfigManager
        config_mgr = ConfigManager(temp_dir)
        config_mgr.save("manager_test.json", {"test": "value"})
        loaded = config_mgr.load("manager_test.json")
        assert loaded["test"] == "value", "ConfigManager data mismatch"
        print("✅ ConfigManager works")
        
        # Test error handling
        try:
            load_json(Path("/nonexistent/file.json"))
            print("❌ Should have raised ConfigError")
            return False
        except ConfigError:
            print("✅ ConfigError properly raised")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        print("✅ All file utils tests passed")
        return True
        
    except Exception as e:
        print(f"❌ File utils tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration between modules."""
    print("\n" + "="*60)
    print("🧪 Testing Integration")
    print("="*60)
    
    try:
        # Test that all utils can be imported together
        from utils import (
            # Subprocess
            run_command, check_package_installed,
            # Logging
            info, success,
            # File
            load_json, ConfigManager
        )
        
        # Test a realistic workflow
        info("Testing realistic workflow...")
        
        # Check if python3 exists (should always be true)
        from utils import check_command_exists
        if check_command_exists("python3"):
            success("python3 command found")
        else:
            print("❌ python3 should exist")
            return False
        
        # Run a simple command
        result = run_command(["echo", "Integration test"])
        if result.success:
            success("Command execution works")
        else:
            print("❌ Command execution failed")
            return False
        
        print("✅ Integration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_config_files():
    """Test with actual config files if they exist."""
    print("\n" + "="*60)
    print("🧪 Testing Real Config Files")
    print("="*60)
    
    try:
        from utils import load_package_list, info
        
        config_files = [
            "configs/install.json",
            "configs/remove.json",
            "configs/flatpak.json"
        ]
        
        for config_file in config_files:
            path = Path(config_file)
            if path.exists():
                packages = load_package_list(path)
                info(f"{path.name}: {len(packages)} packages")
                print(f"   ✅ Successfully loaded {path.name}")
            else:
                info(f"{path.name}: not found (skipped)")
        
        print("✅ Real config files test passed")
        return True
        
    except Exception as e:
        print(f"❌ Real config files test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🛠️  MintyForge Utils Module - Comprehensive Test Suite")
    print("="*70)
    
    all_passed = True
    
    if not test_logging_utils():
        all_passed = False
    
    if not test_file_utils():
        all_passed = False
    
    if not test_integration():
        all_passed = False
    
    if not test_real_config_files():
        all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED! Utils module is working correctly.")
        print("="*70)
        return 0
    else:
        print("❌ SOME TESTS FAILED. Please check the output above.")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
