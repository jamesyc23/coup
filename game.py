from typing import List, Optional, Tuple
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

    action_challenged: bool
    challenging_player_index: Optional[int]
    challenge_success: Optional[bool]
    card_lost_in_challenge: Optional[Card]

    action_blocked: bool
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

    my_coins: int
    my_cards: List[Card]
    other_player_coins: List[int]
    other_player_card_counts: List[int]

class Game:
    def __init__(
        self,
        agents: List[Agent],
        unshuffled_deck: List[Card] = list(Card) * 3,
        cards_per_player: int = 2,
        starting_coins: int = 2,
    ):
        num_players = len(agents)
        assert num_players * cards_per_player <= len(unshuffled_deck)
        self.deck = sample(unshuffled_deck, k=len(unshuffled_deck))
        self.players = [
            Player(
                agent=agent,
                cards=[self._deal_card() for _ in range(cards_per_player)],
                starting_coins=starting_coins,
            )
            for agent in agents
        ]
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
            yield self.players[(self.acting_player_index + i) % num_players]

    def action_from_info(self, action_info: ActionInfo, game: "Game") -> Action:
        acting_player = game._current_player()
        move = action_info.move
        target_player = game.players[action_info.target_player_index] if action_info.target_player_index is not None else None

        return Action(acting_player=acting_player, move=move, target_player=target_player)
    
    def _step_action(self, action: Action):
        acting_player = action.acting_player
        move = action.move
        target_player = action.target_player

        if move == Move.INCOME:
            acting_player.coins += 1
        elif move == Move.FOREIGN_AID:
            acting_player.coins += 2
        elif move == Move.COUP:
            if acting_player.coins < 7 or target_player is None:
                raise ValueError("Invalid coup")
            acting_player.coins -= 7
            self._lose_influence(target_player)
        elif move == Move.TAX:
            acting_player.coins += 3
        elif move == Move.ASSASSINATE:
            if acting_player.coins < 3 or target_player is None:
                raise ValueError("Invalid assassination")
            acting_player.coins -= 3
        elif move == Move.STEAL:
            if target_player is None:
                raise ValueError("Invalid steal")
            acting_player.coins += min(target_player.coins, 2)
            target_player.coins -= min(target_player.coins, 2)
        elif move == Move.EXCHANGE:
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
        action = self.action_from_info(action_info=action_info, game=self)
        will_take_action = True

        action_challenged = False
        for other_player in self._iterate_other_players():
            challenge_decision = other_player.get_challenge_decision(action_info)
            if challenge_decision:
                action_challenged = True
                challenging_player_index = self.players.index(other_player)
                challenge_success, card_lost_in_challenge = self.step_challenge(action, challenging_player=other_player)
                if challenge_success:
                    will_take_action = False
                break
        
        action_blocked = False
        for other_player in self._iterate_other_players():
            block_decision = other_player.get_block_decision(action_info)
            if block_decision:
                action_blocked = True
                blocking_player_index = self.players.index(other_player)
                block_challenged = current_player.get_block_challenge_decision(action_info)
                if block_challenged:
                    block_challenge_success, card_lost_in_block_challenge = self.step_block_challenge(action, blocking_player=other_player)
                    block_success = not block_challenge_success
                else:
                    block_success = True
                if block_success:
                    will_take_action = False

        if will_take_action:
            self._step_action(action)

        for player_index, player in enumerate(self.players):
            turn_view = TurnView(
                observer_index=player_index,
                acting_player_index=self.acting_player_index,
                action=action,
                action_challenged=action_challenged,
                challenging_player_index=challenging_player_index if action_challenged else None,
                challenge_success=challenge_success if action_challenged else None,
                card_lost_in_challenge=card_lost_in_challenge if action_challenged else None,
                action_blocked=action_blocked,
                blocking_player_index=blocking_player_index if action_blocked else None,
                block_challenged=block_challenged if action_blocked else None,
                block_challenge_success=block_challenge_success if action_blocked else None,
                card_lost_in_block_challenge=card_lost_in_block_challenge if action_blocked else None,
            ) # TODO: shift indices
            player.observe(turn_view=turn_view, game_view=self.to_game_view(observer_index=0))

        self.acting_player_index = (self.acting_player_index + 1) % self._num_players()

    def _lose_influence(self, player: Player):
        # TODO: give the player choice
        assert len(player.cards) > 0
        return player.cards.pop(0)

    def to_game_view(self, observer_index: int) -> GameView:
        my_player = self.players[observer_index]
        other_players = [self.players[observer_index + i] for i in range(1, self._num_players()) if i != observer_index]

        return GameView(
            observer_index=observer_index,
            my_coins=my_player.coins,
            my_cards=my_player.cards,
            other_player_coins=[player.coins for player in other_players],
            other_player_card_counts=[len(player.cards) for player in other_players]
        )

    def __repr__(self):
        return f"""
            Current player: {self._current_player()}
            Players: {self.players}

            Deck: {self.deck}
        """