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

def orient_pst(table):
    return [table[(7 - (sq // 8)) * 8 + (sq % 8)] for sq in range(64)]

PAWN_PST = orient_pst([
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
])

KNIGHT_PST = orient_pst([
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
])

BISHOP_PST = orient_pst([
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
])

ROOK_PST = orient_pst([
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
])

QUEEN_PST = orient_pst([
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  5,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
])

KING_PST = orient_pst([
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
])

PST_MAP = {
    chess.PAWN: PAWN_PST,
    chess.KNIGHT: KNIGHT_PST,
    chess.BISHOP: BISHOP_PST,
    chess.ROOK: ROOK_PST,
    chess.QUEEN: QUEEN_PST,
    chess.KING: KING_PST
}

class Agent:
    def __init__(self, method="minimax"):
        self.method = method
        self.nodes_searched = 0
        self.transposition_table = {}

    def evaluate(self, board):
        if board.is_checkmate():
            if board.turn == chess.WHITE:
                return -100000
            else:
                return 100000
        elif board.is_game_over():
            return 0

        score = 0
        for sq, piece in board.piece_map().items():
            value = PIECES_VALUES.get(piece.piece_type, 0)
            pst_table = PST_MAP.get(piece.piece_type)

            if piece.color == chess.WHITE:
                pst_val = pst_table[sq] if pst_table else 0
                score += value + pst_val
            else:
                mirrored_sq = chess.square_mirror(sq)
                pst_val_black = pst_table[mirrored_sq] if pst_table else 0
                score -= (value + pst_val_black)

        return score

    def score_move(self, board, move):
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            victim_val = PIECES_VALUES.get(victim.piece_type, 0) if victim else 0
            attacker = board.piece_at(move.from_square)
            attacker_val = PIECES_VALUES.get(attacker.piece_type, 0) if attacker else 0
            return 1000 + victim_val - attacker_val
        if move.promotion:
            return 900
        return 0
    def quiescence(self, board, alpha, beta, qs_depth = 3):
        """
        Search captures (and promotions) until the position is quiet,
        then return a static evaluation.
        """
        self.nodes_searched += 1
        
        eval_score = self.evaluate(board)
        stand_pat = eval_score if board.turn == chess.WHITE else -eval_score

        if qs_depth == 0:
            return stand_pat

        # Stand-pat: evaluate the position without making any more captures.
        # If it's already >= beta, prune immediately (opponent won't allow this).
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        # Only look at captures (and promotions) to keep the search focused.
        capture_moves = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
        capture_moves.sort(key=lambda m: self.score_move(board, m), reverse=True)

        for move in capture_moves:
            board.push(move)
            score = -self.quiescence(board, -beta, -alpha, qs_depth-1)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def minimax(self, board, depth, maximizing_player):
        self.nodes_searched += 1
        if depth == 0 or board.is_game_over():
            return self.evaluate(board)

        moves = sorted(board.legal_moves, key=lambda m: self.score_move(board, m), reverse=True)

        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                board.push(move)
                eval_score = self.minimax(board, depth - 1, False)
                board.pop()
                if eval_score > max_eval:
                    max_eval = eval_score
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
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

        moves = sorted(board.legal_moves, key=lambda m: self.score_move(board, m), reverse=True)

        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
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
            for move in moves:
                board.push(move)
                eval_score = self.alpha_beta(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def alpha_beta_qs(self, board, depth, alpha, beta, maximizing_player):
        """
        Alpha-beta that drops into quiescence search at depth 0 instead
        of calling evaluate() directly.
        """
        self.nodes_searched += 1

        if board.is_game_over():
            return self.evaluate(board)

        if depth == 0:
            # Hand off to quiescence instead of a raw static eval.
            # Note: quiescence uses negamax-style signs internally,
            # so we flip for the minimizing player.
            if maximizing_player:
                return self.quiescence(board, alpha, beta)
            else:
                return -self.quiescence(board, -beta, -alpha)

        moves = sorted(board.legal_moves, key=lambda m: self.score_move(board, m), reverse=True)

        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                board.push(move)
                eval_score = self.alpha_beta_qs(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                board.push(move)
                eval_score = self.alpha_beta_qs(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def find_move(self, board, depth=4):
        self.nodes_searched = 0
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        if self.method == "random":
            return random.choice(legal_moves)

        if self.method == "minimax":
            search_fn = lambda b, d, a, b_, maximizing: self.minimax(b, d, maximizing)
        elif self.method == "minimax_ab":
            search_fn = lambda b, d, a, b_, maximizing: self.alpha_beta(b, d, a, b_, maximizing)
        elif self.method == "minimax_ab_qs":
            search_fn = lambda b, d, a, b_, maximizing: self.alpha_beta_qs(b, d, a, b_, maximizing)
        else:
            return random.choice(legal_moves)

        legal_moves.sort(key=lambda m: self.score_move(board, m), reverse=True)

        best_move = None
        if board.turn == chess.WHITE:
            best_score = -float('inf')
            alpha = -float('inf')
            beta = float('inf')
            for move in legal_moves:
                board.push(move)
                score = search_fn(board, depth - 1, alpha, beta, False)
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
                score = search_fn(board, depth - 1, alpha, beta, True)
                board.pop()
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, score)

        return best_move


if __name__ == "__main__":
    board = chess.Board()

    for method in ["minimax", "minimax_ab", "minimax_ab_qs"]:
        agent = Agent(method=method)
        move = agent.find_move(board, depth=4)
        print(f"[{method}] move={move}, nodes={agent.nodes_searched}")