from typing import Optional, TYPE_CHECKING

from game_elements import ActionInfo, Move

if TYPE_CHECKING:
    from game import TurnView, GameView

class Agent:
    def load_initial_game_view(self, game_view: "GameView"):
        self.coins = game_view.observer_coins
        self.cards = game_view.observer_cards
        self.other_player_coins = game_view.other_player_coins
        self.other_player_card_counts = game_view.other_player_card_counts

    def get_action_info(self) -> "ActionInfo":
        raise NotImplementedError()
    
    def get_challenge_decision(self, action_info: "ActionInfo") -> bool:
        raise NotImplementedError()

    def get_block_decision(self, action_info: "ActionInfo") -> bool:
        raise NotImplementedError()
    
    def get_block_challenge_decision(self, action_info: "ActionInfo") -> bool:
        raise NotImplementedError()
    
    def observe(self, turn_view: "TurnView", game_view: "GameView"):
        self.coins = game_view.observer_coins
        self.cards = game_view.observer_cards
        self.other_player_coins = game_view.other_player_coins
        self.other_player_card_counts = game_view.other_player_card_counts

    def __repr__(self):
        return f"{self.__class__.__name__}({self.coins=}, {self.cards=}, {self.other_player_coins=}, {self.other_player_card_counts=})"

# class RandomAgent(Agent):
#     def __init__(self):
#         super().__init__()
    
#     def get_action_info(self) -> ActionInfo:

class IncomeAgent(Agent):
    def load_initial_game_view(self, game_view: "GameView"):
        return super().load_initial_game_view(game_view)

    def get_action_info(self) -> "ActionInfo":
        if self.coins < 7:
            return ActionInfo(move=Move.INCOME)
        else:
            return ActionInfo(move=Move.COUP, target_player_index=1)
    
    def get_challenge_decision(self, action_info: "ActionInfo") -> bool:
        return False

    def get_block_decision(self, action_info: "ActionInfo") -> bool:
        return False
    
    def get_block_challenge_decision(self, action_info: "ActionInfo") -> bool:
        return False
    
    def observe(self, turn_view: "TurnView", game_view: "GameView"):
        super().observe(turn_view=turn_view, game_view=game_view)

    def __repr__(self):
        return super().__repr__()