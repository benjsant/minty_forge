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
- themes: GTK/Icon/Cursor themes
"""

from .packages import Package, PackageList
from .flatpak import FlatpakApp, FlatpakList
from .external import ExternalPackage, ExternalPackageList
from .themes import Theme, ThemeList
from .profile import Profile, ProfileAptPackage, ProfileFlatpak, ProfileExternal, ProfileRemove

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

    # Profile schemas
    'Profile',
    'ProfileAptPackage',
    'ProfileFlatpak',
    'ProfileExternal',
    'ProfileRemove',
]
