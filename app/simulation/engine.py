"""
engine.py -- Core simulation engine for CFBL fantasy baseball.

Provides:
- aggregate_team_stats: Compute projected team totals for all scoring categories
- compare_teams: Head-to-head category comparison between two teams
- compute_moneyline: Convert category margin into moneyline odds
- generate_power_rankings: Round-robin simulation across all teams
- generate_matchup_predictions: Predict outcomes for a week's matchups

League format: 8x8 H2H categories
    Hitting:  R, HR, RBI, SB, AVG, OBP, SLG, CYC
    Pitching: W, K, ERA, WHIP, K/BB, NH, QS, SV+H

CYC (cycles) and NH (no-hitters) are lottery categories that almost always
tie 0-0, so they are treated as automatic ties in simulation (14 active
categories + 2 auto-ties = 16 total).
"""

from __future__ import annotations

from datetime import datetime, timezone
from itertools import combinations
from typing import Optional

from app.simulation.lineup import solve_optimal_lineup


# --- Category configuration ---

# Categories where higher is better
HIGHER_IS_BETTER = {"r", "hr", "rbi", "sb", "avg", "obp", "slg", "w", "k", "kbb", "qs", "svh"}

# Categories where lower is better
LOWER_IS_BETTER = {"era", "whip"}

# All 14 active sim categories (excludes CYC and NH lottery cats)
ACTIVE_CATEGORIES = HIGHER_IS_BETTER | LOWER_IS_BETTER

# Display names for categories (for output / breakdowns)
CATEGORY_DISPLAY = {
    "r": "R",
    "hr": "HR",
    "rbi": "RBI",
    "sb": "SB",
    "avg": "AVG",
    "obp": "OBP",
    "slg": "SLG",
    "w": "W",
    "k": "K",
    "era": "ERA",
    "whip": "WHIP",
    "kbb": "K/BB",
    "qs": "QS",
    "svh": "SV+H",
}

# Hitting counting stats (summed directly)
HITTING_COUNTING = {"r", "hr", "rbi", "sb"}

# Pitching counting stats (summed directly)
PITCHING_COUNTING = {"w", "k", "qs", "svh"}


def _safe_float(val, default: float = 0.0) -> float:
    """Convert a value to float, returning default if None or non-numeric."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Team stat aggregation
# ---------------------------------------------------------------------------

def aggregate_team_stats(
    active_hitters: list[dict],
    active_pitchers: list[dict],
) -> dict:
    """
    Compute projected team totals for all 14 scoring categories.

    Counting stats are summed. Rate stats are weighted:
    - AVG, SLG: weighted by AB
    - OBP: weighted by PA
    - ERA, WHIP: weighted by IP
    - K/BB: total K / total BB (derived from individual K and K/BB)

    Args:
        active_hitters: List of hitter player dicts in the active lineup
        active_pitchers: List of pitcher player dicts in the active lineup

    Returns:
        Dict with keys: r, hr, rbi, sb, avg, obp, slg, w, k, era, whip, kbb, qs, svh
    """
    stats: dict[str, float] = {}

    # --- Hitting counting stats ---
    for cat in HITTING_COUNTING:
        stats[cat] = sum(_safe_float(p.get(cat)) for p in active_hitters)

    # --- Hitting rate stats (weighted averages) ---
    total_ab = sum(_safe_float(p.get("ab")) for p in active_hitters)
    total_pa = sum(_safe_float(p.get("pa")) for p in active_hitters)

    if total_ab > 0:
        stats["avg"] = sum(
            _safe_float(p.get("avg")) * _safe_float(p.get("ab"))
            for p in active_hitters
        ) / total_ab
        stats["slg"] = sum(
            _safe_float(p.get("slg")) * _safe_float(p.get("ab"))
            for p in active_hitters
        ) / total_ab
    else:
        stats["avg"] = 0.0
        stats["slg"] = 0.0

    if total_pa > 0:
        stats["obp"] = sum(
            _safe_float(p.get("obp")) * _safe_float(p.get("pa"))
            for p in active_hitters
        ) / total_pa
    else:
        stats["obp"] = 0.0

    # --- Pitching counting stats ---
    for cat in PITCHING_COUNTING:
        stats[cat] = sum(_safe_float(p.get(cat)) for p in active_pitchers)

    # --- Pitching rate stats (weighted by IP) ---
    total_ip = sum(_safe_float(p.get("ip")) for p in active_pitchers)

    if total_ip > 0:
        stats["era"] = sum(
            _safe_float(p.get("era")) * _safe_float(p.get("ip"))
            for p in active_pitchers
        ) / total_ip
        stats["whip"] = sum(
            _safe_float(p.get("whip")) * _safe_float(p.get("ip"))
            for p in active_pitchers
        ) / total_ip
    else:
        stats["era"] = 0.0
        stats["whip"] = 0.0

    # --- K/BB (total K / total BB) ---
    # Derive individual BB from K and K/BB: BB = K / (K/BB)
    total_k = stats["k"]
    total_bb = 0.0
    for p in active_pitchers:
        p_k = _safe_float(p.get("k"))
        p_kbb = _safe_float(p.get("kbb"))
        if p_kbb > 0 and p_k > 0:
            total_bb += p_k / p_kbb

    stats["kbb"] = (total_k / total_bb) if total_bb > 0 else 0.0

    return stats


# ---------------------------------------------------------------------------
# Head-to-head comparison
# ---------------------------------------------------------------------------

def compare_teams(
    stats_a: dict,
    stats_b: dict,
) -> tuple[int, int, int]:
    """
    Compare two teams across all 16 categories (14 active + 2 lottery ties).

    For the 14 active categories:
    - Higher is better: r, hr, rbi, sb, avg, obp, slg, w, k, kbb, qs, svh
    - Lower is better: era, whip
    - Ties go to ties column

    CYC and NH are auto-tied (lottery categories).

    Args:
        stats_a: Team A aggregated stats dict
        stats_b: Team B aggregated stats dict

    Returns:
        (wins_a, wins_b, ties) -- sums to 16
    """
    wins_a = 0
    wins_b = 0
    ties = 0

    for cat in ACTIVE_CATEGORIES:
        val_a = _safe_float(stats_a.get(cat))
        val_b = _safe_float(stats_b.get(cat))

        if cat in LOWER_IS_BETTER:
            # Lower is better: flip comparison
            # Edge case: if both are 0 (e.g. no IP), treat as tie
            if val_a == 0.0 and val_b == 0.0:
                ties += 1
            elif val_a < val_b:
                wins_a += 1
            elif val_b < val_a:
                wins_b += 1
            else:
                ties += 1
        else:
            # Higher is better
            if val_a > val_b:
                wins_a += 1
            elif val_b > val_a:
                wins_b += 1
            else:
                ties += 1

    # Add 2 automatic ties for CYC and NH (lottery categories)
    ties += 2

    return wins_a, wins_b, ties


def compare_teams_detail(
    stats_a: dict,
    stats_b: dict,
) -> dict:
    """
    Category-by-category breakdown of a head-to-head matchup.

    Returns a dict keyed by display category name with:
        {display_name: {"a": val_a, "b": val_b, "edge": "a" | "b" | "tie"}}
    """
    breakdown: dict[str, dict] = {}

    for cat in ACTIVE_CATEGORIES:
        val_a = _safe_float(stats_a.get(cat))
        val_b = _safe_float(stats_b.get(cat))
        display = CATEGORY_DISPLAY[cat]

        if cat in LOWER_IS_BETTER:
            if val_a == 0.0 and val_b == 0.0:
                edge = "tie"
            elif val_a < val_b:
                edge = "a"
            elif val_b < val_a:
                edge = "b"
            else:
                edge = "tie"
        else:
            if val_a > val_b:
                edge = "a"
            elif val_b > val_a:
                edge = "b"
            else:
                edge = "tie"

        breakdown[display] = {
            "a": round(val_a, 3),
            "b": round(val_b, 3),
            "edge": edge,
        }

    # Add lottery categories as auto-ties
    breakdown["CYC"] = {"a": 0, "b": 0, "edge": "tie"}
    breakdown["NH"] = {"a": 0, "b": 0, "edge": "tie"}

    return breakdown


# ---------------------------------------------------------------------------
# Moneyline computation
# ---------------------------------------------------------------------------

def compute_moneyline(wins_a: int, wins_b: int) -> tuple[str, str]:
    """
    Convert category win margin into moneyline odds for both sides.

    The team with more category wins is the favorite (negative line).
    Margin thresholds:
        11+ category wins -> -500 / +400
        10 category wins  -> -300 / +250
        9  category wins  -> -200 / +170
        8  category wins  -> -140 / +120
        7 or fewer        -> -110 / +100 (pick'em)

    Args:
        wins_a: Team A category wins (out of 16 total including ties)
        wins_b: Team B category wins

    Returns:
        (moneyline_a, moneyline_b) as formatted strings (e.g. "-200", "+170")
    """
    # Determine which team is favored and by how much
    if wins_a > wins_b:
        fav_wins = wins_a
    elif wins_b > wins_a:
        fav_wins = wins_b
    else:
        # Dead even
        return ("-110", "-110")

    if fav_wins >= 11:
        fav_line, dog_line = "-500", "+400"
    elif fav_wins >= 10:
        fav_line, dog_line = "-300", "+250"
    elif fav_wins >= 9:
        fav_line, dog_line = "-200", "+170"
    elif fav_wins >= 8:
        fav_line, dog_line = "-140", "+120"
    else:
        fav_line, dog_line = "-110", "+100"

    if wins_a > wins_b:
        return (fav_line, dog_line)
    else:
        return (dog_line, fav_line)


# ---------------------------------------------------------------------------
# Power rankings (round-robin simulation)
# ---------------------------------------------------------------------------

def _build_team_stats_cache(
    teams: list[dict],
    player_db: dict,
) -> dict[int, dict]:
    """
    For each team, solve the optimal lineup and aggregate stats.

    Returns:
        Dict keyed by team_id -> aggregated stats dict
    """
    cache: dict[int, dict] = {}
    for team in teams:
        active_h, active_p = solve_optimal_lineup(team["players"], player_db)
        cache[team["id"]] = aggregate_team_stats(active_h, active_p)
    return cache


def generate_power_rankings(
    teams: list[dict],
    player_db: dict,
    prev_rankings: Optional[dict] = None,
) -> dict:
    """
    Run a round-robin simulation and produce power rankings.

    Steps:
    1. For each team, solve optimal lineup and aggregate stats.
    2. Compare every team vs every other team (N*(N-1)/2 matchups).
    3. Track per-team: category W/L/T, matchup W/L/T.
    4. Rank by matchup win pct (primary), category win pct (tiebreaker).
    5. Compute rank delta from prev_rankings if provided.
    6. Identify top 3 strengths and top 3 weaknesses per team.

    Args:
        teams: List of team dicts from get_teams()
        player_db: Dict from load_player_db()
        prev_rankings: Previous week's rankings dict (optional)

    Returns:
        Dict with "rankings" list and metadata
    """
    # Step 1: Build stats cache
    stats_cache = _build_team_stats_cache(teams, player_db)

    # Build team name lookup
    team_names = {t["id"]: t["name"] for t in teams}
    team_ids = [t["id"] for t in teams]

    # Step 2 & 3: Round-robin comparisons
    records: dict[int, dict] = {}
    for tid in team_ids:
        records[tid] = {
            "cat_wins": 0,
            "cat_losses": 0,
            "cat_ties": 0,
            "matchup_wins": 0,
            "matchup_losses": 0,
            "matchup_ties": 0,
        }

    for id_a, id_b in combinations(team_ids, 2):
        wins_a, wins_b, ties = compare_teams(stats_cache[id_a], stats_cache[id_b])

        # Category records
        records[id_a]["cat_wins"] += wins_a
        records[id_a]["cat_losses"] += wins_b
        records[id_a]["cat_ties"] += ties

        records[id_b]["cat_wins"] += wins_b
        records[id_b]["cat_losses"] += wins_a
        records[id_b]["cat_ties"] += ties

        # Matchup records (who won the H2H)
        if wins_a > wins_b:
            records[id_a]["matchup_wins"] += 1
            records[id_b]["matchup_losses"] += 1
        elif wins_b > wins_a:
            records[id_b]["matchup_wins"] += 1
            records[id_a]["matchup_losses"] += 1
        else:
            records[id_a]["matchup_ties"] += 1
            records[id_b]["matchup_ties"] += 1

    # Step 4: Sort by matchup win pct, then category win pct
    def _win_pct(w: int, l: int, t: int) -> float:
        total = w + l + t
        return (w + 0.5 * t) / total if total > 0 else 0.0

    ranked_ids = sorted(
        team_ids,
        key=lambda tid: (
            _win_pct(
                records[tid]["matchup_wins"],
                records[tid]["matchup_losses"],
                records[tid]["matchup_ties"],
            ),
            _win_pct(
                records[tid]["cat_wins"],
                records[tid]["cat_losses"],
                records[tid]["cat_ties"],
            ),
        ),
        reverse=True,
    )

    # Step 5: Compute deltas from previous rankings
    prev_rank_map: dict[int, int] = {}
    if prev_rankings and "rankings" in prev_rankings:
        for entry in prev_rankings["rankings"]:
            prev_rank_map[entry["team_id"]] = entry["rank"]

    # Step 6: Identify strengths and weaknesses per team
    # Compute league averages for each category
    league_avgs: dict[str, float] = {}
    for cat in ACTIVE_CATEGORIES:
        vals = [_safe_float(stats_cache[tid].get(cat)) for tid in team_ids]
        league_avgs[cat] = sum(vals) / len(vals) if vals else 0.0

    def _get_strengths_weaknesses(team_stats: dict) -> tuple[list[str], list[str]]:
        """Return top 3 strengths and top 3 weaknesses as display names."""
        # Compute z-score-like deviation from league average for each category
        deviations: list[tuple[str, float]] = []
        for cat in ACTIVE_CATEGORIES:
            val = _safe_float(team_stats.get(cat))
            avg = league_avgs[cat]

            if avg == 0.0:
                dev = 0.0
            elif cat in LOWER_IS_BETTER:
                # For ERA/WHIP, lower is better: negative deviation = strength
                dev = -(val - avg) / abs(avg) if avg != 0 else 0.0
            else:
                dev = (val - avg) / abs(avg) if avg != 0 else 0.0

            deviations.append((CATEGORY_DISPLAY[cat], dev))

        # Sort: highest deviation = biggest strength
        deviations.sort(key=lambda x: x[1], reverse=True)
        strengths = [d[0] for d in deviations[:3]]
        weaknesses = [d[0] for d in deviations[-3:]]
        # Reverse weaknesses so worst is first
        weaknesses.reverse()

        return strengths, weaknesses

    # Build rankings list
    rankings_list = []
    for rank_idx, tid in enumerate(ranked_ids, start=1):
        rec = records[tid]
        team_stats = stats_cache[tid]
        strengths, weaknesses = _get_strengths_weaknesses(team_stats)

        m_w = rec["matchup_wins"]
        m_l = rec["matchup_losses"]
        m_t = rec["matchup_ties"]
        c_w = rec["cat_wins"]
        c_l = rec["cat_losses"]
        c_t = rec["cat_ties"]

        win_pct = _win_pct(m_w, m_l, m_t)

        # Delta from previous week
        prev_rank = prev_rank_map.get(tid)
        if prev_rank is not None:
            delta = prev_rank - rank_idx  # positive = moved up
        else:
            delta = "NEW"

        # Round team totals for cleaner output
        rounded_totals = {}
        for cat in ACTIVE_CATEGORIES:
            val = _safe_float(team_stats.get(cat))
            if cat in ("avg", "obp", "slg", "era", "whip", "kbb"):
                rounded_totals[cat] = round(val, 3)
            else:
                rounded_totals[cat] = round(val, 1)

        rankings_list.append({
            "rank": rank_idx,
            "prev_rank": prev_rank,
            "delta": delta,
            "team_id": tid,
            "team_name": team_names[tid],
            "matchup_record": f"{m_w}-{m_l}-{m_t}",
            "cat_record": f"{c_w}-{c_l}-{c_t}",
            "win_pct": round(win_pct, 3),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "team_totals": rounded_totals,
            "blurb": "Blurb coming soon...",
        })

    return {
        "rankings": rankings_list,
    }


# ---------------------------------------------------------------------------
# Matchup predictions
# ---------------------------------------------------------------------------

def generate_matchup_predictions(
    matchup_pairs: list[list[int]],
    teams: list[dict],
    player_db: dict,
) -> dict:
    """
    Generate predictions for a set of weekly matchups.

    For each matchup pair:
    1. Solve optimal lineups and aggregate stats for both teams.
    2. Compare categories head-to-head.
    3. Generate moneyline odds based on category margin.
    4. Build per-category breakdown.

    Args:
        matchup_pairs: List of [team_a_id, team_b_id] pairs
        teams: List of team dicts from get_teams()
        player_db: Dict from load_player_db()

    Returns:
        Dict with "matchups" list
    """
    # Build lookup
    team_lookup = {t["id"]: t for t in teams}

    # Stats cache (reuse if same team appears in multiple contexts)
    stats_cache: dict[int, dict] = {}

    def _get_stats(team_id: int) -> dict:
        if team_id not in stats_cache:
            team = team_lookup[team_id]
            active_h, active_p = solve_optimal_lineup(team["players"], player_db)
            stats_cache[team_id] = aggregate_team_stats(active_h, active_p)
        return stats_cache[team_id]

    matchups_list = []

    for pair in matchup_pairs:
        id_a, id_b = pair[0], pair[1]
        team_a = team_lookup[id_a]
        team_b = team_lookup[id_b]

        stats_a = _get_stats(id_a)
        stats_b = _get_stats(id_b)

        wins_a, wins_b, ties = compare_teams(stats_a, stats_b)
        ml_a, ml_b = compute_moneyline(wins_a, wins_b)
        breakdown = compare_teams_detail(stats_a, stats_b)

        # Determine favorite
        if wins_a > wins_b:
            favorite = "team_a"
        elif wins_b > wins_a:
            favorite = "team_b"
        else:
            favorite = "even"

        matchups_list.append({
            "team_a": {"id": id_a, "name": team_a["name"]},
            "team_b": {"id": id_b, "name": team_b["name"]},
            "predicted_score": f"{wins_a}-{wins_b}-{ties}",
            "favorite": favorite,
            "moneyline_a": ml_a,
            "moneyline_b": ml_b,
            "cat_breakdown": breakdown,
            "blurb": "Blurb coming soon...",
        })

    return {
        "matchups": matchups_list,
    }
