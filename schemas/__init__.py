#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Schemas Package
-----------------------------
Pydantic models for JSON configuration validation.

This package provides schemas for:
- packages: APT packages (install/remove)
- flatpak: Flatpak applications
- external: External packages
- themes: GTK/Icon/Cursor/Kvantum themes
"""

from .packages import Package, PackageList
from .flatpak import FlatpakApp, FlatpakList
from .external import ExternalPackage, ExternalPackageList
from .themes import Theme, ThemeList, KvantumTheme, KvantumThemeList

__all__ = [
    # Package schemas
    'Package',
    'PackageList',
    
    # Flatpak schemas
    'FlatpakApp',
    'FlatpakList',
    
    # External package schemas
    'ExternalPackage',
    'ExternalPackageList',
    
    # Theme schemas
    'Theme',
    'ThemeList',
    'KvantumTheme',
    'KvantumThemeList',
]
