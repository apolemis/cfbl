#!/usr/bin/env python3
"""
run_week.py -- CLI script to generate weekly CFBL power rankings and matchup predictions.

Usage:
    python3 -m app.scripts.run_week --week 1
    python3 -m app.scripts.run_week --week 5

Run from the project root (/Users/anthony/cfbl/).

Steps:
1. Load player projections database
2. Load team rosters
3. Load previous week's rankings (if week > 1) for rank deltas
4. Generate round-robin power rankings
5. Generate matchup predictions for the week
6. Save rankings JSON to app/data/rankings/week{NN}.json
7. Save matchups JSON to app/data/matchups/week{NN}.json
8. Print summary to console
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from app.simulation.projections import load_player_db
from app.simulation.rosters import get_teams, get_matchups
from app.simulation.engine import (
    generate_power_rankings,
    generate_matchup_predictions,
)


# --- Week label mapping ---
# Season starts March 25, 2026. Each week is ~7 days.
# Adjust these as the schedule firms up.
WEEK_LABELS = {
    1: "Week 1 (Mar 25 - Mar 29)",
    2: "Week 2 (Mar 30 - Apr 5)",
    3: "Week 3 (Apr 6 - Apr 12)",
    4: "Week 4 (Apr 13 - Apr 19)",
    5: "Week 5 (Apr 20 - Apr 26)",
    6: "Week 6 (Apr 27 - May 3)",
    7: "Week 7 (May 4 - May 10)",
    8: "Week 8 (May 11 - May 17)",
    9: "Week 9 (May 18 - May 24)",
    10: "Week 10 (May 25 - May 31)",
    11: "Week 11 (Jun 1 - Jun 7)",
    12: "Week 12 (Jun 8 - Jun 14)",
    13: "Week 13 (Jun 15 - Jun 21)",
    14: "Week 14 (Jun 22 - Jun 28)",
    15: "Week 15 (Jun 29 - Jul 5)",
    16: "Week 16 (Jul 6 - Jul 12)",
    17: "Week 17 (Jul 13 - Jul 19)",
    18: "Week 18 (Jul 20 - Jul 26)",
    19: "Week 19 (Jul 27 - Aug 2)",
    20: "Week 20 (Aug 3 - Aug 9)",
    21: "Week 21 (Aug 10 - Aug 16)",
    22: "Week 22 (Aug 17 - Aug 23)",
    23: "Week 23 (Aug 24 - Aug 30)",
    24: "Week 24 (Aug 31 - Sep 6)",
    25: "Week 25 (Sep 7 - Sep 13)",
    26: "Week 26 (Sep 14 - Sep 20)",
}


# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RANKINGS_DIR = os.path.join(DATA_DIR, "rankings")
MATCHUPS_DIR = os.path.join(DATA_DIR, "matchups")


def _ensure_dirs() -> None:
    """Create output directories if they don't exist."""
    os.makedirs(RANKINGS_DIR, exist_ok=True)
    os.makedirs(MATCHUPS_DIR, exist_ok=True)


def _load_prev_rankings(week: int) -> dict | None:
    """Load the previous week's rankings JSON, or None if week 1 or file missing."""
    if week <= 1:
        return None
    prev_file = os.path.join(RANKINGS_DIR, f"week{week - 1:02d}.json")
    if not os.path.exists(prev_file):
        print(f"  Note: No previous rankings found at {prev_file}")
        return None
    with open(prev_file, "r") as f:
        return json.load(f)


def _format_delta(delta) -> str:
    """Format a rank delta for display."""
    if delta == "NEW":
        return "NEW"
    if isinstance(delta, (int, float)):
        if delta > 0:
            return f"+{delta}"
        elif delta < 0:
            return str(delta)
        else:
            return "--"
    return str(delta)


def run(week: int) -> None:
    """Main entry point: generate rankings and matchup predictions for a week."""
    _ensure_dirs()

    week_label = WEEK_LABELS.get(week, f"Week {week}")
    now = datetime.now(timezone.utc).isoformat()

    print(f"\n{'='*60}")
    print(f"  CFBL Simulation Engine -- {week_label}")
    print(f"{'='*60}\n")

    # Step 1: Load player database
    print("Loading player projections...")
    player_db = load_player_db()
    print(f"  {len(player_db)} players loaded.\n")

    # Step 2: Load teams
    print("Loading team rosters...")
    teams = get_teams()
    print(f"  {len(teams)} teams loaded.\n")

    # Step 3: Load previous rankings
    print("Loading previous rankings...")
    prev_rankings = _load_prev_rankings(week)
    if prev_rankings:
        print(f"  Loaded week {week - 1} rankings.\n")
    else:
        print("  No previous rankings (first week or file missing).\n")

    # Step 4: Generate power rankings
    print("Running round-robin simulation...")
    rankings_data = generate_power_rankings(teams, player_db, prev_rankings)
    rankings_data["week"] = week
    rankings_data["week_label"] = week_label
    rankings_data["generated_at"] = now
    print(f"  Power rankings generated for {len(rankings_data['rankings'])} teams.\n")

    # Step 5: Generate matchup predictions
    print("Generating matchup predictions...")
    try:
        matchup_pairs = get_matchups(week)
        matchups_data = generate_matchup_predictions(matchup_pairs, teams, player_db)
        matchups_data["week"] = week
        matchups_data["week_label"] = week_label
        print(f"  {len(matchups_data['matchups'])} matchups predicted.\n")
    except ValueError as e:
        print(f"  Warning: {e}")
        print("  Skipping matchup predictions.\n")
        matchups_data = {
            "week": week,
            "week_label": week_label,
            "matchups": [],
        }

    # Step 6: Save rankings JSON
    rankings_file = os.path.join(RANKINGS_DIR, f"week{week:02d}.json")
    with open(rankings_file, "w") as f:
        json.dump(rankings_data, f, indent=2)
    print(f"Rankings saved to {rankings_file}")

    # Step 7: Save matchups JSON
    matchups_file = os.path.join(MATCHUPS_DIR, f"week{week:02d}.json")
    with open(matchups_file, "w") as f:
        json.dump(matchups_data, f, indent=2)
    print(f"Matchups saved to {matchups_file}")

    # Step 8: Print summary
    _print_summary(rankings_data, matchups_data)


def _print_summary(rankings_data: dict, matchups_data: dict) -> None:
    """Print a console summary of rankings and matchups."""
    rankings = rankings_data["rankings"]

    print(f"\n{'='*60}")
    print("  POWER RANKINGS SUMMARY")
    print(f"{'='*60}\n")

    # Full rankings table
    print(f"  {'#':<4} {'Delta':<7} {'Team':<30} {'Record':<12} {'Win%':<7}")
    print(f"  {'-'*4} {'-'*7} {'-'*30} {'-'*12} {'-'*7}")
    for entry in rankings:
        delta_str = _format_delta(entry["delta"])
        print(
            f"  {entry['rank']:<4} {delta_str:<7} {entry['team_name']:<30} "
            f"{entry['matchup_record']:<12} {entry['win_pct']:<7.3f}"
        )

    # Top 3
    print(f"\n  Top 3:")
    for entry in rankings[:3]:
        print(
            f"    {entry['rank']}. {entry['team_name']} "
            f"({entry['matchup_record']}, {entry['cat_record']})"
        )
        print(f"       Strengths: {', '.join(entry['strengths'])}")
        print(f"       Weaknesses: {', '.join(entry['weaknesses'])}")

    # Biggest mover (largest positive delta)
    movers = [
        e for e in rankings
        if isinstance(e["delta"], (int, float)) and e["delta"] != 0
    ]
    if movers:
        biggest_up = max(movers, key=lambda e: e["delta"])
        if biggest_up["delta"] > 0:
            print(
                f"\n  Biggest Mover: {biggest_up['team_name']} "
                f"(+{biggest_up['delta']} spots, now #{biggest_up['rank']})"
            )
        biggest_down = min(movers, key=lambda e: e["delta"])
        if biggest_down["delta"] < 0:
            print(
                f"  Biggest Fall: {biggest_down['team_name']} "
                f"({biggest_down['delta']} spots, now #{biggest_down['rank']})"
            )

    # Lock of the week (matchup with biggest category margin)
    matchups = matchups_data.get("matchups", [])
    if matchups:
        print(f"\n{'='*60}")
        print("  MATCHUP PREDICTIONS")
        print(f"{'='*60}\n")

        best_margin = 0
        lock_matchup = None

        for m in matchups:
            score_parts = m["predicted_score"].split("-")
            wins_a = int(score_parts[0])
            wins_b = int(score_parts[1])
            margin = abs(wins_a - wins_b)

            fav = m["team_a"]["name"] if m["favorite"] == "team_a" else m["team_b"]["name"]
            dog = m["team_b"]["name"] if m["favorite"] == "team_a" else m["team_a"]["name"]

            if m["favorite"] == "even":
                fav = m["team_a"]["name"]
                dog = m["team_b"]["name"]

            print(
                f"  {m['team_a']['name']:<28} vs  {m['team_b']['name']:<28}"
            )
            print(
                f"    Score: {m['predicted_score']}  |  "
                f"ML: {m['moneyline_a']} / {m['moneyline_b']}"
            )

            if margin > best_margin:
                best_margin = margin
                lock_matchup = m

        if lock_matchup:
            if lock_matchup["favorite"] == "team_a":
                lock_team = lock_matchup["team_a"]["name"]
                lock_ml = lock_matchup["moneyline_a"]
            elif lock_matchup["favorite"] == "team_b":
                lock_team = lock_matchup["team_b"]["name"]
                lock_ml = lock_matchup["moneyline_b"]
            else:
                lock_team = lock_matchup["team_a"]["name"]
                lock_ml = lock_matchup["moneyline_a"]

            print(f"\n  Lock of the Week: {lock_team} ({lock_ml})")

    print(f"\n{'='*60}\n")


def main() -> None:
    """Parse CLI arguments and run."""
    parser = argparse.ArgumentParser(
        description="CFBL Weekly Simulation -- Generate power rankings and matchup predictions."
    )
    parser.add_argument(
        "--week",
        type=int,
        required=True,
        help="Week number to simulate (e.g. 1, 2, ...)",
    )
    args = parser.parse_args()

    if args.week < 1:
        print("Error: Week must be >= 1", file=sys.stderr)
        sys.exit(1)

    run(args.week)


if __name__ == "__main__":
    main()
