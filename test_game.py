import pytest
from game import Game
from game_elements import Card, Move, Action, Player, ActionInfo
from agent import Agent

class MockAgent(Agent):
    def __init__(self, actions=None, challenge_blocks=False):
        self.actions = actions or []
        self.action_index = 0
        self.challenge_blocks = challenge_blocks

    def get_action_info(self):
        action = self.actions[self.action_index]
        self.action_index = (self.action_index + 1) % len(self.actions)
        return action

    def get_challenge_decision(self, action_info):
        return False

    def get_block_decision(self, action_info):
        return True  # Always try to block

    def get_block_challenge_decision(self, action_info):
        return self.challenge_blocks
    
    def choose_cards(self, cards_to_choose_from):
        return cards_to_choose_from[2:] # Always return the first two cards

@pytest.fixture
def game():
    return Game(
        named_agents={"player1": MockAgent(), "player2": MockAgent()},
        cards_per_player=1
    )

def test_income(game):
    player = game._current_player()
    initial_coins = player.coins
    game._step_nonexchange_action(Action(acting_player=player, move=Move.INCOME), blocked=False)
    assert player.coins == initial_coins + 1

def test_foreign_aid(game):
    player = game._current_player()
    initial_coins = player.coins
    game._step_nonexchange_action(Action(acting_player=player, move=Move.FOREIGN_AID), blocked=False)
    assert player.coins == initial_coins + 2

def test_coup(game):
    player = game._current_player()
    player.coins = 7
    target_player = game.get_player("player2")
    initial_target_cards = len(target_player.cards)
    game._step_nonexchange_action(Action(acting_player=player, move=Move.COUP, target_player=target_player), blocked=False)
    assert player.coins == 0
    assert len(target_player.cards) == initial_target_cards - 1

def test_tax(game):
    player = game._current_player()
    initial_coins = player.coins
    game._step_nonexchange_action(Action(acting_player=player, move=Move.TAX), blocked=False)
    assert player.coins == initial_coins + 3

def test_assassinate(game):
    player = game._current_player()
    player.coins = 3
    target_player = game.get_player("player2")
    initial_target_cards = len(target_player.cards)
    game._step_nonexchange_action(Action(acting_player=player, move=Move.ASSASSINATE, target_player=target_player), blocked=False)
    assert player.coins == 0
    assert len(target_player.cards) == initial_target_cards - 1

def test_steal(game):
    player = game._current_player()
    target_player = game.get_player("player2")
    target_player.coins = 2
    initial_player_coins = player.coins
    game._step_nonexchange_action(Action(acting_player=player, move=Move.STEAL, target_player=target_player), blocked=False)
    assert player.coins == initial_player_coins + 2
    assert target_player.coins == 0

def test_exchange_one_card(game):
    player = game._current_player()
    player.cards = [Card.ASSASSIN]
    initial_cards = player.cards
    top_two_cards = game.deck[:2]
    cards_to_choose_from = game._exchange_cards_to_choose_from(player)
    chosen_cards = player.choose_cards(cards_to_choose_from)
    game._complete_exchange(player, cards_to_choose_from, chosen_cards)
    assert len(player.cards) == 1
    assert player.cards[0] == top_two_cards[1]

def test_exchange_two_cards(game):
    player = game._current_player()
    player.cards = [Card.ASSASSIN, Card.AMBASSADOR]
    initial_cards = player.cards
    top_two_cards = game.deck[:2]
    cards_to_choose_from = game._exchange_cards_to_choose_from(player)
    chosen_cards = player.choose_cards(cards_to_choose_from)
    game._complete_exchange(player, cards_to_choose_from, chosen_cards)
    assert len(player.cards) == 2
    assert player.cards == top_two_cards

def test_challenge_success(game):
    player = game._current_player()
    player.cards = [Card.ASSASSIN]
    challenging_player = game.get_player("player2")
    action = Action(acting_player=player, move=Move.TAX)
    success, card_lost = game.step_challenge(action, challenging_player)
    assert success
    assert card_lost == Card.ASSASSIN
    assert len(player.cards) == 0

def test_challenge_failure(game):
    player = game._current_player()
    player.cards = [Card.DUKE]
    challenging_player = game.get_player("player2")
    challenging_player.cards = [Card.ASSASSIN]
    action = Action(acting_player=player, move=Move.TAX)
    success, card_lost = game.step_challenge(action, challenging_player)
    assert not success
    assert card_lost == Card.ASSASSIN
    assert len(challenging_player.cards) == 0

def test_block_foreign_aid(game):
    player = game._current_player()
    initial_coins = player.coins
    blocking_player = game.get_player("player2")
    blocking_player.cards = [Card.DUKE]
    action = Action(acting_player=player, move=Move.FOREIGN_AID)
    game._step_nonexchange_action(action, blocked=True)
    assert player.coins == initial_coins  # Coins should not increase

def test_block_steal(game):
    player = game._current_player()
    target_player = game.get_player("player2")
    target_player.cards = [Card.AMBASSADOR]
    target_player.coins = 2
    initial_player_coins = player.coins
    initial_target_coins = target_player.coins
    action = Action(acting_player=player, move=Move.STEAL, target_player=target_player)
    game._step_nonexchange_action(action, blocked=True)
    assert player.coins == initial_player_coins
    assert target_player.coins == initial_target_coins

def test_block_assassinate(game):
    player = game._current_player()
    player.coins = 3
    target_player = game.get_player("player2")
    target_player.cards = [Card.CONTESSA]
    initial_target_cards = len(target_player.cards)
    action = Action(acting_player=player, move=Move.ASSASSINATE, target_player=target_player)
    game._step_nonexchange_action(action, blocked=True)
    assert player.coins == 0  # Coins should still be deducted
    assert len(target_player.cards) == initial_target_cards  # Target should not lose a card

def test_successful_block_challenge_foreign_aid():
    acting_agent = MockAgent([ActionInfo(move=Move.FOREIGN_AID)], challenge_blocks=True)
    blocking_agent = MockAgent(challenge_blocks=False)
    game = Game(
        named_agents={"player1": acting_agent, "player2": blocking_agent},
        cards_per_player=1
    )
    game.get_player("player2").cards = [Card.CONTESSA]  # Incorrect card for blocking Foreign Aid

    initial_acting_coins = game.get_player("player1").coins
    initial_blocking_cards = len(game.get_player("player2").cards)

    game.play_turn()

    assert game.get_player("player1").coins == initial_acting_coins + 2
    assert len(game.get_player("player2").cards) == initial_blocking_cards - 1

def test_failed_block_challenge_foreign_aid():
    acting_agent = MockAgent([ActionInfo(move=Move.FOREIGN_AID)], challenge_blocks=True)
    blocking_agent = MockAgent(challenge_blocks=False)
    game = Game(
        named_agents={"player1": acting_agent, "player2": blocking_agent},
        cards_per_player=1
    )
    game.get_player("player2").cards = [Card.DUKE]  # Correct card for blocking Foreign Aid

    initial_acting_coins = game.get_player("player1").coins
    initial_acting_cards = len(game.get_player("player1").cards)
    initial_blocking_cards = len(game.get_player("player2").cards)

    game.play_turn()

    assert game.get_player("player1").coins == initial_acting_coins
    assert len(game.get_player("player1").cards) == initial_acting_cards - 1
    assert len(game.get_player("player2").cards) == initial_blocking_cards

def test_successful_block_challenge_assassinate():
    acting_agent = MockAgent([ActionInfo(move=Move.ASSASSINATE, target_player_index=1)], challenge_blocks=True)
    blocking_agent = MockAgent(challenge_blocks=False)
    game = Game(
        named_agents={"player1": acting_agent, "player2": blocking_agent},
        cards_per_player=1
    )
    game.get_player("player1").coins = 3  # Ensure enough coins for assassination
    game.get_player("player2").cards = [Card.DUKE]  # Incorrect card for blocking Assassinate

    initial_acting_coins = game.get_player("player1").coins
    initial_blocking_cards = len(game.get_player("player2").cards)

    game.play_turn()

    assert game.get_player("player1").coins == initial_acting_coins - 3
    assert len(game.get_player("player2").cards) == initial_blocking_cards - 1

def test_failed_block_challenge_assassinate():
    acting_agent = MockAgent([ActionInfo(move=Move.ASSASSINATE, target_player_index=1)], challenge_blocks=True)
    blocking_agent = MockAgent(challenge_blocks=False)
    game = Game(
        named_agents={"player1": acting_agent, "player2": blocking_agent},
        cards_per_player=1
    )
    game.get_player("player1").coins = 3  # Ensure enough coins for assassination
    game.get_player("player2").cards = [Card.CONTESSA]  # Correct card for blocking Assassinate

    initial_acting_coins = game.get_player("player1").coins
    initial_acting_cards = len(game.get_player("player1").cards)
    initial_blocking_cards = len(game.get_player("player2").cards)

    game.play_turn()

    assert game.get_player("player1").coins == initial_acting_coins - 3  # Coins still deducted
    assert len(game.get_player("player1").cards) == initial_acting_cards - 1
    assert len(game.get_player("player2").cards) == initial_blocking_cards

def test_successful_block_challenge_steal():
    acting_agent = MockAgent([ActionInfo(move=Move.STEAL, target_player_index=1)], challenge_blocks=True)
    blocking_agent = MockAgent(challenge_blocks=False)
    game = Game(
        named_agents={"player1": acting_agent, "player2": blocking_agent},
        cards_per_player=1
    )
    game.get_player("player2").cards = [Card.DUKE]  # Incorrect card for blocking Steal
    game.get_player("player2").coins = 2  # Ensure coins available to steal

    initial_acting_coins = game.get_player("player1").coins
    initial_blocking_coins = game.get_player("player2").coins
    initial_blocking_cards = len(game.get_player("player2").cards)

    game.play_turn()

    assert game.get_player("player1").coins == initial_acting_coins + 2
    assert game.get_player("player2").coins == initial_blocking_coins - 2
    assert len(game.get_player("player2").cards) == initial_blocking_cards - 1

def test_failed_block_challenge_steal():
    acting_agent = MockAgent([ActionInfo(move=Move.STEAL, target_player_index=1)], challenge_blocks=True)
    blocking_agent = MockAgent(challenge_blocks=False)
    game = Game(
        named_agents={"player1": acting_agent, "player2": blocking_agent},
        cards_per_player=1
    )
    game.get_player("player2").cards = [Card.AMBASSADOR]  # Correct card for blocking Steal
    game.get_player("player2").coins = 2  # Ensure coins available to steal

    initial_acting_coins = game.get_player("player1").coins
    initial_blocking_coins = game.get_player("player2").coins
    initial_acting_cards = len(game.get_player("player1").cards)
    initial_blocking_cards = len(game.get_player("player2").cards)

    game.play_turn()

    assert game.get_player("player1").coins == initial_acting_coins
    assert game.get_player("player2").coins == initial_blocking_coins
    assert len(game.get_player("player1").cards) == initial_acting_cards - 1
    assert len(game.get_player("player2").cards) == initial_blocking_cards