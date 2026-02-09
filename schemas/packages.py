#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Package Schemas
-----------------------------
Pydantic models for APT packages (install.json, remove.json).
"""

from typing import List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class Package(BaseModel):
    """Base model for a package (APT, etc.)."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra='forbid'  # Forbid extra fields not in model
    )
    
    name: str = Field(
        ...,
        min_length=1,
        description="Package name (cannot be empty)"
    )
    description: str = Field(
        default="",
        description="Package description"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate package name."""
        if not v or v.isspace():
            raise ValueError("Package name cannot be empty or whitespace only")
        return v.strip()


class PackageList(BaseModel):
    """List of packages for install.json and remove.json."""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    packages: List[Package] = Field(
        ...,
        min_length=1,
        description="List of packages (must contain at least one)"
    )
    
    @field_validator('packages')
    @classmethod
    def validate_unique_names(cls, v: List[Package]) -> List[Package]:
        """Ensure package names are unique."""
        names = [pkg.name for pkg in v]
        duplicates = [name for name in names if names.count(name) > 1]
        
        if duplicates:
            unique_dupes = list(set(duplicates))
            raise ValueError(
                f"Duplicate package names found: {', '.join(unique_dupes)}"
            )
        
        return v
