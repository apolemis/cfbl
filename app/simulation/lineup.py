"""
lineup.py -- Optimal lineup solver for CFBL fantasy baseball.

Given a team's full roster (including BN/IL/NA players) and a player_db,
assigns players to active slots to maximize total z-score.

Roster slot configuration:
    Hitting:  C x1, 1B x1, 2B x1, 3B x1, SS x1, OF x3, Util x3 (11 active)
    Pitching: SP x3, RP x2, P x3 (8 active)

Position eligibility comes from the PLAYERS data `pos` field, NOT the Yahoo
roster slot assignment. BN/IL/NA players are still considered for optimal lineup.
"""

from __future__ import annotations

from typing import Optional

from app.simulation.projections import find_player


# Ordered position-specific hitting slots.
# Each entry: (slot_name, count, eligible_positions)
HITTING_SLOTS = [
    ("C", 1, {"C"}),
    ("1B", 1, {"1B"}),
    ("2B", 1, {"2B"}),
    ("3B", 1, {"3B"}),
    ("SS", 1, {"SS"}),
    ("OF", 3, {"OF"}),
    # Util accepts any hitter (including DH)
    ("Util", 3, {"C", "1B", "2B", "3B", "SS", "OF", "DH"}),
]

# Ordered position-specific pitching slots.
PITCHING_SLOTS = [
    ("SP", 3, {"SP"}),
    ("RP", 2, {"RP"}),
    # P accepts any pitcher
    ("P", 3, {"SP", "RP"}),
]


def _resolve_roster_players(
    roster_players: list[dict],
    player_db: dict,
) -> tuple[list[dict], list[dict]]:
    """
    Resolve a team's roster player names against the player_db.

    Separates resolved players into hitters and pitchers.
    Players not found in the DB (minor leaguers, NA-stash, etc.) are skipped.

    Special handling for Shohei Ohtani: when the Yahoo roster slot is a
    pitching slot (SP/RP/P), look up the pitcher version; otherwise the batter.

    Args:
        roster_players: List of {"name": str, "pos": str} from rosters.json
        player_db: Dict from load_player_db()

    Returns:
        (hitters, pitchers) -- each a list of player dicts from the DB
    """
    hitters = []
    pitchers = []
    seen_names: set[str] = set()

    # Pitching Yahoo roster positions (active + bench)
    pitching_yahoo_slots = {"SP", "RP", "P"}

    for rp in roster_players:
        name = rp["name"]
        yahoo_pos = rp["pos"]

        # Determine player_type hint for Ohtani disambiguation
        player_type: Optional[str] = None
        if "ohtani" in name.lower():
            player_type = "P" if yahoo_pos in pitching_yahoo_slots else "H"

        player = find_player(name, player_db, player_type=player_type)
        if player is None:
            continue

        # Avoid double-counting the same player (e.g. if roster has dupes)
        key = (player["name"], player["type"])
        if key in seen_names:
            continue
        seen_names.add(key)

        if player["type"] == "H":
            hitters.append(player)
        elif player["type"] == "P":
            pitchers.append(player)

    return hitters, pitchers


def _assign_hitters(hitters: list[dict]) -> list[dict]:
    """
    Assign hitters to active lineup slots, maximizing total z-score.

    Strategy: greedy assignment.
    1. Sort all hitters by totalz descending.
    2. For each positional slot (C, 1B, 2B, 3B, SS, OF x3), pick the
       highest-totalz eligible player not yet assigned.
    3. For Util x3, pick the highest-totalz remaining hitter (any position).

    Args:
        hitters: List of hitter player dicts

    Returns:
        List of player dicts assigned to active hitting slots (up to 11)
    """
    # Sort by totalz descending; use name as tiebreaker for determinism
    pool = sorted(hitters, key=lambda p: (-_safe_z(p), p["name"]))
    assigned: list[dict] = []
    used: set[str] = set()  # Track by player name

    for slot_name, count, eligible_positions in HITTING_SLOTS:
        filled = 0
        for player in pool:
            if filled >= count:
                break
            if player["name"] in used:
                continue
            if player["pos"] in eligible_positions:
                assigned.append(player)
                used.add(player["name"])
                filled += 1

    return assigned


def _assign_pitchers(pitchers: list[dict]) -> list[dict]:
    """
    Assign pitchers to active lineup slots, maximizing total z-score.

    Strategy: greedy assignment.
    1. Sort all pitchers by totalz descending.
    2. For SP x3, pick the highest-totalz SP-eligible pitchers.
    3. For RP x2, pick the highest-totalz RP-eligible pitchers.
    4. For P x3, pick the highest-totalz remaining pitchers (any).

    Args:
        pitchers: List of pitcher player dicts

    Returns:
        List of player dicts assigned to active pitching slots (up to 8)
    """
    pool = sorted(pitchers, key=lambda p: (-_safe_z(p), p["name"]))
    assigned: list[dict] = []
    used: set[str] = set()

    for slot_name, count, eligible_positions in PITCHING_SLOTS:
        filled = 0
        for player in pool:
            if filled >= count:
                break
            if player["name"] in used:
                continue
            if player["pos"] in eligible_positions:
                assigned.append(player)
                used.add(player["name"])
                filled += 1

    return assigned


def _safe_z(player: dict) -> float:
    """Return totalz for a player, defaulting to 0.0 if None."""
    val = player.get("totalz")
    return float(val) if val is not None else 0.0


def solve_optimal_lineup(
    roster_players: list[dict],
    player_db: dict,
) -> tuple[list[dict], list[dict]]:
    """
    Solve the optimal active lineup for a team.

    Given the full roster (including BN/IL/NA players) and the player
    projection database, assign players to active slots to maximize total
    z-score.

    Args:
        roster_players: List of {"name": str, "pos": str} from a team's roster
        player_db: Dict from load_player_db()

    Returns:
        (active_hitters, active_pitchers) -- each a list of player dicts
    """
    hitters, pitchers = _resolve_roster_players(roster_players, player_db)
    active_hitters = _assign_hitters(hitters)
    active_pitchers = _assign_pitchers(pitchers)
    return active_hitters, active_pitchers
