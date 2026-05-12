import chess
import random

PIECES_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

class Agent:
    def __init__(self, method="minimax"):
        self.method = method
        self.nodes_searched = 0
    
    def evaluate(self, board):
        if board.is_checkmate():
            if board.turn == chess.WHITE:
                # White is checkmated 
                return -100000
            else:
                # Black is checkmated 
                return 100000
        elif board.is_game_over():
            # Stalemate, draw by insufficient material
            return 0

        def count_pieces(board):
            counts = {chess.WHITE: {}, chess.BLACK: {}}
            for sq in chess.SQUARES:
                p = board.piece_at(sq)
                if p:
                    counts[p.color][p.piece_type] = counts[p.color].get(p.piece_type, 0) + 1
            return counts
        
        pieces = count_pieces(board)
        white_material = 0
        black_material = 0
        for piece_type in chess.PIECE_TYPES:
            white_material += pieces[chess.WHITE].get(piece_type, 0) * PIECES_VALUES.get(piece_type, 0)
            black_material += pieces[chess.BLACK].get(piece_type, 0) * PIECES_VALUES.get(piece_type, 0)

        return white_material - black_material

    def minimax(self, board, depth, maximizing_player):
        self.nodes_searched += 1
        if depth == 0 or board.is_game_over():
            return self.evaluate(board)
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.minimax(board, depth - 1, False)
                board.pop()
                if eval_score > max_eval:
                    max_eval = eval_score
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.minimax(board, depth - 1, True)
                board.pop()
                if eval_score < min_eval:
                    min_eval = eval_score
            return min_eval

    def alpha_beta(self, board, depth, alpha, beta, maximizing_player):
        self.nodes_searched += 1
        if depth == 0 or board.is_game_over():
            return self.evaluate(board)
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.alpha_beta(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval_score = self.alpha_beta(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def find_move(self, board, depth=5):
        self.nodes_searched = 0
        if self.method == "random":
            legal_moves = list(board.legal_moves)
            if legal_moves:
                return random.choice(legal_moves)
        elif self.method == "minimax":
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return None
            
            best_move = None
            if board.turn == chess.WHITE:
                best_score = -float('inf')
                for move in legal_moves:
                    board.push(move)
                    score = self.minimax(board, depth - 1, False)
                    board.pop()
                    if score > best_score:
                        best_score = score
                        best_move = move
            else:
                best_score = float('inf')
                for move in legal_moves:
                    board.push(move)
                    score = self.minimax(board, depth - 1, True)
                    board.pop()
                    if score < best_score:
                        best_score = score
                        best_move = move
                        
            return best_move
        elif self.method == "minimax_ab":
            legal_moves = list(board.legal_moves)
            captures = list(board.generate_legal_captures)
            moves_mvv = captures + legal_moves
            if not legal_moves:
                return None
            
            best_move = None
            if board.turn == chess.WHITE:
                best_score = -float('inf')
                alpha = -float('inf')
                beta = float('inf')
                for move in legal_moves:
                    board.push(move)
                    score = self.alpha_beta(board, depth - 1, alpha, beta, False)
                    board.pop()
                    if score > best_score:
                        best_score = score
                        best_move = move
                    alpha = max(alpha, score)
            else:
                best_score = float('inf')
                alpha = -float('inf')
                beta = float('inf')
                for move in legal_moves:
                    board.push(move)
                    score = self.alpha_beta(board, depth - 1, alpha, beta, True)
                    board.pop()
                    if score < best_score:
                        best_score = score
                        best_move = move
                    beta = min(beta, score)
                        
            return best_move
        return None

if __name__ == "__main__":
    board = chess.Board()
    agent = Agent()

    move = agent.find_move(board)
    evaluation = agent.evaluate(board)
    print(f"Sample Move: {move}, Evaluation: {evaluation}")