from fastapi import APIRouter, Depends

from app.api.deps import get_conn
from app.api.schemas import NoteIn
from app.services import notes

router = APIRouter(prefix="/api", tags=["notes"])


@router.post("/jobs/{job_id}/notes")
def add_note(job_id: int, note: NoteIn, conn=Depends(get_conn)):
    notes.add(conn, job_id, note.body, note.author)
    return {"ok": True}


@router.delete("/notes/{note_id}")
def delete_note(note_id: int, conn=Depends(get_conn)):
    notes.delete(conn, note_id)
    return {"ok": True}
