from fastapi import APIRouter, Depends

from app.api.deps import get_conn
from app.api.schemas import UserIn, UserJobIn
from app.services import users

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(conn=Depends(get_conn)):
    return users.list_all(conn)


@router.post("")
def add_user(body: UserIn, conn=Depends(get_conn)):
    return users.get_or_create(conn, body.name)


@router.get("/{user_id}/prefs")
def get_prefs(user_id: int, conn=Depends(get_conn)):
    return users.get_prefs(conn, user_id)


@router.put("/{user_id}/prefs")
def save_prefs(user_id: int, prefs: dict, conn=Depends(get_conn)):
    return users.save_prefs(conn, user_id, prefs)


@router.put("/{user_id}/jobs/{job_id}")
def set_user_job(user_id: int, job_id: int, body: UserJobIn, conn=Depends(get_conn)):
    users.set_job_flags(conn, user_id, job_id, starred=body.starred, hidden=body.hidden)
    return {"ok": True}
