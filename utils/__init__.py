#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Utilities Package
-------------------------------
Common utility functions for MintyForge scripts.

This package provides:
- subprocess_utils: Secure command execution
- logging_utils: Colorized logging
- file_utils: File and JSON handling
- validation: JSON configuration validation (Pydantic)
"""

# State management (persistent action tracking + rollback)
from .state_manager import (
    StateManager,
    StateEntry,
    StateError,
    get_state_manager,
    ACTION_APT_INSTALL,
    ACTION_APT_REMOVE,
    ACTION_FLATPAK_INSTALL,
    ACTION_EXTERNAL_INSTALL,
)

# Subprocess utilities (secure command execution)
from .subprocess_utils import (
    run_command,
    run_sudo_command,
    check_package_installed,
    check_command_exists,
    apt_install,
    apt_remove,
    apt_update,
    apt_upgrade,
    flatpak_install,
    flatpak_list,
    check_flatpak_installed,
    git_clone,
    run_bash_script,
    run_python_script,
    CommandResult
)

# Logging utilities (colorized output)
from .logging_utils import (
    Logger,
    Colors,
    info,
    success,
    warn,
    error,
    debug,
    step,
    header,
    log_info,
    log_success,
    log_warn,
    log_error,
    log_debug,
    log_step,
    log_header,
    set_log_file
)

# File utilities (JSON and file handling)
from .file_utils import (
    load_json,
    save_json,
    load_package_list,
    ensure_directory,
    safe_read_file,
    safe_write_file,
    get_user_home,
    find_file_in_paths,
    ConfigManager,
    ConfigError
)

# Validation utilities (JSON config validation with Pydantic)
from .validation import (
    validate_config,
    validate_install_config,
    validate_remove_config,
    validate_flatpak_config,
    validate_external_config,
    validate_theme_config,
    validate_all_configs,
    ConfigValidationError
)

# Pydantic schemas (sibling package — project root must be on sys.path)
from schemas import (
    Package,
    PackageList,
    FlatpakApp,
    FlatpakList,
    ExternalPackage,
    ExternalPackageList,
    Theme,
    ThemeList
)

__all__ = [
    # State management
    'StateManager',
    'StateEntry',
    'StateError',
    'get_state_manager',
    'ACTION_APT_INSTALL',
    'ACTION_APT_REMOVE',
    'ACTION_FLATPAK_INSTALL',
    'ACTION_EXTERNAL_INSTALL',

    # Subprocess utilities
    'run_command',
    'run_sudo_command',
    'check_package_installed',
    'check_command_exists',
    'apt_install',
    'apt_remove',
    'apt_update',
    'apt_upgrade',
    'flatpak_install',
    'flatpak_list',
    'check_flatpak_installed',
    'git_clone',
    'run_bash_script',
    'run_python_script',
    'CommandResult',
    
    # Logging utilities
    'Logger',
    'Colors',
    'info',
    'success',
    'warn',
    'error',
    'debug',
    'step',
    'header',
    'log_info',
    'log_success',
    'log_warn',
    'log_error',
    'log_debug',
    'log_step',
    'log_header',
    'set_log_file',
    
    # File utilities
    'load_json',
    'save_json',
    'load_package_list',
    'ensure_directory',
    'safe_read_file',
    'safe_write_file',
    'get_user_home',
    'find_file_in_paths',
    'ConfigManager',
    'ConfigError',
    
    # Validation utilities
    'validate_config',
    'validate_install_config',
    'validate_remove_config',
    'validate_flatpak_config',
    'validate_external_config',
    'validate_theme_config',
    'validate_all_configs',
    'ConfigValidationError',
    'Package',
    'PackageList',
    'FlatpakApp',
    'FlatpakList',
    'ExternalPackage',
    'ExternalPackageList',
    'Theme',
    'ThemeList'
]
