"""
rosters.py — Roster and schedule loading helpers.

Loads rosters.json which contains:
- 12 teams, each with an id, name, and list of players (name + roster pos)
- week1_matchups (list of [team_a_id, team_b_id] pairs)
"""

import json
import os
from typing import Optional


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ROSTERS_FILE = os.path.join(DATA_DIR, "rosters.json")


def load_rosters(filepath: str = ROSTERS_FILE) -> dict:
    """
    Load the full rosters.json file.

    Returns:
        dict with keys "teams" (list of team dicts) and "week1_matchups"
    """
    with open(filepath, "r") as f:
        return json.load(f)


def get_teams(filepath: str = ROSTERS_FILE) -> list:
    """
    Return the list of all 12 teams.

    Each team dict has:
        - id: int (1-12)
        - name: str
        - players: list of {"name": str, "pos": str}
    """
    data = load_rosters(filepath)
    return data["teams"]


def get_team_by_id(team_id: int, filepath: str = ROSTERS_FILE) -> Optional[dict]:
    """Look up a single team by its numeric ID (1-12)."""
    for team in get_teams(filepath):
        if team["id"] == team_id:
            return team
    return None


def get_team_by_name(name: str, filepath: str = ROSTERS_FILE) -> Optional[dict]:
    """Look up a single team by its name (case-insensitive partial match)."""
    name_lower = name.lower()
    for team in get_teams(filepath):
        if name_lower in team["name"].lower():
            return team
    return None


def get_matchups(week: int = 1, filepath: str = ROSTERS_FILE) -> list:
    """
    Get matchup pairs for the given week.

    Currently only week1_matchups is stored in rosters.json.
    Returns a list of (team_a_id, team_b_id) tuples.

    Args:
        week: Week number (currently only 1 is supported from rosters.json)
        filepath: Path to rosters.json

    Returns:
        List of [team_a_id, team_b_id] pairs
    """
    data = load_rosters(filepath)

    key = f"week{week}_matchups"
    if key in data:
        return data[key]

    # Fallback: check for a schedule file
    schedule_file = os.path.join(DATA_DIR, "schedule.json")
    if os.path.exists(schedule_file):
        with open(schedule_file, "r") as f:
            schedule = json.load(f)
        week_key = str(week)
        if week_key in schedule:
            return schedule[week_key]

    raise ValueError(
        f"No matchups found for week {week}. "
        f"Checked rosters.json key '{key}' and schedule.json."
    )


def get_roster_positions() -> dict:
    """
    Return the roster slot configuration.

    Active slots:
        Hitting: C, 1B, 2B, 3B, SS, OF x3, Util x3 (11 hitters)
        Pitching: SP x3, RP x2, P x3 (8 pitchers)

    Inactive designations: BN (bench), IL (injured list), NA (not available)
    """
    return {
        "hitting": {
            "C": 1,
            "1B": 1,
            "2B": 1,
            "3B": 1,
            "SS": 1,
            "OF": 3,
            "Util": 3,
        },
        "pitching": {
            "SP": 3,
            "RP": 2,
            "P": 3,
        },
        "inactive": ["BN", "IL", "NA"],
    }
