from typing import Optional, TYPE_CHECKING

from game_elements import ActionInfo, Move

if TYPE_CHECKING:
    from game import TurnView, GameView

class Agent:
    def __init__(self):
        pass

    def get_action_info(self) -> "ActionInfo":
        raise NotImplementedError()
    
    def get_challenge_decision(self, action_info: "ActionInfo") -> bool:
        raise NotImplementedError()

    def get_block_decision(self, action_info: "ActionInfo") -> bool:
        raise NotImplementedError()
    
    def get_block_challenge_decision(self, action_info: "ActionInfo") -> bool:
        raise NotImplementedError()
    
    def observe(self, turn_view: "TurnView", game_view: "GameView"):
        raise NotImplementedError()

# class RandomAgent(Agent):
#     def __init__(self):
#         super().__init__()
    
#     def get_action_info(self) -> ActionInfo:

class IncomeAgent(Agent):
    def __init__(self):
        super().__init__()
    
    def get_action_info(self) -> "ActionInfo":
        return ActionInfo(move=Move.INCOME)
    
    def get_challenge_decision(self, action_info: "ActionInfo") -> bool:
        return False

    def get_block_decision(self, action_info: "ActionInfo") -> bool:
        return False
    
    def get_block_challenge_decision(self, action_info: "ActionInfo") -> bool:
        return False
    
    def observe(self, turn_view: "TurnView", game_view: "GameView"):
        pass