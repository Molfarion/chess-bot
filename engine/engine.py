import chess
import chess.polyglot
import random

PIECES_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

PASSED_PAWN_BONUS = [0, 10, 20, 30, 45, 60, 80, 0]

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

NULL_MOVE_REDUCTION = 2

ASPIRATION_DELTA = 200

FULL_DEPTH_MOVES = 3   
LMR_MIN_DEPTH   = 2 

class Agent:
    def __init__(self, method="minimax"):
        self.method = method
        self.nodes_searched = 0
        self.transposition_table = {}
        self.tt_hits = 0

    def game_phase(self, board):
        """0.0 = endgame, 1.0 = full middlegame. Based on remaining material."""
        phase_material = (
            len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK))
        ) * 300 + (
            len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK))
        ) * 300 + (
            len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK))
        ) * 500 + (
            len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
        ) * 900
        return min(1.0, phase_material / 6200)
    
    def _pawn_structure(self, board, color):
        """Score pawn structure for one side. Returns centipawns (positive = good)."""
        score = 0
        pawns = board.pieces(chess.PAWN, color)
        enemy_pawns = board.pieces(chess.PAWN, not color)

        pawn_files = [chess.square_file(sq) for sq in pawns]

        for sq in pawns:
            f = chess.square_file(sq)
            r = chess.square_rank(sq)
            if color == chess.BLACK:
                r = 7 - r  

            if pawn_files.count(f) > 1:
                score -= 20

            adjacent = [p for p in pawn_files if p in (f - 1, f + 1)]
            if not adjacent:
                score -= 15

            if color == chess.WHITE:
                blockers = [ep for ep in enemy_pawns
                            if chess.square_file(ep) in (f - 1, f, f + 1)
                            and chess.square_rank(ep) > r]
            else:
                blockers = [ep for ep in enemy_pawns
                            if chess.square_file(ep) in (f - 1, f, f + 1)
                            and chess.square_rank(ep) < chess.square_rank(sq)]
            if not blockers:
                score += PASSED_PAWN_BONUS[min(r, 7)]

        return score

    def _king_safety(self, board, color, phase):
        """Penalty for exposed king. Scaled by game phase (irrelevant in endgame)."""
        if phase < 0.2:
            return 0  # endgame — king activity matters more than shelter

        king_sq = board.king(color)
        if king_sq is None:
            return 0

        king_file = chess.square_file(king_sq)
        king_rank = chess.square_rank(king_sq)
        penalty = 0

        # Pawn shield: count friendly pawns in the 3 files in front of the king
        shield_rank = king_rank + 1 if color == chess.WHITE else king_rank - 1
        for df in (-1, 0, 1):
            f = king_file + df
            if not (0 <= f <= 7):
                continue
            shield_sq = chess.square(f, shield_rank) if 0 <= shield_rank <= 7 else None
            if shield_sq is None or board.piece_at(shield_sq) != chess.Piece(chess.PAWN, color):
                penalty -= 20

        # Open file in front of king
        for df in (-1, 0, 1):
            f = king_file + df
            if not (0 <= f <= 7):
                continue
            friendly_on_file = any(
                chess.square_file(sq) == f
                for sq in board.pieces(chess.PAWN, color)
            )
            if not friendly_on_file:
                penalty -= 15  # open file near king is dangerous

        return int(penalty * phase)

    def evaluate(self, board, depth=0):
        if board.is_checkmate():
            return -100000 - depth if board.turn == chess.WHITE else 100000 + depth
        elif board.is_game_over():
            return 0

        score = 0
        phase = self.game_phase(board)

        # --- Material + PST (existing logic, unchanged) ---
        for piece_type in PIECES_VALUES:
            white_pieces = board.pieces(piece_type, chess.WHITE)
            black_pieces = board.pieces(piece_type, chess.BLACK)
            value = PIECES_VALUES[piece_type]
            pst_table = PST_MAP[piece_type]
            for sq in white_pieces:
                score += value + pst_table[sq]
            for sq in black_pieces:
                score -= (value + pst_table[chess.square_mirror(sq)])

        # Count legal moves for the side to move, then flip and count for the other
        white_mobility = sum(1 for _ in board.generate_legal_moves()) if board.turn == chess.WHITE else 0
        board.push(chess.Move.null())
        black_mobility = sum(1 for _ in board.generate_legal_moves()) if board.turn == chess.BLACK else 0
        board.pop()
        # If it was Black's turn initially, swap
        if board.turn == chess.BLACK:
            white_mobility, black_mobility = black_mobility, white_mobility
        score += 5 * (white_mobility - black_mobility)

        # --- Pawn structure ---
        score += self._pawn_structure(board, chess.WHITE)
        score -= self._pawn_structure(board, chess.BLACK)

        # --- King safety ---
        score += self._king_safety(board, chess.WHITE, phase)
        score -= self._king_safety(board, chess.BLACK, phase)

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
            return self.evaluate(board, depth)

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
            return self.evaluate(board, depth)

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
            return self.evaluate(board, depth)

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

    def negamax(self, board, depth, alpha, beta, null_move_allowed=True, lmr_allowed=True):
        self.nodes_searched += 1
        original_alpha = alpha

        state_key = chess.polyglot.zobrist_hash(board)
        tt_entry  = self.transposition_table.get(state_key)

        if tt_entry is not None and tt_entry['depth'] >= depth:
            self.tt_hits += 1
            if tt_entry['flag'] == 'EXACT':
                return tt_entry['score']
            elif tt_entry['flag'] == 'LOWERBOUND':
                alpha = max(alpha, tt_entry['score'])
            elif tt_entry['flag'] == 'UPPERBOUND':
                beta = min(beta, tt_entry['score'])
            if alpha >= beta:
                return tt_entry['score']

        if board.is_game_over():
            score = self.evaluate(board)
            return score if board.turn == chess.WHITE else -score

        if depth <= 0:
            return self.quiescence(board, alpha, beta)

        # Null-move pruning
        is_endgame = self.game_phase(board) < 0.2
        if (null_move_allowed
                and not board.is_check()
                and not is_endgame
                and depth >= NULL_MOVE_REDUCTION + 1):
            board.push(chess.Move.null())
            null_score = -self.negamax(
                board, depth - 1 - NULL_MOVE_REDUCTION,
                -beta, -beta + 1,
                null_move_allowed=False
            )
            board.pop()
            if null_score >= beta:
                return beta

        moves = list(board.legal_moves)
        best_move_tt = tt_entry['best_move'] if tt_entry else None
        best_move_current = None

        moves.sort(key=lambda m: 1000000 if m == best_move_tt else self.score_move(board, m), reverse=True)

        max_eval = -float('inf')
        
        for i, move in enumerate(moves):
            is_capture   = board.is_capture(move)
            is_promotion = move.promotion is not None
            board.push(move)
            gives_check  = board.is_check()

            reduce = (
                lmr_allowed
                and depth >= LMR_MIN_DEPTH
                and i >= FULL_DEPTH_MOVES
                and not is_capture
                and not gives_check
                and not is_promotion
            )

            if reduce:
                reduction = 1 if i < 8 else 2
                eval_score = -self.negamax(
                    board, depth - 1 - reduction, -alpha - 1, -alpha,
                    lmr_allowed=False
                )
                if eval_score > alpha:
                    eval_score = -self.negamax(
                        board, depth - 1, -beta, -alpha,
                        lmr_allowed=False
                    )
            else:
                eval_score = -self.negamax(board, depth - 1, -beta, -alpha)
                
            board.pop()
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move_current = move
                
            alpha = max(alpha, eval_score)
            if alpha >= beta:
                break

        flag = ('EXACT' if original_alpha < max_eval < beta
                else 'UPPERBOUND' if max_eval <= original_alpha
                else 'LOWERBOUND')
                
        self.transposition_table[state_key] = {
            'score': max_eval, 'depth': depth,
            'flag': flag, 'best_move': best_move_current
        }
        return max_eval

    def iterative_deepening(self, board, max_depth):
        best_move = None
        prev_score = 0
        for d in range(1, max_depth + 1):
            if d <= 2:
                alpha = -float('inf')
                beta  = float('inf')
            else:
                alpha = prev_score - ASPIRATION_DELTA
                beta  = prev_score + ASPIRATION_DELTA
                
            while True:
                score = self.negamax(board, d, alpha, beta)
                
                if score <= alpha:
                    alpha = -float('inf')  # Failed low, widen lower bound
                elif score >= beta:
                    beta = float('inf')    # Failed high, widen upper bound
                else:
                    prev_score = score     # Exact score found within window
                    break
                    
            state_key = chess.polyglot.zobrist_hash(board)
            tt_entry = self.transposition_table.get(state_key)
            if tt_entry and tt_entry['best_move']:
                best_move = tt_entry['best_move']
                
        return best_move

    def find_move(self, board, depth=4):
        self.nodes_searched = 0
        self.tt_hits = 0
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        if len(self.transposition_table) > 100000:
            self.transposition_table.clear()

        if self.method == "random":
            return random.choice(legal_moves)

        if self.method == "negamax_tt":
            return self.iterative_deepening(board, depth)

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

    for method in ["minimax", "minimax_ab", "minimax_ab_qs", "negamax_tt"]:
        agent = Agent(method=method)
        move = agent.find_move(board, depth=4)
        print(f"[{method}] move={move}, nodes={agent.nodes_searched}")