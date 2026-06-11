import random
import sys

# Make sure the trophy emoji prints on the Windows console too.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Expanded ratings (top teams)
team_ratings = {
    "Spain": 94, "Argentina": 93, "France": 92, "England": 90,
    "Brazil": 91, "Portugal": 89, "Germany": 88, "Netherlands": 88,
    "Mexico": 75, "USA": 78, "Morocco": 80, "Croatia": 86
}

teams = list(team_ratings.keys())

# Win probability
def win_prob(a, b):
    rA = team_ratings[a]
    rB = team_ratings[b]
    return 1 / (1 + 10 ** ((rB - rA) / 10))

# Simulate one match
def play_match(a, b):
    if random.random() < win_prob(a, b):
        return a
    return b

# Simulate knockout bracket
def simulate_bracket(teams):
    round_teams = teams[:]
    random.shuffle(round_teams)
    rounds = []

    while len(round_teams) > 1:
        next_round = []
        results = []

        # If the round has an odd number of teams, the last one gets a bye.
        if len(round_teams) % 2 == 1:
            bye = round_teams.pop()
            results.append((bye, "(bye)", bye))
            next_round.append(bye)

        for i in range(0, len(round_teams), 2):
            t1 = round_teams[i]
            t2 = round_teams[i+1]
            winner = play_match(t1, t2)
            results.append((t1, t2, winner))
            next_round.append(winner)

        rounds.append(results)
        round_teams = next_round

    return rounds, round_teams[0]

# Run many simulations
def run_simulations(n=500):
    winners = {}

    for _ in range(n):
        _, champ = simulate_bracket(teams)
        winners[champ] = winners.get(champ, 0) + 1

    return winners

# Print bracket
def print_bracket(rounds):
    for i, rnd in enumerate(rounds):
        print(f"\n=== Round {i+1} ===")
        for t1, t2, w in rnd:
            print(f"{t1} vs {t2} -> {w}")

# MAIN
if __name__ == "__main__":
    print("\n=== SINGLE TOURNAMENT BRACKET ===")
    rounds, champ = simulate_bracket(teams)
    print_bracket(rounds)
    print(f"\n🏆 Champion: {champ}")

    print("\n=== SIMULATION RESULTS (500 runs) ===")
    results = run_simulations(500)

    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    for team, wins in sorted_results:
        print(f"{team}: {round(wins/5, 1)}% win rate")

    input("\nDone. Press Enter to exit...")
