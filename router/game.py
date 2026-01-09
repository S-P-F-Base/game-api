import os
import random
from pathlib import Path

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse

from template_env import templates

router = APIRouter()
HTML_DIR = Path("templates")
LOADING_MEDIA_DIR = Path("static/loading_media")


async def resolve_name_from_steam(steamid: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/",
                params={
                    "key": os.environ["steam_api"],
                    "steamids": steamid,
                },
            )
            response.raise_for_status()

        players = response.json().get("response", {}).get("players", [])
        if players:
            return players[0].get("personaname", "гость")

    except Exception:
        pass

    return "гость"


def pick_weighted_media() -> str | None:
    candidates: list[Path] = []

    for path in LOADING_MEDIA_DIR.iterdir():
        if not path.is_file():
            continue

        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue

        try:
            weight = int(path.name.split("_", 1)[0])
        except (ValueError, IndexError):
            continue

        candidates.extend([path] * weight)

    if not candidates:
        return None

    chosen = random.choice(candidates)
    return f"loading_media/{chosen.name}"


@router.get("/game/loading", response_class=HTMLResponse)
async def loading(request: Request, steamid: str = "", mapname: str = ""):
    name = await resolve_name_from_steam(steamid) if steamid else "гость"
    media_url = pick_weighted_media()

    return templates.TemplateResponse(
        "loading.html",
        {
            "request": request,
            "mapname": mapname,
            "name": name,
            "media_url": media_url,
        },
    )


@router.get("/game/{file_name}")
def get_page(request: Request, file_name: str):
    if not file_name or file_name.strip() != file_name:
        return Response(
            content="Invalid file name",
            status_code=400,
            media_type="text/html",
        )

    if not file_name.endswith(".html"):
        file_name += ".html"

    file_path = HTML_DIR / Path(file_name)

    try:
        file_path.resolve().relative_to(HTML_DIR.resolve())

    except ValueError:
        return Response(
            content="Forbidden",
            status_code=403,
            media_type="text/html",
        )

    if not file_path.is_file():
        return Response(
            content="File not found",
            status_code=404,
            media_type="text/html",
        )

    return templates.TemplateResponse(
        file_name,
        {"request": request},
    )
