#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - File Utilities
----------------------------
Common file operations and JSON handling.
Centralizes file management logic.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConfigError(Exception):
    """Raised when configuration file is invalid or missing."""
    pass


def load_json(file_path: Path, required: bool = True) -> Dict[str, Any]:
    """
    Load and parse a JSON configuration file.
    
    Args:
        file_path: Path to JSON file
        required: If True, raise error if file doesn't exist
    
    Returns:
        Parsed JSON data as dictionary
    
    Raises:
        ConfigError: If file is missing (when required=True) or invalid JSON
    
    Example:
        config = load_json(Path("configs/install.json"))
        packages = config.get("packages", [])
    """
    if not file_path.exists():
        if required:
            raise ConfigError(f"Configuration file not found: {file_path}")
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise ConfigError(f"Error reading {file_path}: {e}")


def save_json(data: Dict[str, Any], file_path: Path, indent: int = 2):
    """
    Save data to JSON file with pretty formatting.
    
    Args:
        data: Dictionary to save
        file_path: Path to save to
        indent: Indentation level (default: 2)
    
    Example:
        save_json({"packages": ["curl", "wget"]}, Path("config.json"))
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_package_list(config_file: Path, validate: bool = True) -> List[Dict[str, str]]:
    """
    Load package list from JSON config file.
    
    Handles both formats:
    - {"packages": [...]}
    - {"flatpaks": [...]}
    - {"themes": [...]}
    
    Args:
        config_file: Path to JSON config
        validate: If True, validate config with Pydantic (default: True)
    
    Returns:
        List of package dictionaries
    
    Raises:
        ConfigError: If file is invalid or doesn't exist
        ConfigValidationError: If validation fails (when validate=True)
    
    Example:
        # With validation (recommended)
        packages = load_package_list(Path("configs/install.json"))
        
        # Without validation (legacy)
        packages = load_package_list(Path("configs/install.json"), validate=False)
        
        for pkg in packages:
            print(pkg["name"], pkg["description"])
    """
    if validate:
        # Use Pydantic validation
        try:
            from .validation import (
                validate_install_config,
                validate_remove_config,
                validate_flatpak_config,
                validate_external_config,
                validate_theme_config
            )
            
            # Determine which validator to use based on filename
            filename = config_file.name.lower()
            
            if "install" in filename and "json" in filename:
                validated = validate_install_config(config_file)
                return [pkg.model_dump() for pkg in validated.packages]
            
            elif "remove" in filename and "json" in filename:
                validated = validate_remove_config(config_file)
                return [pkg.model_dump() for pkg in validated.packages]
            
            elif "flatpak" in filename and "json" in filename:
                validated = validate_flatpak_config(config_file)
                return [app.model_dump() for app in validated.flatpaks]
            
            elif "external" in filename and "json" in filename:
                validated = validate_external_config(config_file)
                return [pkg.model_dump() for pkg in validated.packages]
            
            elif "themes" in filename or "theme" in filename:
                validated = validate_theme_config(config_file)
                return [theme.model_dump() for theme in validated.themes]
            
            else:
                # Unknown config type - fall back to non-validated loading
                pass
        
        except ImportError:
            # Pydantic not installed - fall back to non-validated loading
            pass
    
    # Non-validated loading (legacy or fallback)
    config = load_json(config_file)
    
    # Try different keys
    for key in ["packages", "flatpaks", "themes"]:
        if key in config:
            return config[key]
    
    return []


def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, create if needed.
    
    Args:
        path: Directory path
    
    Returns:
        The same path (for chaining)
    
    Example:
        themes_dir = ensure_directory(Path("themes"))
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_read_file(file_path: Path, default: str = "") -> str:
    """
    Safely read file content, return default if error.
    
    Args:
        file_path: Path to file
        default: Default value if error
    
    Returns:
        File content or default
    
    Example:
        content = safe_read_file(Path("README.md"), "No readme")
    """
    try:
        return file_path.read_text(encoding='utf-8')
    except Exception:
        return default


def safe_write_file(file_path: Path, content: str) -> bool:
    """
    Safely write content to file.
    
    Args:
        file_path: Path to file
        content: Content to write
    
    Returns:
        True if successful, False otherwise
    
    Example:
        if safe_write_file(Path("output.txt"), "Hello"):
            print("Written!")
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return True
    except Exception:
        return False


def get_user_home() -> Path:
    """
    Get user home directory, handling sudo correctly.
    
    Returns:
        Path to real user's home (even when running with sudo)
    
    Example:
        home = get_user_home()  # /home/username (not /root)
    """
    import os
    
    # Try SUDO_USER first (when running with sudo)
    sudo_user = os.getenv("SUDO_USER")
    if sudo_user:
        return Path(f"/home/{sudo_user}")
    
    # Fallback to regular user
    user = os.getenv("USER")
    if user and user != "root":
        return Path(f"/home/{user}")
    
    # Last resort
    return Path.home()


def find_file_in_paths(filename: str, search_paths: List[Path]) -> Optional[Path]:
    """
    Search for a file in multiple directories.
    
    Args:
        filename: File name to search for
        search_paths: List of directories to search
    
    Returns:
        Path to first matching file, or None
    
    Example:
        script = find_file_in_paths(
            "install.sh",
            [Path("scripts"), Path("bin")]
        )
    """
    for path in search_paths:
        candidate = path / filename
        if candidate.exists():
            return candidate
    return None


class ConfigManager:
    """
    Manages configuration files for MintyForge.
    
    Example:
        config = ConfigManager(Path("configs"))
        packages = config.get_packages("install.json")
        flatpaks = config.get_packages("flatpak.json")
    """
    
    def __init__(self, config_dir: Path):
        """
        Initialize config manager.
        
        Args:
            config_dir: Directory containing config files
        """
        self.config_dir = config_dir
        ensure_directory(config_dir)
    
    def get_config_path(self, filename: str) -> Path:
        """Get full path to a config file."""
        return self.config_dir / filename
    
    def load(self, filename: str) -> Dict[str, Any]:
        """Load a configuration file."""
        return load_json(self.get_config_path(filename))
    
    def save(self, filename: str, data: Dict[str, Any]):
        """Save a configuration file."""
        save_json(data, self.get_config_path(filename))
    
    def get_packages(self, filename: str) -> List[Dict[str, str]]:
        """Get package list from a config file."""
        return load_package_list(self.get_config_path(filename))
    
    def exists(self, filename: str) -> bool:
        """Check if a config file exists."""
        return self.get_config_path(filename).exists()
