"""Background QuickBooks sync every JCT_SYNC_MINUTES while the web server runs."""

import asyncio
import logging

from app import config
from app.services import sync

log = logging.getLogger(__name__)


async def sync_loop():
    while True:
        try:
            await asyncio.to_thread(sync.run_sync)
        except Exception:
            log.exception("Scheduled sync failed")
        await asyncio.sleep(config.sync_minutes() * 60)
