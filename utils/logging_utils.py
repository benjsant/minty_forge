#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Logging Utilities
-------------------------------
Centralized logging functions with colorized output.
Eliminates code duplication across all scripts.
"""

import logging
from typing import Optional
from pathlib import Path

# ANSI Color codes
class Colors:
    """Terminal color codes for output formatting."""
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[1;31m"
    BLUE = "\033[1;34m"
    CYAN = "\033[1;36m"
    MAGENTA = "\033[1;35m"
    WHITE = "\033[1;37m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class Logger:
    """
    Centralized logger with colorized console output.
    
    Usage:
        from utils import Logger
        logger = Logger()
        logger.info("Starting installation...")
        logger.success("Installation completed!")
    """
    
    def __init__(self, name: str = "MintyForge", log_file: Optional[Path] = None):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            log_file: Optional log file path
        """
        self.name = name
        self.log_file = log_file
        
        # Setup file logging if requested
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(
                filename=str(log_file),
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(message)s",
            )
    
    def info(self, msg: str):
        """Print info message in blue."""
        print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")
        if self.log_file:
            logging.info(msg)
    
    def success(self, msg: str):
        """Print success message in green."""
        print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")
        if self.log_file:
            logging.info(f"✓ {msg}")
    
    def warn(self, msg: str):
        """Print warning message in yellow."""
        print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")
        if self.log_file:
            logging.warning(msg)
    
    def error(self, msg: str):
        """Print error message in red."""
        print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}")
        if self.log_file:
            logging.error(msg)
    
    def debug(self, msg: str):
        """Print debug message in cyan."""
        print(f"{Colors.CYAN}[DEBUG]{Colors.RESET} {msg}")
        if self.log_file:
            logging.debug(msg)
    
    def step(self, msg: str):
        """Print step message (bold)."""
        print(f"{Colors.BOLD}→ {msg}{Colors.RESET}")
        if self.log_file:
            logging.info(f"→ {msg}")
    
    def header(self, msg: str):
        """Print header message."""
        separator = "=" * len(msg)
        print(f"\n{Colors.BOLD}{separator}")
        print(msg)
        print(f"{separator}{Colors.RESET}\n")
        if self.log_file:
            logging.info(f"\n{'='*60}\n{msg}\n{'='*60}")


# Global default logger instance
_default_logger = Logger()


# Convenience functions using default logger
def info(msg: str):
    """Print info message (convenience function)."""
    _default_logger.info(msg)


def success(msg: str):
    """Print success message (convenience function)."""
    _default_logger.success(msg)


def warn(msg: str):
    """Print warning message (convenience function)."""
    _default_logger.warn(msg)


def error(msg: str):
    """Print error message (convenience function)."""
    _default_logger.error(msg)


def debug(msg: str):
    """Print debug message (convenience function)."""
    _default_logger.debug(msg)


def step(msg: str):
    """Print step message (convenience function)."""
    _default_logger.step(msg)


def header(msg: str):
    """Print header message (convenience function)."""
    _default_logger.header(msg)


def set_log_file(log_file: Path):
    """Set log file for the default logger."""
    global _default_logger
    _default_logger = Logger(log_file=log_file)


# Aliases for consistency
log_info = info
log_success = success
log_warn = warn
log_error = error
log_debug = debug
log_step = step
log_header = header
