"""
Notes CRUD routes.

All endpoints are provided under /api/notes with standard REST semantics.
Uses parameterized SQL with sqlite3 and ensures cursors/connections are closed.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from src.api import db
from src.api.models import NoteCreate, NoteOut, NoteUpdate

router = APIRouter(prefix="/api/notes", tags=["notes"])


def _row_to_note_out(row) -> NoteOut:
    """Convert sqlite3.Row to NoteOut."""
    return NoteOut(
        id=int(row["id"]),
        title=str(row["title"]),
        content=str(row["content"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


@router.get(
    "",
    response_model=list[NoteOut],
    summary="List notes",
    description="Return all notes ordered by most recently updated first.",
    operation_id="listNotes",
)
def list_notes() -> list[NoteOut]:
    """
    List all notes.

    Returns:
        List[NoteOut]: Notes ordered by updated_at DESC, then id DESC.
    """
    rows = db.execute_select(
        "SELECT id, title, content, created_at, updated_at FROM notes ORDER BY updated_at DESC, id DESC"
    )
    return [_row_to_note_out(r) for r in rows]


@router.get(
    "/{note_id}",
    response_model=NoteOut,
    summary="Get note",
    description="Get a single note by ID.",
    operation_id="getNote",
)
def get_note(note_id: int) -> NoteOut:
    """
    Get a note by id.

    Args:
        note_id: The note ID.

    Returns:
        NoteOut: The requested note.

    Raises:
        HTTPException: 404 if the note does not exist.
    """
    row = db.execute_select_one(
        "SELECT id, title, content, created_at, updated_at FROM notes WHERE id = ?",
        (note_id,),
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return _row_to_note_out(row)


@router.post(
    "",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create note",
    description="Create a new note.",
    operation_id="createNote",
)
def create_note(payload: NoteCreate) -> NoteOut:
    """
    Create a new note.

    Args:
        payload: NoteCreate

    Returns:
        NoteOut: Newly created note.
    """
    now = db.utc_now_iso()
    new_id = db.execute_modify(
        "INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (payload.title, payload.content, now, now),
    )
    row = db.execute_select_one(
        "SELECT id, title, content, created_at, updated_at FROM notes WHERE id = ?",
        (new_id,),
    )
    # Should exist immediately after insert; still guard for safety.
    if row is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create note")
    return _row_to_note_out(row)


@router.put(
    "/{note_id}",
    response_model=NoteOut,
    summary="Update note",
    description="Update an existing note by ID. Only provided fields are updated.",
    operation_id="updateNote",
)
def update_note(note_id: int, payload: NoteUpdate) -> NoteOut:
    """
    Update an existing note.

    Args:
        note_id: Note ID
        payload: NoteUpdate

    Returns:
        NoteOut: Updated note.

    Raises:
        HTTPException: 404 if note doesn't exist, 400 if no fields to update.
    """
    existing = db.execute_select_one(
        "SELECT id, title, content, created_at, updated_at FROM notes WHERE id = ?",
        (note_id,),
    )
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    new_title = payload.title if payload.title is not None else str(existing["title"])
    new_content = payload.content if payload.content is not None else str(existing["content"])

    if payload.title is None and payload.content is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update")

    now = db.utc_now_iso()
    db.execute_modify(
        "UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?",
        (new_title, new_content, now, note_id),
    )

    row = db.execute_select_one(
        "SELECT id, title, content, created_at, updated_at FROM notes WHERE id = ?",
        (note_id,),
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update note")
    return _row_to_note_out(row)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete note",
    description="Delete a note by ID.",
    operation_id="deleteNote",
)
def delete_note(note_id: int) -> Response:
    """
    Delete a note.

    Args:
        note_id: Note ID

    Returns:
        Response: 204 No Content on success.

    Raises:
        HTTPException: 404 if note doesn't exist.
    """
    existing = db.execute_select_one("SELECT id FROM notes WHERE id = ?", (note_id,))
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    db.execute_modify("DELETE FROM notes WHERE id = ?", (note_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
