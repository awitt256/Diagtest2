import time
import random
import os
# Base team strength ratings (simulated ELO-style)
team_ratings = {
    "Mexico": 75,
    "South Africa": 55,
    "USA": 78,
    "Paraguay": 72,
    "Brazil": 92,
    "Morocco": 80,
    "Switzerland": 85,
    "Qatar": 60,
    "France": 94,
    "Senegal": 82,
    "England": 90,
    "Croatia": 86
}
# List of games
games = [
    {"teams": ("Mexico", "South Africa"), "date": "June 11"},
    {"teams": ("USA", "Paraguay"), "date": "June 12"},
    {"teams": ("Brazil", "Morocco"), "date": "June 13"},
    {"teams": ("Switzerland", "Qatar"), "date": "June 13"},
    {"teams": ("France", "Senegal"), "date": "June 16"},
    {"teams": ("England", "Croatia"), "date": "June 17"}
]
# Convert ratings → win probability
def calculate_win_probability(rA, rB):
    probA = 1 / (1 + 10 ** ((rB - rA) / 10))
    return round(probA * 100)
# Generate updated predictions
def update_predictions():
    updated_games = []
    for game in games:
        teamA, teamB = game["teams"]
        # Simulate small rating changes
        ratingA = team_ratings[teamA] + random.uniform(-2, 2)
        ratingB = team_ratings[teamB] + random.uniform(-2, 2)
        probA = calculate_win_probability(ratingA, ratingB)
        updated_games.append({
            "teams": (teamA, teamB),
            "date": game["date"],
            "odds": {
                "teamA": probA,
                "teamB": 100 - probA
            }
        })
    return updated_games
# Display games (with optional search)
def display_games(game_list, search=""):
    os.system("cls" if os.name == "nt" else "clear")
    print("=== World Cup 2026 Live Odds ===
")
    for game in game_list:
        teamA, teamB = game["teams"]
        if search.lower() not in teamA.lower() and search.lower() not in teamB.lower():
            continue
        print(f"{teamA} vs {teamB} ({game['date']})")
        print(f"  {teamA}: {game['odds']['teamA']}%")
        print(f"  {teamB}: {game['odds']['teamB']}%")
        print("-" * 40)


# Main loop
if __name__ == "__main__":
    search_team = input("Search for a team (or press Enter for all): ")


    try:
        while True:
            updated = update_predictions()
            display_games(updated, search_team)
            time.sleep(3)
    except KeyboardInterrupt:
        print("
Exiting...")