from typing import Dict, List, Optional, Tuple
from random import sample
from dataclasses import dataclass

from game_elements import Card, Move, Action, ActionInfo, Player
from agent import Agent

@dataclass
class TurnView:
    """
    Information about a turn in the game. All indices except observer_index are with respect to a specific player (the observer):
    the observer has index 0, the player after the observer has index 1, and so on. The observer_index is the global index of the observer.
    """
    observer_index: int # Included for debugging purposes

    acting_player_index: int
    action: Action

    challenged: bool
    challenging_player_index: Optional[int]
    challenge_success: Optional[bool]
    card_lost_in_challenge: Optional[Card]

    blocked: bool
    block_attempted: bool
    blocking_player_index: Optional[int]
    block_challenged: Optional[bool]
    block_challenge_success: Optional[bool]
    card_lost_in_block_challenge: Optional[Card]

@dataclass
class GameView:
    """
    Information about the game state after a turn. Information about other players is listed from the observer's perspective.
    """
    observer_index: int # Included for debugging purposes

    observer_coins: int
    observer_cards: List[Card]
    other_player_coins: List[int]
    other_player_card_counts: List[int]

class Game:
    def __init__(
        self,
        named_agents: Dict[str, Agent],
        unshuffled_deck: List[Card] = list(Card) * 3,
        cards_per_player: int = 2,
        starting_coins: int = 2,
    ):
        num_players = len(named_agents)
        assert num_players * cards_per_player <= len(unshuffled_deck)
        self.deck = sample(unshuffled_deck, k=len(unshuffled_deck))
        self.players = [
            Player(
                agent=agent,
                name=name,
                cards=[self._deal_card() for _ in range(cards_per_player)],
                starting_coins=starting_coins,
            )
            for name, agent in named_agents.items()
        ]
        self.players_by_name = {player.name: player for player in self.players}
        [player.agent.load_initial_game_view(game_view=self.to_game_view(observer_index=i)) for i, player in enumerate(self.players)]
        self.acting_player_index = 0
        self.face_up_cards = []

    def _deal_card(self):
        return self.deck.pop(0)

    def _current_player(self):
        return self.players[self.acting_player_index]
    
    def _num_players(self):
        return len(self.players)
    
    def _iterate_other_players(self):
        num_players = self._num_players()
        for i in range(1, num_players):
            player = self.players[(self.acting_player_index + i) % num_players]
            if player.alive():
                yield player

    def get_player(self, name: str) -> Player:
        return self.players_by_name[name]

    def is_game_over(self):
        return sum(player.alive() for player in self.players) <= 1
    
    def winner(self):
        if not self.is_game_over():
            raise ValueError("Game is not over")
        return next(player for player in self.players if player.alive())

    def action_from_info(self, action_info: ActionInfo) -> Action:
        acting_player = self._current_player()
        move = action_info.move
        target_player = (
            self.players[(self.acting_player_index + action_info.target_player_index) % self._num_players()]
            if action_info.target_player_index is not None
            else None
        )

        return Action(acting_player=acting_player, move=move, target_player=target_player)
    
    def _step_action(self, action: Action, blocked: bool):
        acting_player = action.acting_player
        move = action.move
        target_player = action.target_player

        if move == Move.INCOME:
            assert not blocked, "Cannot block income"
            acting_player.coins += 1
        elif move == Move.FOREIGN_AID:
            if not blocked:
                acting_player.coins += 2
        elif move == Move.COUP:
            assert not blocked, "Cannot block coup"
            if acting_player.coins < 7 or target_player is None:
                raise ValueError("Invalid coup")
            acting_player.coins -= 7
            self._lose_influence(target_player)
        elif move == Move.TAX:
            assert not blocked, "Cannot block tax"
            acting_player.coins += 3
        elif move == Move.ASSASSINATE:
            assert acting_player.coins >= 3 and target_player is not None, "Invalid assassination"
            acting_player.coins -= 3
            if not blocked and target_player.alive():
                self._lose_influence(target_player)
        elif move == Move.STEAL:
            assert target_player is not None, "Invalid steal"
            if not blocked:
                acting_player.coins += min(target_player.coins, 2)
                target_player.coins -= min(target_player.coins, 2)
        elif move == Move.EXCHANGE:
            assert not blocked, "Cannot block exchange"
            # TODO: implement
            pass
        else:
            raise ValueError("Invalid action")

    def step_challenge(self, action: Action, challenging_player: Player) -> Tuple[bool, Card]:
        challenge_success = not any(action.move.enabled_by(card) for card in action.acting_player.cards)
        if challenge_success:
            card_lost = self._lose_influence(action.acting_player)
        else:
            card_lost = self._lose_influence(challenging_player)
            # TODO: give the acting player a new card

        return challenge_success, card_lost

    def step_block_challenge(self, action: Action, blocking_player: Player) -> Tuple[bool, Card]:
        challenge_success = not any(action.move.blockable_by(card) for card in blocking_player.cards)
        if challenge_success:
            card_lost = self._lose_influence(blocking_player)
        else:
            card_lost = self._lose_influence(action.acting_player)
            # TODO: give the blocking player a new card

        return challenge_success, card_lost

    def play_turn(self):
        current_player = self._current_player()
        action_info = current_player.get_action_info()
        action = self.action_from_info(action_info=action_info)

        if action.target_player is not None:
            assert action.target_player.alive(), "Invalid target player"
        
        will_take_action = True
        for other_player in self._iterate_other_players():
            challenged = other_player.get_challenge_decision(action_info)
            if challenged:
                challenging_player_index = self.players.index(other_player)
                challenge_success, card_lost_in_challenge = self.step_challenge(action, challenging_player=other_player)
                if challenge_success:
                    will_take_action = False
                break
        
        blocked = False
        for other_player in self._iterate_other_players():
            block_attempted = other_player.get_block_decision(action_info)
            if block_attempted:
                blocking_player_index = self.players.index(other_player)
                block_challenged = current_player.get_block_challenge_decision(action_info)
                if block_challenged:
                    block_challenge_success, card_lost_in_block_challenge = self.step_block_challenge(action, blocking_player=other_player)
                    blocked = not block_challenge_success
                else:
                    blocked = True

        if will_take_action:
            self._step_action(action, blocked=blocked)

        for player_index, player in enumerate(self.players):
            turn_view = TurnView(
                observer_index=player_index,
                acting_player_index=self.acting_player_index,
                action=action,
                challenged=challenged,
                challenging_player_index=challenging_player_index if challenged else None,
                challenge_success=challenge_success if challenged else None,
                card_lost_in_challenge=card_lost_in_challenge if challenged else None,
                blocked=blocked,
                block_attempted=block_attempted,
                blocking_player_index=blocking_player_index if block_attempted else None,
                block_challenged=block_challenged if block_attempted else None,
                block_challenge_success=block_challenge_success if block_attempted else None,
                card_lost_in_block_challenge=card_lost_in_block_challenge if block_attempted else None,
            ) # TODO: shift indices
            player.observe(turn_view=turn_view, game_view=self.to_game_view(observer_index=player_index))

        self.acting_player_index = (self.acting_player_index + 1) % self._num_players()

    def play(self, verbose=False):
        while not self.is_game_over():
            self.play_turn()
            if verbose:
                print(self)
        
        return self.winner()

    def _lose_influence(self, player: Player):
        # TODO: give the player choice
        return player.cards.pop(0)

    def to_game_view(self, observer_index: int) -> GameView:
        my_player = self.players[observer_index]
        other_players = [self.players[observer_index + i] for i in range(1, self._num_players()) if i != observer_index]

        return GameView(
            observer_index=observer_index,
            observer_coins=my_player.coins,
            observer_cards=my_player.cards,
            other_player_coins=[player.coins for player in other_players],
            other_player_card_counts=[len(player.cards) for player in other_players]
        )

    def __repr__(self):
        return f"""
            Current player: {self._current_player()}
            Players: {self.players}

            Deck: {self.deck}
        """