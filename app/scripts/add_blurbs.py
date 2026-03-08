#!/usr/bin/env python3
"""Add irreverent blurbs to rankings and matchup JSONs."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

RANKING_BLURBS = {
    8: (  # Universal Basic Civale — #1
        "The undisputed king of the CFBL sits atop his throne made of dingers and "
        "reliever ratios. Judge and Soto in the same lineup is genuinely unfair — "
        "that's a combined 90+ homers and an OBP that looks like a batting average "
        "from the steroid era. Harper, Freeman, and Riley just pile on. The pitching "
        "strategy is diabolical: only two real starters (Crochet and Webb) propped up "
        "by a fleet of elite relievers (Miller, Cade Smith, Abreu, Estrada) who keep "
        "the ERA at 3.30 and the SV+H flowing like rum punch at a beach bar. Wins and "
        "QS? Never heard of them. Don't need them. This team projected to beat EVERY "
        "SINGLE TEAM in the league in a head-to-head. 11-0 against the field. If you're "
        "playing against this squad, just set your lineup and look away. It'll be over soon."
    ),
    7: (  # Young and Yandy Indiana Drift — #2
        "The most balanced roster in the league, which in fantasy baseball is code for "
        "\"doesn't have a glaring weakness anyone can exploit.\" Bobby Witt Jr., Lindor, "
        "and Ketel Marte form a middle infield that would make most real MLB teams jealous, "
        "and Wheeler-Gilbert is a genuinely elite 1-2 punch on the mound. The depth is "
        "absurd — Olson, Kwan, Happ, Nimmo, Vientos all sitting on the bench like it's a "
        "fantasy baseball buffet. The only knock is that this team doesn't dominate any "
        "single category the way the top team does. They're the straight-A student who "
        "never gets a 100. Still, 8-1-2 against the field is nothing to sneeze at. "
        "The manager just needs to, you know, actually set their lineup."
    ),
    10: (  # Moo Moo Cowsers — #3
        "A sneaky-good roster that most people probably aren't paying attention to, kind of "
        "like the Cowsers name suggests. Altuve and Turner provide the veteran presence, "
        "Yamamoto-Valdez-Eovaldi is a rotation that actually generates Wins and QS (what a "
        "concept), and Hader-Devin Williams is a disgusting closer tandem. The offense isn't "
        "going to blow anyone away — there's no singular \"wow\" bat — but there are no easy "
        "outs either. Rooker is a sneaky HR contributor and Jac Caglianone is the kind of "
        "boom-or-bust prospect pick that either looks genius or gets dropped by Week 6. "
        "The Achilles heel? That OBP is rough. This team swings first and asks questions never."
    ),
    3: (  # Kings of Castillo and Leon — #4
        "Kyle Tucker is the engine, Corey Seager is the co-pilot, and everyone else is just "
        "along for the ride hoping the plane doesn't crash. Jackson Holliday and Corbin Carroll "
        "provide upside but also the kind of volatility that keeps you refreshing the app at 2am. "
        "The pitching is... interesting. Gausman and Castillo are solid but unspectacular, and "
        "the rest of the staff is a collection of names you'd find on a Triple-A all-star roster. "
        "The SV+H situation is a catastrophe — 0.5 projected saves+holds for the entire season. "
        "That's not a strategy, that's a cry for help. If this team figures out the bullpen, "
        "they could move up. If they don't, well, enjoy that sweet QS total nobody else cares about."
    ),
    1: (  # Nine Spoons One Brûlée — #5
        "Paul Skenes and Ohtani (the pitching version) headline a rotation that generates Ks "
        "like a broken batting cage machine. 1,130 strikeouts projected — that's an absurd "
        "number. Cole Ragans and Ryan Pepiot quietly add depth. The problem? The offense looks "
        "like it was assembled from the clearance rack at a fantasy baseball yard sale. Gunnar "
        "Henderson is fantastic, but after that it's Jazz Chisholm (when he's not hurt), "
        "Brenton Doyle (who hits like he's swinging a pool noodle), and a bunch of question "
        "marks. 639 projected RBI is dead last. This is the fantasy equivalent of a team "
        "that wins 1-0 every night — exciting if you're a pitching nerd, depressing if "
        "you enjoy watching runs score."
    ),
    11: (  # Señor Burns — #6
        "Chris Sale, Bryan Woo, George Kirby, Aaron Nola, Shota Imanaga — this is the kind "
        "of rotation that wins you Wins, QS, and K while you sit back and sip your cafecito. "
        "The K/BB ratio (4.2) is the best in the league by a mile. The hitting is anchored "
        "by Vlad Jr. and Arraez, two of the best pure hitters in baseball, but this team is "
        "allergic to stolen bases (85 projected — worst in the league). That 674 R total "
        "isn't great either. This roster screams \"I dominated my league in 2018\" with its "
        "old-school reliance on pitching and contact hitting. In a league that rewards SB "
        "and SLG, this approach is fighting with one hand tied behind its back. Still, when "
        "Sale and Kirby are dealing, nobody wants this smoke."
    ),
    6: (  # Implicitly Explicit — #7
        "This team has more talent on the bench than some teams have in their starting lineup. "
        "Devers, Riley Greene, Manny Machado, Spencer Strider, Bryce Miller, Roki Sasaki — "
        "all just... sitting there. On the bench. ALL of them. The lineup isn't set. It's "
        "Week 1, my brother. This is like showing up to a potluck and leaving your dish in "
        "the car. The raw talent here is probably top-4 in the league when optimally deployed, "
        "but the \"when\" is doing heavy lifting. The prospect stash (Bazzana, Basallo, "
        "Eldridge, Crews) is the best in the CFBL and suggests this manager is playing the "
        "long game. Unfortunately, the long game doesn't win you matchups in March. Set. "
        "Your. Lineup."
    ),
    5: (  # CLAUDE 4 COMMISH — #8
        "On paper, this should be the best team in the league. Ohtani (batter), Acuna, Tatis, "
        "Elly De La Cruz — that's 170 combined stolen bases and a highlight reel that would "
        "break Twitter. Gerrit Cole adds ace-level pitching. So why is this team ranked 8th? "
        "Because the rest of the roster is held together with duct tape and prayers. The SV+H "
        "total of 1.1 is not a typo — this team has essentially ZERO relievers. The K/BB ratio "
        "(3.07) is ugly. Glasnow and Snell are boom-or-bust arms that could easily bust. "
        "This team is the sports car with no brakes — thrilling to watch, terrifying to rely on. "
        "The stolen base title is theirs for the taking, but you can't steal your way out of "
        "a 3.85 ERA."
    ),
    4: (  # PO' BOYD SANDWICH — #9
        "Yordan Alvarez and Kyle Schwarber provide the power, CJ Abrams provides the speed, "
        "and the bench provides... more pitchers than a Little League tournament. Seriously, "
        "there are 15 pitchers on this roster, including Max Fried, Kyle Bradish, Michael King, "
        "Carlos Rodon, and Freddy Peralta — ALL ON THE BENCH. None of them in active pitching "
        "slots. The only active pitchers are two relievers (Chapman and Iglesias). This is either "
        "a 4D chess move that hasn't been deployed yet, or someone forgot that starting pitchers "
        "need to be, you know, started. The raw SP depth is elite if properly activated, but "
        "right now this team is bringing a knife to a gunfight and leaving the gun at home."
    ),
    9: (  # Duran Duran — #10
        "Jose Ramirez, Mookie Betts, and Jarren Duran — that's a legitimate core that "
        "generates R, HR, RBI, and SB. But after the top three, this roster falls off a cliff "
        "faster than Duran Duran's career after \"Rio.\" The pitching is a war crime. Gavin "
        "Williams, Trevor Rogers, and Cade Horton as your SP1-SP2-SP3? That's a combined ERA "
        "that'll make your eyes water. The saving grace is a loaded bullpen (Edwin Diaz, "
        "Jhoan Duran, Kenley Jansen, Carlos Estevez) that racks up SV+H like nobody's business "
        "(167.8 — second in the league). But the 26.5 QS projection is historically bad. "
        "This team is a relief pitcher with a dream and a prayer."
    ),
    2: (  # Boydz n the Hood — #11
        "Tarik Skubal is a legitimate ace. That's the nice part. The rest of this roster reads "
        "like a keeper league that's been tanking for three years. Corbin Burnes is on the IL, "
        "Jared Jones is on the IL, and the remaining \"depth\" is Jack Flaherty, Edward Cabrera, "
        "and a prayer candle. The offense is carried by Julio Rodriguez and Oneil Cruz — two "
        "electric talents surrounded by Spencer Torkelson (yikes), Kazuma Okamoto (bold), and "
        "Drake Baldwin catching. The prospect stash (Max Clark, Sebastian Walcott, JJ Wetherholt) "
        "says \"trust the process,\" but the 1-8-2 record against the field says \"the process "
        "isn't working yet.\" This is a rebuild. Embrace it."
    ),
    12: (  # ShawSwank Redemption — #12
        "0-11. Zero. Wins. Against. The. Field. This roster is the fantasy equivalent of showing "
        "up to a sword fight with a pool noodle. The marquee \"aces\" are Brandon Woodruff "
        "(hasn't thrown a meaningful pitch since 2023), Robbie Ray (same), and Sandy Alcantara "
        "(please refer to previous parenthetical). The offense features Lawrence Butler and "
        "Matt Shaw as the headliners, which is the kind of thing you say when you don't have "
        "headliners. The stolen base total (162) is actually impressive, but it's like being "
        "the fastest runner on a sinking ship. The team name promises redemption, but the "
        "projections promise pain. At least Kyle Teel and Jordan Lawlar give you something "
        "to dream about for 2027."
    ),
}

MATCHUP_BLURBS = {
    (8, 9): (  # Universal Basic Civale vs Duran Duran
        "Tony's juggernaut opens the season against Duran Duran, and this matchup has "
        "\"mercy rule\" written all over it. Universal Basic Civale projects to win 12 of 14 "
        "active categories — losing only SB (Duran's one trick) and SV+H (Duran's loaded "
        "bullpen). Judge and Soto alone will out-homer Duran Duran's entire lineup. The ERA "
        "gap (3.30 vs 3.83) is a full half-run, and the OBP gap (.358 vs .329) is a canyon. "
        "If you're Gio, the best strategy might be to just not look at the scoreboard until "
        "next Monday."
    ),
    (1, 7): (  # Nine Spoons One Brûlée vs Young and Yandy Indiana Drift
        "A fascinating clash of styles: Nine Spoons brings the pitching firepower (Skenes, "
        "Ohtani-P, 1,130 K) while Young and Yandy counters with the most balanced offense in "
        "the league. The Drift's hitting advantage is massive — 842 RBI vs 639, 243 HR vs 199, "
        "893 R vs 657. Nine Spoons takes the pitching cats (ERA, WHIP, QS, K) but loses "
        "basically every hitting category. When your offense is getting outscored by 200+ runs, "
        "no amount of K's will save you. Young and Yandy should cruise, but they need to "
        "actually set their lineup first. Details, details."
    ),
    (2, 11): (  # Boydz n the Hood vs Señor Burns
        "The battle of the bottom half, and it's not pretty. Boydz brings a Skubal-led rotation "
        "that wins ERA but loses basically everything else. Señor Burns has the superior pitching "
        "staff (Sale, Woo, Kirby, Nola) and it shows — they take W, K, WHIP, K/BB, QS, and "
        "SV+H. Boydz manages to eke out ERA, RBI, SB, and HR, but it's not enough. The 4-10 "
        "projected score is ugly. Boydz n the Hood is bringing a starter to a full-roster fight. "
        "With Burnes on the IL, this team is just waiting for reinforcements that may come too late."
    ),
    (3, 6): (  # Kings of Castillo and Leon vs Implicitly Explicit
        "The closest matchup of the week, projected at 8-6. Kings have Tucker and Seager "
        "driving the offense, winning SB, HR, AVG, OBP, SLG, and R — basically every hitting "
        "category that matters. Implicitly Explicit counters with raw pitching volume "
        "(1,270 K from Strider, Greene, Miller, Cease and company) and wins ERA, W, QS, K, "
        "and SV+H. But here's the thing — Implicitly Explicit still hasn't set their lineup. "
        "If they actually slot their players in, this could flip. If they don't, well, you "
        "can't win categories with benched players. Kings should take this, but it's not a lock."
    ),
    (4, 5): (  # PO' BOYD SANDWICH vs CLAUDE 4 COMMISH
        "The true pick'em of Week 1 — dead even at 7-7. PO' BOYD brings the pitching depth "
        "(76 W, 1,116 K, 75 QS) while CLAUDE 4 COMMISH brings the offensive fireworks "
        "(Ohtani, Acuna, Tatis, Elly = 170 SB and 238 HR). It's the classic \"pitching vs "
        "hitting\" battle that makes H2H fantasy so fun. CLAUDE takes R, HR, RBI, SB, AVG, "
        "OBP, SLG — basically the entire hitting side. PO' BOYD takes ERA, WHIP, W, QS, K, "
        "K/BB, SV+H — basically the entire pitching side. Whoever wins this matchup is the team "
        "that steals one extra category. This is going to be a war."
    ),
    (10, 12): (  # Moo Moo Cowsers vs ShawSwank Redemption
        "This is what happens when the #3 team draws the #12 team in Week 1: a projected "
        "12-2 beatdown. Moo Moo Cowsers wins literally every category except SB and K (barely). "
        "ShawSwank's roster of comeback pitchers (Woodruff, Ray, Alcantara) and replacement-level "
        "hitters simply cannot compete with Altuve, Turner, Yamamoto, and Hader. This is the "
        "matchup equivalent of a preseason game — it's technically competitive, but everyone "
        "knows how it ends. ShawSwank's only hope is that Woodruff suddenly looks like 2023 "
        "Woodruff. Spoiler: the projections do not think that will happen."
    ),
}

def main():
    # Update rankings
    rankings_file = DATA_DIR / "rankings" / "week01.json"
    rankings = json.loads(rankings_file.read_text())

    for team in rankings["rankings"]:
        tid = team["team_id"]
        if tid in RANKING_BLURBS:
            team["blurb"] = RANKING_BLURBS[tid]

    rankings_file.write_text(json.dumps(rankings, indent=2, ensure_ascii=False))
    print(f"Updated {len(RANKING_BLURBS)} ranking blurbs")

    # Update matchups
    matchups_file = DATA_DIR / "matchups" / "week01.json"
    matchups = json.loads(matchups_file.read_text())

    # Also add lock_of_the_week
    matchups["lock_of_the_week"] = (
        "Universal Basic Civale (-500) over Duran Duran"
    )

    for m in matchups["matchups"]:
        key = (m["team_a"]["id"], m["team_b"]["id"])
        if key in MATCHUP_BLURBS:
            m["blurb"] = MATCHUP_BLURBS[key]

    matchups_file.write_text(json.dumps(matchups, indent=2, ensure_ascii=False))
    print(f"Updated {len(MATCHUP_BLURBS)} matchup blurbs")
    print("Lock of the week: Universal Basic Civale (-500) over Duran Duran")

if __name__ == "__main__":
    main()
