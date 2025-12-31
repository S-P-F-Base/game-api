import asyncio
import contextlib
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from router.overlord_api import router as overlord_router
from router.proxy import router as proxy_router
from router.static_accel import router as static_accel_router
from services import poll_services


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(poll_services())

    try:
        yield

    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

if os.getenv("FASTAPISTATIC") == "1":
    app.mount(
        "/static",
        StaticFiles(directory="static"),
        name="static",
    )

app.include_router(overlord_router)
app.include_router(static_accel_router)
app.include_router(proxy_router)
