from game import Game
from agent import Agent

def main():
    game = Game(
        agents=[Agent(), Agent()],
        starting_coins=2
    )
    print(game)

if __name__ == "__main__":
    main()