"""
Pydantic models for Notes API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    """Payload for creating a new note."""

    title: str = Field(..., min_length=1, max_length=200, description="Note title")
    content: str = Field(..., min_length=1, description="Note content")


class NoteUpdate(BaseModel):
    """Payload for updating an existing note. All fields are optional."""

    title: str | None = Field(None, min_length=1, max_length=200, description="Updated note title")
    content: str | None = Field(None, min_length=1, description="Updated note content")


class NoteOut(BaseModel):
    """API representation of a note."""

    id: int = Field(..., description="Note ID")
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content")
    created_at: str = Field(..., description="ISO-8601 UTC timestamp when created")
    updated_at: str = Field(..., description="ISO-8601 UTC timestamp when last updated")
