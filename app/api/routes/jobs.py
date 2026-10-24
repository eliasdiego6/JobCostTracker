from fastapi import APIRouter, Depends

from app.api.deps import get_conn, get_qb
from app.api.schemas import Estimates, JobIn
from app.services import jobs

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
def list_jobs(user_id: int | None = None, conn=Depends(get_conn)):
    return jobs.dashboard(conn, user_id)


@router.get("/{job_id}")
def job_detail(job_id: int, conn=Depends(get_conn)):
    return jobs.detail(conn, job_id)


@router.post("")
def add_job(body: JobIn, conn=Depends(get_conn), qb=Depends(get_qb)):
    estimates = body.model_dump(include=set(Estimates.model_fields))
    return jobs.add(conn, qb, body.job_number, body.qb_list_id, estimates, body.created_by)


@router.put("/{job_id}")
def update_job(job_id: int, body: Estimates, conn=Depends(get_conn)):
    return jobs.update_estimates(conn, job_id, body.model_dump())


@router.delete("/{job_id}")
def delete_job(job_id: int, conn=Depends(get_conn)):
    jobs.delete(conn, job_id)
    return {"ok": True}
