from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from pydantic import BaseModel
import json
import time
import uuid

app = FastAPI(title="CFBL")
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

SALARY_CAP_PATH = BASE_DIR / "data" / "salary_cap.json"
MESSAGES_PATH = BASE_DIR / "data" / "messages.json"


def load_latest(subdir):
    d = BASE_DIR / "data" / subdir
    files = sorted(d.glob("week*.json"))
    if files:
        return json.loads(files[-1].read_text())
    return None


def load_salary_cap():
    if SALARY_CAP_PATH.exists():
        return json.loads(SALARY_CAP_PATH.read_text())
    return None


def save_salary_cap(data):
    SALARY_CAP_PATH.write_text(json.dumps(data, indent=2))


def compute_current_salary(team, round_values):
    """Current salary = starting + value of original picks no longer owned - value of acquired picks."""
    original_picks = set(range(1, 27))
    current_picks = set(team["picks"])
    traded_away = original_picks - current_picks
    acquired = current_picks - original_picks  # picks from other teams (round nums won't overlap since picks are just round numbers)

    # Actually, picks are just round numbers (1-26). When trades happen, we swap pick round numbers.
    # A team's "picks" list contains the round numbers they currently own.
    # Starting salary + sum of values of picks they traded away - sum of values of picks they acquired.
    # But since picks are just round numbers, we can't distinguish "original" from "acquired" just from the list.
    # We need to track this via trade history.

    salary = team["starting_salary"]
    for trade in team["trades"]:
        for rd in trade.get("gave", []):
            salary += round_values[rd - 1]
        for rd in trade.get("got", []):
            salary -= round_values[rd - 1]
    return salary


class TradeRequest(BaseModel):
    team_a_id: int
    team_b_id: int
    team_a_gives: list[int]  # round numbers team A gives away
    team_b_gives: list[int]  # round numbers team B gives away


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    rankings = load_latest("rankings")
    matchups = load_latest("matchups")
    salary_cap = load_salary_cap()
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "rankings": rankings,
            "matchups": matchups,
            "salary_cap": salary_cap,
        },
    )


@app.get("/api/salary-cap")
async def get_salary_cap():
    data = load_salary_cap()
    if not data:
        return JSONResponse({"error": "No salary cap data"}, status_code=404)
    for team in data["teams"]:
        team["current_salary"] = compute_current_salary(team, data["round_values"])
    return data


@app.post("/api/trade")
async def execute_trade(trade: TradeRequest):
    data = load_salary_cap()
    if not data:
        return JSONResponse({"error": "No salary cap data"}, status_code=404)

    rv = data["round_values"]

    # Find teams
    team_a = next((t for t in data["teams"] if t["id"] == trade.team_a_id), None)
    team_b = next((t for t in data["teams"] if t["id"] == trade.team_b_id), None)
    if not team_a or not team_b:
        return JSONResponse({"error": "Team not found"}, status_code=400)
    if trade.team_a_id == trade.team_b_id:
        return JSONResponse({"error": "Cannot trade with yourself"}, status_code=400)

    # Validate equal picks
    if len(trade.team_a_gives) != len(trade.team_b_gives):
        return JSONResponse({"error": "Must exchange equal number of picks"}, status_code=400)
    if len(trade.team_a_gives) == 0:
        return JSONResponse({"error": "Must select at least one pick per side"}, status_code=400)

    # Validate picks are owned
    for rd in trade.team_a_gives:
        if rd not in team_a["picks"]:
            return JSONResponse({"error": f"{team_a['owner']} doesn't own round {rd}"}, status_code=400)
    for rd in trade.team_b_gives:
        if rd not in team_b["picks"]:
            return JSONResponse({"error": f"{team_b['owner']} doesn't own round {rd}"}, status_code=400)

    # Compute pro-forma salaries
    a_salary = compute_current_salary(team_a, rv)
    b_salary = compute_current_salary(team_b, rv)

    a_gives_value = sum(rv[rd - 1] for rd in trade.team_a_gives)
    a_gets_value = sum(rv[rd - 1] for rd in trade.team_b_gives)
    b_gives_value = a_gets_value
    b_gets_value = a_gives_value

    new_a_salary = a_salary + a_gives_value - a_gets_value
    new_b_salary = b_salary + b_gives_value - b_gets_value

    # Check cap limits
    ceiling = data["cap_ceiling"]
    floor = data["cap_floor"]
    errors = []
    if new_a_salary > ceiling:
        errors.append(f"{team_a['owner']} would exceed cap ceiling (${new_a_salary} > ${ceiling})")
    if new_a_salary < floor:
        errors.append(f"{team_a['owner']} would fall below cap floor (${new_a_salary} < ${floor})")
    if new_b_salary > ceiling:
        errors.append(f"{team_b['owner']} would exceed cap ceiling (${new_b_salary} > ${ceiling})")
    if new_b_salary < floor:
        errors.append(f"{team_b['owner']} would fall below cap floor (${new_b_salary} < ${floor})")
    if errors:
        return JSONResponse({"error": "; ".join(errors)}, status_code=400)

    # Execute trade
    for rd in trade.team_a_gives:
        team_a["picks"].remove(rd)
        team_b["picks"].append(rd)
    for rd in trade.team_b_gives:
        team_b["picks"].remove(rd)
        team_a["picks"].append(rd)

    team_a["picks"].sort()
    team_b["picks"].sort()

    trade_record = {
        "team_a_id": trade.team_a_id,
        "team_a_owner": team_a["owner"],
        "team_b_id": trade.team_b_id,
        "team_b_owner": team_b["owner"],
        "team_a_gives": trade.team_a_gives,
        "team_b_gives": trade.team_b_gives,
    }
    team_a["trades"].append({"gave": trade.team_a_gives, "got": trade.team_b_gives, "with": team_b["owner"]})
    team_b["trades"].append({"gave": trade.team_b_gives, "got": trade.team_a_gives, "with": team_a["owner"]})

    save_salary_cap(data)

    return {
        "success": True,
        "trade": trade_record,
        "team_a_salary": new_a_salary,
        "team_b_salary": new_b_salary,
    }


@app.post("/api/undo-trade")
async def undo_trade():
    data = load_salary_cap()
    if not data:
        return JSONResponse({"error": "No salary cap data"}, status_code=404)

    # Find the most recent trade across all teams
    latest_trade = None
    latest_team = None
    for team in data["teams"]:
        if team["trades"]:
            latest_trade = team["trades"][-1]
            latest_team = team
            break

    if not latest_trade:
        return JSONResponse({"error": "No trades to undo"}, status_code=400)

    # Find the partner team
    partner = next((t for t in data["teams"] if t["owner"] == latest_trade["with"]), None)
    if not partner:
        return JSONResponse({"error": "Trade partner not found"}, status_code=400)

    # Reverse the trade: give back what was got, take back what was gave
    for rd in latest_trade["got"]:
        if rd in latest_team["picks"]:
            latest_team["picks"].remove(rd)
            partner["picks"].append(rd)
    for rd in latest_trade["gave"]:
        if rd in partner["picks"]:
            partner["picks"].remove(rd)
            latest_team["picks"].append(rd)

    latest_team["picks"].sort()
    partner["picks"].sort()

    # Remove trade records from both teams
    latest_team["trades"].pop()
    # Find and remove matching trade from partner
    for i in range(len(partner["trades"]) - 1, -1, -1):
        t = partner["trades"][i]
        if t["with"] == latest_team["owner"] and set(t["gave"]) == set(latest_trade["got"]) and set(t["got"]) == set(latest_trade["gave"]):
            partner["trades"].pop(i)
            break

    save_salary_cap(data)
    return {"success": True, "message": "Last trade undone"}


## ============================================
## Message Board
## ============================================

def load_messages():
    if MESSAGES_PATH.exists():
        return json.loads(MESSAGES_PATH.read_text())
    return []


def save_messages(messages):
    MESSAGES_PATH.write_text(json.dumps(messages, indent=2))


class MessageRequest(BaseModel):
    name: str
    message: str


class VoteRequest(BaseModel):
    message_id: str
    vote_type: str  # "thumbsup" or "lock"


@app.get("/api/messages")
async def get_messages():
    return load_messages()


@app.post("/api/messages")
async def post_message(msg: MessageRequest):
    name = msg.name.strip()[:50]
    message = msg.message.strip()[:500]
    if not name or not message:
        return JSONResponse({"error": "Name and message are required"}, status_code=400)

    messages = load_messages()
    new_msg = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "message": message,
        "timestamp": int(time.time()),
        "thumbsup": 0,
        "lock": 0,
    }
    messages.insert(0, new_msg)
    save_messages(messages)
    return new_msg


@app.post("/api/messages/vote")
async def vote_message(vote: VoteRequest):
    if vote.vote_type not in ("thumbsup", "lock"):
        return JSONResponse({"error": "Invalid vote type"}, status_code=400)

    messages = load_messages()
    for m in messages:
        if m["id"] == vote.message_id:
            m[vote.vote_type] = m.get(vote.vote_type, 0) + 1
            save_messages(messages)
            return {"success": True, "thumbsup": m["thumbsup"], "lock": m["lock"]}

    return JSONResponse({"error": "Message not found"}, status_code=404)


@app.get("/health")
async def health():
    return {"status": "ok"}
