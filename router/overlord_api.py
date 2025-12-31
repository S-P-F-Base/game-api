from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from template_env import templates

router = APIRouter()


@router.get("/ping")
async def ping_overlord():
    return {"ok": True}
