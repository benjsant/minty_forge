#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Theme Schemas
---------------------------
Pydantic models for themes (GTK, icons, cursors).
"""

from typing import List
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    model_validator
)


class Theme(BaseModel):
    """Model for GTK/Icon/Cursor themes."""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    name: str = Field(
        ...,
        min_length=1,
        description="Theme name (for reference)"
    )
    name_to_use: str = Field(
        ...,
        min_length=1,
        description="Actual theme name to apply"
    )
    url: str = Field(
        default="",
        description="Git repository URL (empty if preinstalled)"
    )
    cmd_user: str = Field(
        default="",
        description="Installation command for user directory"
    )
    cmd_root: str = Field(
        default="",
        description="Installation command for system directory"
    )
    description: str = Field(
        default="",
        description="Theme description"
    )
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL if provided."""
        if v and not v.isspace():
            # Basic URL validation
            if not (v.startswith('http://') or v.startswith('https://') 
                    or v.startswith('git://')):
                raise ValueError(
                    f"Invalid URL: '{v}'. Must start with http://, https://, or git://"
                )
        return v.strip() if v else ""
    
    @model_validator(mode='after')
    def validate_installation(self) -> 'Theme':
        """Ensure either URL+commands or neither (for preinstalled)."""
        has_url = bool(self.url)
        has_cmd_user = bool(self.cmd_user)
        has_cmd_root = bool(self.cmd_root)
        
        # If no URL, it's a preinstalled theme (no commands needed)
        # If URL, at least one cmd should be provided
        if has_url and not (has_cmd_user or has_cmd_root):
            raise ValueError(
                f"Theme '{self.name}' has URL but no installation commands. "
                "Provide at least cmd_user or cmd_root."
            )
        
        return self


class ThemeList(BaseModel):
    """List of themes (GTK, icons, cursors)."""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    themes: List[Theme] = Field(
        ...,
        min_length=1,
        description="List of themes"
    )
    
    @field_validator('themes')
    @classmethod
    def validate_unique_themes(cls, v: List[Theme]) -> List[Theme]:
        """Ensure theme names are unique."""
        names = [theme.name for theme in v]
        duplicates = [name for name in names if names.count(name) > 1]
        
        if duplicates:
            unique_dupes = list(set(duplicates))
            raise ValueError(
                f"Duplicate theme names found: {', '.join(unique_dupes)}"
            )
        
        return v
