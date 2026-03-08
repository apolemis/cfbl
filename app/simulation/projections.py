"""
projections.py — Player database loader and fuzzy name matching.

Loads players.json into a lookup dict keyed by normalized name.
Handles Shohei Ohtani's dual entries (Batter vs Pitcher),
accented characters (Jose vs Jose), and common name variations.
"""

import json
import os
import unicodedata
from typing import Optional


# Path to the players.json data file
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")


def _normalize_name(name: str) -> str:
    """
    Normalize a player name for matching:
    - Strip accents (Jose Ramirez matches Jose Ramirez)
    - Lowercase
    - Strip whitespace
    - Remove periods (J.D. -> JD, C.J. -> CJ)
    """
    # Decompose unicode, strip combining marks (accents)
    nfkd = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Lowercase, strip, remove periods
    return stripped.lower().strip().replace(".", "")


def load_player_db(filepath: str = PLAYERS_FILE) -> dict:
    """
    Load players.json and return a dict keyed by normalized name.

    Special handling for Shohei Ohtani:
    - "Shohei Ohtani" (batter, type=H) is stored under "shohei ohtani"
      AND "shohei ohtani (batter)"
    - "Shohei Ohtani" (pitcher, type=P) is stored under "shohei ohtani (pitcher)"

    Returns:
        dict: {normalized_name: player_dict}
    """
    with open(filepath, "r") as f:
        players = json.load(f)

    db = {}
    ohtani_batter = None
    ohtani_pitcher = None

    for player in players:
        name = player["name"]
        norm = _normalize_name(name)

        # Handle the two Ohtani entries
        if norm == "shohei ohtani":
            if player["type"] == "H":
                ohtani_batter = player
            elif player["type"] == "P":
                ohtani_pitcher = player
            continue

        # For all other players, just store by normalized name.
        # If there's a collision (rare), the later entry overwrites.
        db[norm] = player

    # Store Ohtani entries with explicit keys
    if ohtani_batter:
        db["shohei ohtani"] = ohtani_batter            # default -> batter
        db["shohei ohtani (batter)"] = ohtani_batter
    if ohtani_pitcher:
        db["shohei ohtani (pitcher)"] = ohtani_pitcher

    return db


def find_player(name: str, player_db: dict, player_type: Optional[str] = None) -> Optional[dict]:
    """
    Look up a player in the database by name.

    Matching strategy (in order):
    1. Exact normalized match
    2. If player_type is provided and name is "Shohei Ohtani", route to batter/pitcher
    3. Suffix-based match for Ohtani ("(Batter)" / "(Pitcher)" in the name)
    4. Substring match (for Jr., III, etc. variations)

    Args:
        name: Player name as it appears on the roster
        player_db: Dict from load_player_db()
        player_type: Optional "H" or "P" to disambiguate Ohtani

    Returns:
        Player dict or None if not found
    """
    norm = _normalize_name(name)

    # 1. Direct match
    if norm in player_db:
        return player_db[norm]

    # 2. Ohtani special case — route by type if known
    if "shohei ohtani" in norm:
        if player_type == "P":
            return player_db.get("shohei ohtani (pitcher)")
        # Default to batter
        return player_db.get("shohei ohtani")

    # 3. Try matching with common suffix/prefix variations
    #    e.g., "Luis Robert" vs "Luis Robert Jr."
    for db_name, player in player_db.items():
        # Check if one is a prefix of the other
        if db_name.startswith(norm) or norm.startswith(db_name):
            return player

    # 4. Fallback: token-based fuzzy match
    #    Split both names into tokens, check if all tokens from the shorter
    #    name appear in the longer name
    name_tokens = set(norm.split())
    if len(name_tokens) >= 2:
        for db_name, player in player_db.items():
            db_tokens = set(db_name.split())
            # If the roster name tokens are a subset of the DB name tokens (or vice versa)
            if name_tokens.issubset(db_tokens) or db_tokens.issubset(name_tokens):
                return player

    return None


def get_all_players(filepath: str = PLAYERS_FILE) -> list:
    """Load and return the raw list of all players from players.json."""
    with open(filepath, "r") as f:
        return json.load(f)
