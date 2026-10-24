from fastapi import APIRouter, Depends, Query

from app.api.deps import get_qb

router = APIRouter(prefix="/api/qb", tags=["quickbooks"])


@router.get("/search")
def qb_search(q: str = Query(min_length=1), qb=Depends(get_qb)):
    return [vars(j) for j in qb.find_jobs(q)]
