import chess
import random

class Agent:
    def __init__(self, method="random"):
        self.method = method
    
    def find_move(self, board):
        if self.method == "random":
            legal_moves = list(board.legal_moves)
            if legal_moves:
                return random.choice(legal_moves)
        return None

board = chess.Board()
agent = Agent()

move = agent.find_move(board)