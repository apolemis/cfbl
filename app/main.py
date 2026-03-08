from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import json

app = FastAPI(title="CFBL")
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def load_latest(subdir):
    d = BASE_DIR / "data" / subdir
    files = sorted(d.glob("week*.json"))
    if files:
        return json.loads(files[-1].read_text())
    return None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    rankings = load_latest("rankings")
    matchups = load_latest("matchups")
    return templates.TemplateResponse("base.html", {
        "request": request,
        "rankings": rankings,
        "matchups": matchups,
    })


@app.get("/health")
async def health():
    return {"status": "ok"}
