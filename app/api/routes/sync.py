import asyncio

from fastapi import APIRouter

from app.services import sync

router = APIRouter(prefix="/api", tags=["sync"])


@router.post("/sync")
async def sync_now():
    count = await asyncio.to_thread(sync.run_sync)
    return {"synced": count}
