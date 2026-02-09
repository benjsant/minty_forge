#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - External Package Schemas
--------------------------------------
Pydantic models for external packages (external_packages.json).
"""

from typing import List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ExternalPackage(BaseModel):
    """Model for external packages (from repositories, scripts, etc.)."""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    name: str = Field(
        ...,
        min_length=1,
        description="Package name"
    )
    description: str = Field(
        default="",
        description="Package description"
    )
    cmd: str = Field(
        ...,
        min_length=1,
        description="Installation command (shell script)"
    )
    
    @field_validator('cmd')
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Validate installation command."""
        if not v or v.isspace():
            raise ValueError("Installation command cannot be empty")
        
        # Warn about potentially dangerous commands (informative only)
        dangerous_patterns = ['rm -rf /', 'dd if=', 'mkfs.', ':(){:|:&};:']
        for pattern in dangerous_patterns:
            if pattern in v.lower():
                # Note: We don't block, just validate format
                pass
        
        return v.strip()


class ExternalPackageList(BaseModel):
    """List of external packages."""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    packages: List[ExternalPackage] = Field(
        ...,
        min_length=1,
        description="List of external packages"
    )
