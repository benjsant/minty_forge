#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Flatpak Schemas
-----------------------------
Pydantic models for Flatpak applications (flatpak.json).
"""

from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator


class FlatpakApp(BaseModel):
    """Model for a Flatpak application."""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    source: Literal["flathub"] = Field(
        default="flathub",
        description="Flatpak source repository (only 'flathub' supported)"
    )
    app: str = Field(
        ...,
        min_length=1,
        pattern=r'^[a-zA-Z0-9._-]+$',
        description="Flatpak app ID (e.g., com.github.app)"
    )
    description: str = Field(
        default="",
        description="App description"
    )
    
    @field_validator('app')
    @classmethod
    def validate_app_id(cls, v: str) -> str:
        """Validate Flatpak app ID format."""
        if not v or v.isspace():
            raise ValueError("Flatpak app ID cannot be empty")
        
        # Basic validation: should look like a reverse-DNS name
        parts = v.split('.')
        if len(parts) < 2:
            raise ValueError(
                f"Invalid Flatpak app ID: '{v}'. "
                "Should be in format: com.example.App"
            )
        
        return v.strip()


class FlatpakList(BaseModel):
    """List of Flatpak applications."""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    flatpaks: List[FlatpakApp] = Field(
        ...,
        min_length=1,
        description="List of Flatpak apps"
    )
    
    @field_validator('flatpaks')
    @classmethod
    def validate_unique_apps(cls, v: List[FlatpakApp]) -> List[FlatpakApp]:
        """Ensure app IDs are unique."""
        app_ids = [app.app for app in v]
        duplicates = [aid for aid in app_ids if app_ids.count(aid) > 1]
        
        if duplicates:
            unique_dupes = list(set(duplicates))
            raise ValueError(
                f"Duplicate Flatpak app IDs found: {', '.join(unique_dupes)}"
            )
        
        return v
