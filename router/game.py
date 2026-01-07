import random
from pathlib import Path

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from config import Config
from template_env import templates

router = APIRouter()
HTML_DIR = Path("templates")
LOADING_MEDIA_DIR = Path("static/loading_media")


def resolve_name_from_steam(steamid: str) -> str:
    try:
        response = requests.get(
            "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/",
            params={"key": Config.steam_api(), "steamids": steamid},
            timeout=3.0,
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
def loading(request: Request, steamid: str = "", mapname: str = ""):
    name = resolve_name_from_steam(steamid) if steamid else "гость"
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
        raise HTTPException(400, "Invalid file name")

    if not file_name.endswith(".html"):
        file_name += ".html"

    safe_path = Path(file_name)
    if safe_path.is_absolute() or any(part == ".." for part in safe_path.parts):
        raise HTTPException(400, "Invalid file path")

    file_path = HTML_DIR / safe_path

    try:
        file_path.resolve().relative_to(HTML_DIR.resolve())

    except ValueError:
        raise HTTPException(400, "Invalid file path")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "File not found")

    return templates.TemplateResponse(
        file_name,
        {
            "request": request,
        },
    )
