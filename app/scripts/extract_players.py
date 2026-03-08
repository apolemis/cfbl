#!/usr/bin/env python3
"""Extract PLAYERS array from draft-board.html into players.json"""
import json
import re
from pathlib import Path

DRAFT_BOARD = Path.home() / "Downloads" / "draft-board.html"
OUTPUT = Path(__file__).parent.parent / "data" / "players.json"

def extract():
    content = DRAFT_BOARD.read_text(encoding="utf-8")

    # Find PLAYERS=[...] on line 272
    idx = content.find("PLAYERS=[")
    if idx == -1:
        raise ValueError("Could not find PLAYERS=[ in draft-board.html")

    array_start = content.find("[", idx)

    # Find matching closing bracket
    depth = 0
    for i in range(array_start, len(content)):
        ch = content[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                array_end = i + 1
                break

    raw = content[array_start:array_end]

    # Fix JS -> JSON: replace unquoted keys, handle null/true/false (already valid JSON)
    # The PLAYERS array uses JSON-compatible syntax, so json.loads should work
    players = json.loads(raw)

    OUTPUT.write_text(json.dumps(players, indent=2), encoding="utf-8")
    print(f"Extracted {len(players)} players to {OUTPUT}")

    # Quick stats
    hitters = [p for p in players if p.get("type") == "H"]
    pitchers = [p for p in players if p.get("type") == "P"]
    print(f"  Hitters: {len(hitters)}, Pitchers: {len(pitchers)}")

    # Show a few sample names
    for p in players[:5]:
        print(f"  #{p.get('rank', '?')} {p['name']} ({p.get('pos')}) - totalz: {p.get('totalz')}")

if __name__ == "__main__":
    extract()
