from typing import List, Optional, TYPE_CHECKING
from enum import Enum, auto
from random import sample
from dataclasses import dataclass

if TYPE_CHECKING:
    from agent import Agent
    from game import TurnView, GameView

class Card(Enum):
    DUKE = auto()
    ASSASSIN = auto()
    CAPTAIN = auto()
    AMBASSADOR = auto()
    CONTESSA = auto()

    def __repr__(self):
        return self.name

class Move(Enum):
    INCOME = auto()
    FOREIGN_AID = auto()
    COUP = auto()
    TAX = auto()
    ASSASSINATE = auto()
    STEAL = auto()
    EXCHANGE = auto()

    def enabled_by(self, card: Card):
        if self in [Move.INCOME, Move.FOREIGN_AID, Move.COUP]:
            return True
        elif self == Move.TAX:
            return card == Card.DUKE
        elif self == Move.ASSASSINATE:
            return card == Card.ASSASSIN
        elif self == Move.STEAL:
            return card == Card.CAPTAIN
        elif self == Move.EXCHANGE:
            return card == Card.AMBASSADOR
    
    def blockable_by(self, card: Card):
        if self == Move.FOREIGN_AID:
            return card == Card.DUKE
        elif self == Move.ASSASSINATE:
            return card == Card.CONTESSA
        elif self == Move.STEAL:
            return card in [Card.CAPTAIN, Card.AMBASSADOR]

@dataclass
class Action:
    acting_player: "Player"
    move: Move
    target_player: Optional["Player"] = None

@dataclass
class ActionInfo:
    move: Move
    target_player_index: Optional[int] = None

class Player:
    def __init__(self, agent: "Agent", cards: List[Card], starting_coins: int = 2):
        self.agent = agent
        self.cards = cards
        self.coins = starting_coins

    def alive(self):
        return len(self.cards) > 0
    
    def get_action_info(self) -> "ActionInfo":
        return self.agent.get_action_info()
    
    def get_challenge_decision(self, action_info: "ActionInfo") -> bool:
        return self.agent.get_challenge_decision(action_info)
    
    def get_block_decision(self, action_info: "ActionInfo") -> bool:
        return self.agent.get_block_decision(action_info)
    
    def get_block_challenge_decision(self, action_info: "ActionInfo") -> bool:
        return self.agent.get_block_challenge_decision(action_info)
    
    def observe(self, turn_view: "TurnView", game_view: "GameView"):
        self.agent.observe(turn_view, game_view)
    
    def __repr__(self):
        return f"Player(coins={self.coins}, cards={self.cards})"