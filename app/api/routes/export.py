import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_conn
from app.services import export, jobs

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/export.xlsx")
def export_xlsx(user_id: int | None = None, include_hidden: bool = False, conn=Depends(get_conn)):
    views = [j for j in jobs.list_views(conn, user_id) if include_hidden or not j["hidden"]]
    return StreamingResponse(
        io.BytesIO(export.jobs_workbook(views)),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="job-costs.xlsx"'},
    )
