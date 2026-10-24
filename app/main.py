"""Web server: JSON API + the dashboard page. Run with `python run.py`."""

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import config, scheduler
from app.api.routes import ROUTERS
from app.services.errors import Conflict, NotFound
from app.services.setup import prepare_database

STATIC = config.ROOT / "app" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    prepare_database(config.db_path())
    task = asyncio.create_task(scheduler.sync_loop())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


def create_app() -> FastAPI:
    app = FastAPI(title="Job Cost Tracker", lifespan=lifespan)

    @app.exception_handler(NotFound)
    async def not_found(request: Request, exc: NotFound):
        return JSONResponse({"detail": str(exc)}, status_code=404)

    @app.exception_handler(Conflict)
    async def conflict(request: Request, exc: Conflict):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    for router in ROUTERS:
        app.include_router(router)
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    return app


app = create_app()
