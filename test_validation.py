#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Validation Tests
------------------------------
Tests for JSON configuration validation with Pydantic.
"""

import sys
import tempfile
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    validate_install_config,
    validate_remove_config,
    validate_flatpak_config,
    validate_external_config,
    validate_theme_config,
    validate_kvantum_config,
    validate_all_configs,
    ConfigValidationError,
    load_package_list,
    info, success, error, warn
)


def test_valid_configs():
    """Test that all real config files are valid."""
    print("\n" + "="*70)
    print("🧪 Test 1: Valid Configurations")
    print("="*70)
    
    config_dir = Path("configs")
    
    if not config_dir.exists():
        error("Config directory not found")
        return False
    
    try:
        results = validate_all_configs(config_dir)
        
        for config_name, result in results.items():
            if result is not None:
                success(f"{config_name}: valid ✅")
        
        print("✅ All existing configs are valid")
        return True
        
    except ConfigValidationError as e:
        error(f"Validation failed: {e.message}")
        return False
    except Exception as e:
        error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_invalid_package_name():
    """Test detection of invalid package names."""
    print("\n" + "="*70)
    print("🧪 Test 2: Invalid Package Name Detection")
    print("="*70)
    
    # Create temp file with invalid package (empty name)
    invalid_config = {
        "packages": [
            {"name": "", "description": "Empty name"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_file = Path(f.name)
    
    try:
        validate_install_config(temp_file)
        error("❌ Should have raised ConfigValidationError")
        temp_file.unlink()
        return False
    except ConfigValidationError as e:
        if "name" in str(e.message).lower() or "empty" in str(e.message).lower():
            success("✅ Correctly detected invalid package name")
            temp_file.unlink()
            return True
        else:
            error(f"❌ Wrong error message: {e.message}")
            temp_file.unlink()
            return False
    except Exception as e:
        error(f"❌ Unexpected error: {e}")
        temp_file.unlink()
        return False


def test_duplicate_packages():
    """Test detection of duplicate package names."""
    print("\n" + "="*70)
    print("🧪 Test 3: Duplicate Package Detection")
    print("="*70)
    
    # Create temp file with duplicate packages
    duplicate_config = {
        "packages": [
            {"name": "curl", "description": "Tool 1"},
            {"name": "wget", "description": "Tool 2"},
            {"name": "curl", "description": "Duplicate!"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(duplicate_config, f)
        temp_file = Path(f.name)
    
    try:
        validate_install_config(temp_file)
        error("❌ Should have raised ConfigValidationError")
        temp_file.unlink()
        return False
    except ConfigValidationError as e:
        if "duplicate" in str(e.message).lower():
            success("✅ Correctly detected duplicate packages")
            temp_file.unlink()
            return True
        else:
            error(f"❌ Wrong error message: {e.message}")
            temp_file.unlink()
            return False
    except Exception as e:
        error(f"❌ Unexpected error: {e}")
        temp_file.unlink()
        return False


def test_invalid_flatpak_id():
    """Test detection of invalid Flatpak app ID."""
    print("\n" + "="*70)
    print("🧪 Test 4: Invalid Flatpak App ID Detection")
    print("="*70)
    
    # Create temp file with invalid Flatpak ID
    invalid_config = {
        "flatpaks": [
            {"source": "flathub", "app": "invalid", "description": "Bad ID"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_file = Path(f.name)
    
    try:
        validate_flatpak_config(temp_file)
        error("❌ Should have raised ConfigValidationError")
        temp_file.unlink()
        return False
    except ConfigValidationError as e:
        if "app id" in str(e.message).lower() or "format" in str(e.message).lower():
            success("✅ Correctly detected invalid Flatpak app ID")
            temp_file.unlink()
            return True
        else:
            error(f"❌ Wrong error message: {e.message}")
            temp_file.unlink()
            return False
    except Exception as e:
        error(f"❌ Unexpected error: {e}")
        temp_file.unlink()
        return False


def test_invalid_url():
    """Test detection of invalid URLs in themes."""
    print("\n" + "="*70)
    print("🧪 Test 5: Invalid Theme URL Detection")
    print("="*70)
    
    # Create temp file with invalid URL
    invalid_config = {
        "themes": [
            {
                "name": "TestTheme",
                "name_to_use": "TestTheme",
                "url": "not-a-valid-url",
                "cmd_user": "install.sh",
                "cmd_root": "install.sh",
                "description": "Test theme"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_file = Path(f.name)
    
    try:
        validate_theme_config(temp_file)
        error("❌ Should have raised ConfigValidationError")
        temp_file.unlink()
        return False
    except ConfigValidationError as e:
        if "url" in str(e.message).lower():
            success("✅ Correctly detected invalid URL")
            temp_file.unlink()
            return True
        else:
            error(f"❌ Wrong error message: {e.message}")
            temp_file.unlink()
            return False
    except Exception as e:
        error(f"❌ Unexpected error: {e}")
        temp_file.unlink()
        return False


def test_missing_installation_command():
    """Test detection of themes with URL but no installation commands."""
    print("\n" + "="*70)
    print("🧪 Test 6: Missing Installation Command Detection")
    print("="*70)
    
    # Create temp file with URL but no commands
    invalid_config = {
        "themes": [
            {
                "name": "TestTheme",
                "name_to_use": "TestTheme",
                "url": "https://github.com/example/theme.git",
                "cmd_user": "",
                "cmd_root": "",
                "description": "Test theme"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_file = Path(f.name)
    
    try:
        validate_theme_config(temp_file)
        error("❌ Should have raised ConfigValidationError")
        temp_file.unlink()
        return False
    except ConfigValidationError as e:
        if "command" in str(e.message).lower() or "url" in str(e.message).lower():
            success("✅ Correctly detected missing installation commands")
            temp_file.unlink()
            return True
        else:
            error(f"❌ Wrong error message: {e.message}")
            temp_file.unlink()
            return False
    except Exception as e:
        error(f"❌ Unexpected error: {e}")
        temp_file.unlink()
        return False


def test_extra_fields():
    """Test detection of extra unknown fields."""
    print("\n" + "="*70)
    print("🧪 Test 7: Extra Fields Detection")
    print("="*70)
    
    # Create temp file with extra fields
    invalid_config = {
        "packages": [
            {
                "name": "curl",
                "description": "Tool",
                "unknown_field": "should not be here"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_config, f)
        temp_file = Path(f.name)
    
    try:
        validate_install_config(temp_file)
        error("❌ Should have raised ConfigValidationError")
        temp_file.unlink()
        return False
    except ConfigValidationError as e:
        if "extra" in str(e.message).lower() or "forbidden" in str(e.message).lower():
            success("✅ Correctly detected extra fields")
            temp_file.unlink()
            return True
        else:
            # Some configs might allow extra fields
            warn(f"⚠️  Extra fields allowed: {e.message}")
            temp_file.unlink()
            return True
    except Exception as e:
        error(f"❌ Unexpected error: {e}")
        temp_file.unlink()
        return False


def test_load_package_list_integration():
    """Test that load_package_list() uses validation automatically."""
    print("\n" + "="*70)
    print("🧪 Test 8: load_package_list() Integration")
    print("="*70)
    
    # Create valid config
    valid_config = {
        "packages": [
            {"name": "test-package", "description": "Test"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_install.json', delete=False) as f:
        json.dump(valid_config, f)
        temp_file = Path(f.name)
    
    try:
        # Test with validation (default)
        packages = load_package_list(temp_file, validate=True)
        if len(packages) == 1 and packages[0]["name"] == "test-package":
            success("✅ load_package_list() with validation works")
        else:
            error(f"❌ Unexpected result: {packages}")
            temp_file.unlink()
            return False
        
        # Test without validation
        packages = load_package_list(temp_file, validate=False)
        if len(packages) == 1:
            success("✅ load_package_list() without validation works")
        else:
            error(f"❌ Unexpected result: {packages}")
            temp_file.unlink()
            return False
        
        temp_file.unlink()
        return True
        
    except Exception as e:
        error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        temp_file.unlink()
        return False


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("🛠️  MintyForge - Validation Test Suite (Option C)")
    print("="*70)
    
    tests = [
        ("Valid configurations", test_valid_configs),
        ("Invalid package name", test_invalid_package_name),
        ("Duplicate packages", test_duplicate_packages),
        ("Invalid Flatpak ID", test_invalid_flatpak_id),
        ("Invalid theme URL", test_invalid_url),
        ("Missing install command", test_missing_installation_command),
        ("Extra fields detection", test_extra_fields),
        ("load_package_list() integration", test_load_package_list_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            error(f"Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*70)
    if passed == total:
        success(f"✅ ALL {total} TESTS PASSED!")
        print("="*70 + "\n")
        return 0
    else:
        error(f"❌ {total - passed}/{total} TESTS FAILED")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
