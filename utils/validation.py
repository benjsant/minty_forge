#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - JSON Configuration Validation
-------------------------------------------
Functions for validating JSON configuration files using Pydantic schemas.
Provides fail-fast validation with clear error messages.
"""

from pathlib import Path
from typing import List, Union
from pydantic import ValidationError

# Import schemas (sibling package — project root must be on sys.path)
from schemas import (
    Package, PackageList,
    FlatpakApp, FlatpakList,
    ExternalPackage, ExternalPackageList,
    Theme, ThemeList
)


# =============================================================================
# Exceptions
# =============================================================================

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    
    def __init__(self, config_file: str, errors: List[dict]):
        self.config_file = config_file
        self.errors = errors
        
        # Format errors for human-readable output
        error_msgs = []
        for error in errors:
            loc = " -> ".join(str(l) for l in error.get("loc", []))
            msg = error.get("msg", "Unknown error")
            error_msgs.append(f"  • {loc}: {msg}")
        
        self.message = (
            f"\n❌ Validation errors in {config_file}:\n"
            + "\n".join(error_msgs)
        )
        super().__init__(self.message)


# =============================================================================
# Validation Functions
# =============================================================================

def validate_config(
    config_path: Union[str, Path],
    model_class: type
) -> any:
    """
    Validate a JSON configuration file against a Pydantic model.
    
    Args:
        config_path: Path to JSON config file
        model_class: Pydantic model class to validate against
    
    Returns:
        Validated model instance
    
    Raises:
        ConfigValidationError: If validation fails
        FileNotFoundError: If config file doesn't exist
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    try:
        # Read and parse JSON
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate with Pydantic
        validated = model_class.model_validate(data)
        return validated
        
    except ValidationError as e:
        # Convert Pydantic errors to our custom exception
        raise ConfigValidationError(
            config_file=str(config_path),
            errors=e.errors()
        )
    except json.JSONDecodeError as e:
        raise ConfigValidationError(
            config_file=str(config_path),
            errors=[{
                "loc": ["json"],
                "msg": f"Invalid JSON: {e.msg} at line {e.lineno}, column {e.colno}"
            }]
        )


def validate_install_config(path: Union[str, Path]) -> PackageList:
    """Validate install.json configuration."""
    return validate_config(path, PackageList)


def validate_remove_config(path: Union[str, Path]) -> PackageList:
    """Validate remove.json configuration."""
    return validate_config(path, PackageList)


def validate_flatpak_config(path: Union[str, Path]) -> FlatpakList:
    """Validate flatpak.json configuration."""
    return validate_config(path, FlatpakList)


def validate_external_config(path: Union[str, Path]) -> ExternalPackageList:
    """Validate external_packages.json configuration."""
    return validate_config(path, ExternalPackageList)


def validate_theme_config(path: Union[str, Path]) -> ThemeList:
    """Validate theme configuration (GTK, icons, cursors)."""
    return validate_config(path, ThemeList)


def validate_all_configs(config_dir: Union[str, Path] = "configs") -> dict:
    """
    Validate all configuration files in the configs directory.
    
    Args:
        config_dir: Path to configs directory (default: "configs")
    
    Returns:
        Dict mapping config names to validation results
    
    Raises:
        ConfigValidationError: If any validation fails (fail-fast)
    """
    config_dir = Path(config_dir)
    results = {}
    
    # Define all configs to validate
    config_validations = [
        ("install.json", validate_install_config),
        ("remove.json", validate_remove_config),
        ("flatpak.json", validate_flatpak_config),
        ("external_packages.json", validate_external_config),
        ("themes_gtk.json", validate_theme_config),
        ("themes_icons.json", validate_theme_config),
        ("themes_cursors.json", validate_theme_config),
    ]
    
    for config_file, validator in config_validations:
        config_path = config_dir / config_file
        
        if not config_path.exists():
            results[config_file] = None  # Optional file
            continue
        
        try:
            validated = validator(config_path)
            results[config_file] = validated
        except ConfigValidationError as e:
            # Re-raise to fail fast
            raise
    
    return results


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent directory to path so we can import utils
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from utils.logging_utils import info, success, error, warn
    
    print("\n" + "="*70)
    print("🔍 MintyForge - Configuration Validation")
    print("="*70 + "\n")
    
    config_dir = Path("configs")
    
    if not config_dir.exists():
        error(f"Config directory not found: {config_dir}")
        sys.exit(1)
    
    try:
        info("Validating all configuration files...")
        results = validate_all_configs(config_dir)
        
        print()
        for config_file, result in results.items():
            if result is None:
                warn(f"{config_file}: not found (skipped)")
            else:
                # Count items
                if hasattr(result, 'packages'):
                    count = len(result.packages)
                    item_type = "packages"
                elif hasattr(result, 'flatpaks'):
                    count = len(result.flatpaks)
                    item_type = "flatpaks"
                elif hasattr(result, 'themes'):
                    count = len(result.themes)
                    item_type = "themes"
                else:
                    count = "?"
                    item_type = "items"
                
                success(f"{config_file}: {count} {item_type} ✅")
        
        print("\n" + "="*70)
        success("✅ ALL CONFIGURATIONS VALID!")
        print("="*70 + "\n")
        sys.exit(0)
        
    except ConfigValidationError as e:
        print()
        error(str(e.message))
        print("\n" + "="*70)
        error("❌ VALIDATION FAILED")
        print("="*70 + "\n")
        sys.exit(1)
    except Exception as e:
        print()
        error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
