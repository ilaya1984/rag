import json
from datetime import datetime
import copy


import json
import uuid
from datetime import datetime

import json
import uuid
from datetime import datetime

import json
import uuid
from datetime import datetime

class CricketMatchManager:
    def __init__(self, match_id, team_a, team_b, venue, city, ground_type, match_type, overs_limit=5, ball_type="leather"):
        self.match = {
            "match_id": match_id,
            "teams": {
                "team_a": team_a,
                "team_b": team_b
            },
            "venue": venue,
            "city": city,
            "ground_type": ground_type,
            "match_type": match_type,
            "overs_limit": overs_limit,
            "ball_type": ball_type,
            "squads": {
                "team_a": {},
                "team_b": {}
            },
            "innings": {},
            "history": [],
            "last_updated": datetime.utcnow().isoformat(),
            "player_stats": {},
            "toss": {},
            "current_innings": None,
            "first_innings_runs": None,
            "second_innings_started": False,
            "innings_complete": {
                "innings_a": False,
                "innings_b": False
            }
        }
        self.current_batsmen = {
            "innings_a": {"striker": None, "non_striker": None},
            "innings_b": {"striker": None, "non_striker": None}
        }
        self.current_bowler = {
            "innings_a": None,
            "innings_b": None
        }

    def add_player(self, team_key, player_name):
        player_id = str(uuid.uuid4())
        self.match["squads"][team_key][player_id] = player_name
        self.match["player_stats"][player_id] = {
            "name": player_name,
            "batting": {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "status": "not out"},
            "bowling": {"overs": 0, "balls": 0, "runs_conceded": 0, "wickets": 0}
        }
        return player_id

    def record_toss(self, winner, decision):
        self.match["toss"] = {"winner": winner, "decision": decision}

    def create_innings(self, innings_key, batting_team, bowling_team):
        self.match["innings"][innings_key] = {
            "batting_team": batting_team,
            "bowling_team": bowling_team,
            "overs": {},
            "total_runs": 0,
            "wickets": 0,
            "extras": {"wides": 0, "no_balls": 0, "byes": 0, "leg_byes": 0},
            "fall_of_wickets": []
        }
        self.match["current_innings"] = innings_key
        if innings_key == "innings_b":
            self.match["second_innings_started"] = True

    def start_new_over(self, innings_key, over_number, bowler_id):
        self.match["innings"][innings_key]["overs"][str(over_number)] = []
        self.current_bowler[innings_key] = bowler_id
        striker = self.current_batsmen[innings_key]["striker"]
        non_striker = self.current_batsmen[innings_key]["non_striker"]
        if striker and non_striker:
            self.current_batsmen[innings_key] = {
                "striker": non_striker,
                "non_striker": striker
            }

    def set_strikers(self, innings_key, striker_id, non_striker_id):
        self.current_batsmen[innings_key] = {
            "striker": striker_id,
            "non_striker": non_striker_id
        }

    def add_score(self, innings_key, runs, extra=None, wicket=None, dismissal_type=None):
        innings = self.match["innings"][innings_key]
        overs = innings["overs"]
        current_over = str(max(map(int, overs)))
        balls = overs[current_over]

        legal_deliveries = [b for b in balls if not b.get("extra") in ["wides", "no_balls"]]
        if len(legal_deliveries) >= 6:
            raise ValueError("Over is complete. Start new over before adding more balls.")

        striker_id = self.current_batsmen[innings_key]["striker"]
        bowler_id = self.current_bowler[innings_key]

        ball_data = {
            "ball": len(balls) + 1,
            "batsman_id": striker_id,
            "bowler_id": bowler_id,
            "runs": runs,
            "extra": extra,
            "wicket": wicket,
            "dismissal": dismissal_type
        }
        balls.append(ball_data)
        innings["total_runs"] += runs

        if extra:
            innings["extras"][extra] += 1
        else:
            self.match["player_stats"][striker_id]["batting"]["runs"] += runs
            self.match["player_stats"][striker_id]["batting"]["balls"] += 1
            if runs == 4:
                self.match["player_stats"][striker_id]["batting"]["fours"] += 1
            if runs == 6:
                self.match["player_stats"][striker_id]["batting"]["sixes"] += 1

            self.match["player_stats"][bowler_id]["bowling"]["runs_conceded"] += runs
            self.match["player_stats"][bowler_id]["bowling"]["balls"] += 1

        if wicket:
            innings["wickets"] += 1
            self.match["player_stats"][striker_id]["batting"]["status"] = dismissal_type or "out"
            self.match["player_stats"][bowler_id]["bowling"]["wickets"] += 1
            innings["fall_of_wickets"].append({"batsman_id": striker_id, "runs": innings["total_runs"]})

        self.match["history"].append(ball_data)
        self.match["last_updated"] = datetime.utcnow().isoformat()

        if not extra and runs % 2 == 1:
            self.swap_strikers(innings_key)

        if innings_key == "innings_a" and innings["wickets"] >= 10:
            self.match["innings_complete"]["innings_a"] = True
        elif innings_key == "innings_b" and innings["wickets"] >= 10:
            self.match["innings_complete"]["innings_b"] = True

        if innings_key == "innings_a":
            self.match["first_innings_runs"] = innings["total_runs"]

    def swap_strikers(self, innings_key):
        self.current_batsmen[innings_key]["striker"], self.current_batsmen[innings_key]["non_striker"] = \
            self.current_batsmen[innings_key]["non_striker"], self.current_batsmen[innings_key]["striker"]

    def get_live_stats(self, innings_key):
        innings = self.match["innings"][innings_key]
        total_runs = innings["total_runs"]
        wickets = innings["wickets"]
        overs = innings["overs"]
        total_legal_balls = sum(len([b for b in over if not b.get("extra") in ["wides", "no_balls"]]) for over in overs.values())
        overs_float = total_legal_balls // 6 + (total_legal_balls % 6) / 10
        run_rate = round((total_runs / total_legal_balls) * 6, 2) if total_legal_balls else 0

        batting_team = innings["batting_team"]
        bowling_team = innings["bowling_team"]

        striker_id = self.current_batsmen[innings_key]["striker"]
        non_striker_id = self.current_batsmen[innings_key]["non_striker"]
        batsmen_stats = []
        for pid, is_strike in [(striker_id, True), (non_striker_id, False)]:
            if pid:
                player = self.match["player_stats"][pid]
                batsmen_stats.append({
                    "name": player["name"],
                    "runs": player["batting"]["runs"],
                    "balls": player["batting"]["balls"],
                    "fours": player["batting"]["fours"],
                    "sixes": player["batting"]["sixes"],
                    "strike": is_strike
                })

        bowler_id = self.current_bowler[innings_key]
        bowler_stats = None
        if bowler_id:
            bowler = self.match["player_stats"][bowler_id]
            balls_bowled = bowler["bowling"]["balls"]
            bowler_overs = balls_bowled // 6 + (balls_bowled % 6) / 10
            bowler_stats = {
                "name": bowler["name"],
                "overs": round(bowler_overs, 1),
                "runs": bowler["bowling"]["runs_conceded"],
                "wickets": bowler["bowling"]["wickets"]
            }

        stats = {
            "team_score": f"{batting_team} {total_runs}/{wickets} ({overs_float:.1f})",
            "batting_team": batting_team,
            "bowling_team": bowling_team,
            "current_batsmen": batsmen_stats,
            "current_bowler": bowler_stats,
            "run_rate": run_rate,
            "overs_float": overs_float,
            "total_legal_balls": total_legal_balls
        }

        if innings_key == "innings_a":
            estimated_score = int(run_rate * self.match["overs_limit"])
            stats["estimated_score"] = estimated_score
        elif innings_key == "innings_b" and self.match["first_innings_runs"] is not None:
            runs_required = self.match["first_innings_runs"] + 1 - total_runs
            balls_remaining = (self.match["overs_limit"] * 6) - total_legal_balls
            required_run_rate = round((runs_required / balls_remaining) * 6, 2) if balls_remaining > 0 else 0
            stats["required_run_rate"] = required_run_rate
            stats["runs_to_win"] = runs_required
            stats["balls_remaining"] = balls_remaining
            stats["dls_par_score"] = self.match["first_innings_runs"] * 0.95

        return stats

    def to_json(self):
        return json.dumps(self.match, indent=2)




# manager = CricketMatchManager(
#     match_id="INDvAUS_2025_07_03",
#     team_a="India",
#     team_b="Australia",
#     venue="Wankhede Stadium",
#     city="Mumbai",
#     ground_type="turf",
#     match_type="limited overs",
#     overs_limit=50,
#     ball_type="white ball"
# )

# # Add players with auto IDs
# a1 = manager.add_player("team_a", "Rohit Sharma")
# a2 = manager.add_player("team_a", "Virat Kohli")

# b1 = manager.add_player("team_b", "David Warner")
# b2 = manager.add_player("team_b", "Pat Cummins")

# # Toss and innings setup
# manager.record_toss("India", "bat")
# manager.create_innings("innings_1", "India", "Australia")
# manager.start_new_over("innings_1", 1)

# # Add a scoring event
# manager.add_score("innings_1", 1, {
#     "ball": 1,
#     "batsman_id": a1,
#     "bowler_id": b2,
#     "runs": 4,
#     "extra": None,
#     "wicket": None
# })

# print(manager.to_json())

import random
import time

def simulate_live_match(manager):
    for innings_key, (batting_team, bowling_team) in zip(
        ["innings_a", "innings_b"],
        [(manager.match["teams"]["team_a"], manager.match["teams"]["team_b"]),
         (manager.match["teams"]["team_b"], manager.match["teams"]["team_a"])]
    ):
        print(f"\nStarting {innings_key.upper()} - {batting_team} batting\n")
        manager.create_innings(innings_key, batting_team, bowling_team)
        players = list(manager.match["squads"][batting_team].keys())
        bowlers = list(manager.match["squads"][bowling_team].keys())

        batsman_index = 2
        manager.set_strikers(innings_key, players[0], players[1])

        for over in range(manager.match["overs_limit"]):
            bowler_id = random.choice(bowlers)
            manager.start_new_over(innings_key, over, bowler_id)
            print(f"\n--- Over {over + 1} --- Bowler: {manager.match['player_stats'][bowler_id]['name']}")
            legal_deliveries = 0

            while legal_deliveries < 6:
                time.sleep(1)  # Simulate time delay between deliveries

                outcome = random.choices(
                    population=["dot", "1", "2", "3", "4", "6", "wicket", "wide", "no_ball"],
                    weights=[10, 20, 10, 5, 15, 10, 10, 5, 5],
                    k=1
                )[0]

                if outcome == "wicket":
                    manager.add_score(innings_key, 0, wicket=True, dismissal_type="bowled")
                    print("WICKET! Bowled")
                    if manager.match["innings"][innings_key]["wickets"] >= 10 or batsman_index >= len(players):
                        break
                    new_batsman = players[batsman_index]
                    manager.set_strikers(innings_key, new_batsman, manager.current_batsmen[innings_key]["non_striker"])
                    batsman_index += 1
                    legal_deliveries += 1

                elif outcome in ["wide", "no_ball"]:
                    manager.add_score(innings_key, 1, extra=outcome)
                    print(f"{outcome.upper()}! +1 extra")

                else:
                    runs = int(outcome)
                    manager.add_score(innings_key, runs)
                    print(f"Runs: {runs}")
                    legal_deliveries += 1

                stats = manager.get_live_stats(innings_key)
                print(stats["team_score"])

            if manager.match["innings"][innings_key]["wickets"] >= 10:
                break

        print(f"\nInnings {innings_key.upper()} Complete - Final Score: {stats['team_score']}")

manager = CricketMatchManager("match123", "Team Alpha", "Team Beta", "Stadium X", "City Y", "Turf", "T20")

# Add players to both teams (you must add at least 11 to each)
for i in range(1, 12):
    manager.add_player("team_a", f"PlayerA{i}")
    manager.add_player("team_b", f"PlayerB{i}")

manager.record_toss("Team Alpha", "bat")
simulate_live_match(manager)

# Optional: print final match JSON
# print(manager.to_json())
