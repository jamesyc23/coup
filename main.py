from game import Game
from agent import Agent, IncomeAgent

def main():
    game = Game(
        named_agents={
            "player1": IncomeAgent(),
            "player2": IncomeAgent(),
        },
        cards_per_player=1,
    )
    winner = game.play(verbose=True)
    print(winner.agent)

if __name__ == "__main__":
    main()