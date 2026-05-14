import pygame
import chess
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.engine import Agent
import subprocess

class UCIEngineAgent:
    def __init__(self, script_path):
        self.script_path = script_path
        self.method = "sunfish"
        self.process = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.nodes_searched = 0
        self.send("uci")
        self.read_until("uciok")
        self.send("isready")
        self.read_until("readyok")

    def send(self, cmd):
        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()

    def read_until(self, expected):
        while True:
            line = self.process.stdout.readline().strip()
            if expected in line:
                return line

    def find_move(self, board, depth=3):
        self.send("ucinewgame")
        self.send("isready")
        self.read_until("readyok")
        
        moves_str = " ".join(m.uci() for m in board.move_stack)
        if moves_str:
            self.send(f"position startpos moves {moves_str}")
        else:
            self.send("position startpos")
            
        self.send(f"go depth {depth}")
        
        self.nodes_searched = 0
        while True:
            line = self.process.stdout.readline().strip()
            if line.startswith("info"):
                parts = line.split()
                if "nodes" in parts:
                    try:
                        nodes_idx = parts.index("nodes")
                        self.nodes_searched = int(parts[nodes_idx + 1])
                    except (ValueError, IndexError):
                        pass
            elif line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2 and parts[1] != "(none)":
                    return chess.Move.from_uci(parts[1])
                break
        return None

    def quit(self):
        try:
            self.send("quit")
        except Exception:
            pass
        self.process.terminate()

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1100, 750
BOARD_SIZE = 600
SQUARE_SIZE = BOARD_SIZE // 8
X_OFFSET = 50   
Y_OFFSET = (HEIGHT - BOARD_SIZE) // 2

COLOR_BACKGROUND = (22, 22, 26)       # Deep slate obsidian (#16161a)
COLOR_PANEL_BG = (31, 32, 38)         # Sleek charcoal slate (#1f2026)
COLOR_TEXT_MAIN = (240, 243, 246)     
COLOR_TEXT_MUTED = (160, 165, 175)    # Cool light grey
COLOR_TEXT_ACCENT = (242, 177, 52)    # Premium amber gold (#f2b134)
COLOR_HEADER_GREEN = (46, 204, 113)   # Vibrant HUD green (#2ecc71)

COLOR_LIGHT_SQ = (240, 217, 181)     # Warm cream maple (#f0d9b5)
COLOR_DARK_SQ = (181, 136, 99)       # Rich walnut brown (#b58863)

HL_SELECTED = (139, 195, 74, 130)       # Vibrant translucent green selection cell (high contrast)
HL_LAST_MOVE = (139, 195, 74, 80)       # Soft matching green for last move
HL_LEGAL_EMPTY = (139, 195, 74, 105)     # Clear green legal move cell
HL_LEGAL_CAPTURE = (235, 60, 60, 130)    # High contrast vibrant coral-red capture cell

COLOR_PIECE_WHITE_BG = (255, 255, 255) 
COLOR_PIECE_BLACK_BG = (40, 44, 52)    
COLOR_PIECE_WHITE_TEXT = (20, 20, 20)  
COLOR_PIECE_BLACK_TEXT = (240, 240, 240) 

UNICODE_PIECES = {
    'P': 'P', 'N': 'N', 'B': 'B', 'R': 'R', 'Q': 'Q', 'K': 'K',  
    'p': 'p', 'n': 'n', 'b': 'b', 'r': 'r', 'q': 'q', 'k': 'k', 
    'P_uni': '♟', 'N_uni': '♞', 'B_uni': '♝', 'R_uni': '♜', 'Q_uni': '♛', 'K_uni': '♚',
    'p_uni': '♟', 'n_uni': '♞', 'b_uni': '♝', 'r_uni': '♜', 'q_uni': '♛', 'k_uni': '♚'
}

PIECE_IMAGES = {}

PIECE_VALUES = {
    chess.QUEEN: 9, chess.ROOK: 5,
    chess.BISHOP: 3, chess.KNIGHT: 3, chess.PAWN: 1,
}
CAPTURE_ORDER = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]
UNICODE_GLYPHS = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚',
}

def get_font(name, size, bold=False):
    for font_option in [name, "roboto", "sans-serif", "dejavusans", "freesans", "segoeuisymbol", "arial", "courier"]:
        try:
            return pygame.font.SysFont(font_option, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)

font_ui_large = get_font("roboto", 26)
font_ui_medium = get_font("roboto", 17)
font_ui_small = get_font("roboto", 12)
font_pieces = get_font("dejavusans", 38)

font_hud_heading = get_font("roboto", 21, bold=True)
font_hud_text = get_font("roboto", 16)

def load_piece_images():
    """Loads piece images from assets/pieces directory and scales them."""
    global PIECE_IMAGES
    PIECE_IMAGES.clear()
    
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "pieces")
    if not os.path.exists(assets_dir):
        return False
        
    for color in ['w', 'b']:
        for piece_char in ['P', 'N', 'B', 'R', 'Q', 'K']:
            filename = f"{color}{piece_char}.png"
            filepath = os.path.join(assets_dir, filename)
            if os.path.exists(filepath):
                img = pygame.image.load(filepath).convert_alpha()
                scale_size = int(SQUARE_SIZE * 0.88)
                scaled_img = pygame.transform.smoothscale(img, (scale_size, scale_size))
                key = piece_char if color == 'w' else piece_char.lower()
                PIECE_IMAGES[key] = scaled_img

    
def draw_transparent_rect(surface, color, rect):
    """Draws a translucent rectangle with an alpha channel."""
    temp_surf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    temp_surf.fill(color)
    surface.blit(temp_surf, (rect[0], rect[1]))

def draw_board_squares(win, selected_square):
    """Draws the 8x8 squares, including selection borders and last-move highlights."""

    frame_color = (45, 45, 52)
    pygame.draw.rect(win, frame_color, (X_OFFSET - 4, Y_OFFSET - 4, BOARD_SIZE + 8, BOARD_SIZE + 8), 2)

    for row in range(8):
        for col in range(8):
            
            square = chess.square(col, 7 - row)
            
            base_color = COLOR_LIGHT_SQ if (row + col) % 2 == 0 else COLOR_DARK_SQ
            x = X_OFFSET + col * SQUARE_SIZE
            y = Y_OFFSET + row * SQUARE_SIZE
            
            pygame.draw.rect(win, base_color, (x, y, SQUARE_SIZE, SQUARE_SIZE))
             
            if square == selected_square:
                draw_transparent_rect(win, HL_SELECTED, (x, y, SQUARE_SIZE, SQUARE_SIZE))

def draw_legal_highlights(win, board, selected_square):
    """Highlights legal destination squares using premium translucent colored cells."""
    if selected_square is None:
        return

    legal_destinations = []
    for move in board.legal_moves:
        if move.from_square == selected_square:
            legal_destinations.append(move.to_square)

    for target_square in legal_destinations:
        col = chess.square_file(target_square)
        row = 7 - chess.square_rank(target_square)
        
        x = X_OFFSET + col * SQUARE_SIZE
        y = Y_OFFSET + row * SQUARE_SIZE

        piece_at_target = board.piece_at(target_square)
        if piece_at_target is not None:
            draw_transparent_rect(win, HL_LEGAL_CAPTURE, (x, y, SQUARE_SIZE, SQUARE_SIZE))
        else:
            draw_transparent_rect(win, HL_LEGAL_EMPTY, (x, y, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(win, board):
    """Draws the pieces on the board using PNGs."""
    for row in range(8):
        for col in range(8):
            square = chess.square(col, 7 - row)
            piece = board.piece_at(square)
            
            if piece is not None:
                x = X_OFFSET + col * SQUARE_SIZE
                y = Y_OFFSET + row * SQUARE_SIZE
                symbol = piece.symbol()
                
                if symbol in PIECE_IMAGES:
                    img = PIECE_IMAGES[symbol]
                    img_w, img_h = img.get_size()
                    piece_x = x + (SQUARE_SIZE - img_w) // 2
                    piece_y = y + (SQUARE_SIZE - img_h) // 2
                    win.blit(img, (piece_x, piece_y))

def get_square_from_coords(pos):
    """Converts Pygame click coordinates to a python-chess square index."""
    x, y = pos
    x_rel = x - X_OFFSET
    y_rel = y - Y_OFFSET

    if 0 <= x_rel < BOARD_SIZE and 0 <= y_rel < BOARD_SIZE:
        col = x_rel // SQUARE_SIZE
        row = y_rel // SQUARE_SIZE
        return chess.square(col, 7 - row)
    return None

def get_move_pairs(board):
    """Reconstructs the move history as a list of (move_number, white_move, black_move) tuples."""
    starting_fen = board.starting_fen if hasattr(board, 'starting_fen') else chess.STARTING_FEN
    temp_board = chess.Board(starting_fen)
    
    start_num = temp_board.fullmove_number
    is_white_first = (temp_board.turn == chess.WHITE)
    
    move_notations = []
    for move in board.move_stack:
        move_notations.append(temp_board.san(move))
        temp_board.push(move)
        
    pairs = []
    remaining_notations = list(move_notations)
    current_num = start_num
    
    # FEN loaded with black to move first
    if not is_white_first and remaining_notations:
        pairs.append((current_num, "...", remaining_notations[0]))
        remaining_notations = remaining_notations[1:]
        current_num += 1
        
    for i in range(0, len(remaining_notations), 2):
        w_move = remaining_notations[i]
        b_move = remaining_notations[i+1] if i+1 < len(remaining_notations) else ""
        pairs.append((current_num, w_move, b_move))
        current_num += 1
        
    return pairs

def get_captured_pieces(board):
    """Return (white_lost, black_lost) dicts of {piece_type: count} taken from each side."""
    starting_fen = board.starting_fen if hasattr(board, 'starting_fen') else chess.STARTING_FEN
    start = chess.Board(starting_fen)

    def counts(b):
        c = {chess.WHITE: {}, chess.BLACK: {}}
        for sq in chess.SQUARES:
            p = b.piece_at(sq)
            if p:
                c[p.color][p.piece_type] = c[p.color].get(p.piece_type, 0) + 1
        return c

    s, cur = counts(start), counts(board)
    white_lost, black_lost = {}, {}
    for pt in chess.PIECE_TYPES:
        dw = s[chess.WHITE].get(pt, 0) - cur[chess.WHITE].get(pt, 0)
        db = s[chess.BLACK].get(pt, 0) - cur[chess.BLACK].get(pt, 0)
        if dw > 0: white_lost[pt] = dw   
        if db > 0: black_lost[pt] = db   
    return white_lost, black_lost

def draw_captured_pieces(win, board):
    """
    Above board: white pieces captured by black.
    Below board: black pieces captured by white.
    Amber +N badge shows material advantage for the leading side.
    """
    white_lost, black_lost = get_captured_pieces(board)

    adv_white = sum(PIECE_VALUES.get(pt, 0) * n for pt, n in black_lost.items())
    adv_black = sum(PIECE_VALUES.get(pt, 0) * n for pt, n in white_lost.items())

    font_cap = get_font("dejavusans", 15)
    font_adv = get_font("roboto", 13)

    def render_row(losses, show_white_glyphs, y_pos, advantage):
        x = X_OFFSET
        for pt in CAPTURE_ORDER:
            cnt = losses.get(pt, 0)
            if cnt == 0:
                continue
            sym = chess.piece_symbol(pt)
            key = sym.upper() if show_white_glyphs else sym
            glyph = UNICODE_GLYPHS.get(key, "?")
            color = (215, 215, 215) if show_white_glyphs else (90, 90, 90)
            for _ in range(cnt):
                s = font_cap.render(glyph, True, color)
                win.blit(s, (x, y_pos))
                x += 17
        if advantage > 0:
            adv_s = font_adv.render(f"+{advantage}", True, COLOR_TEXT_ACCENT)
            win.blit(adv_s, (x + 4, y_pos + 1))

    render_row(white_lost, show_white_glyphs=True,  y_pos=Y_OFFSET - 22, advantage=adv_black)
    render_row(black_lost, show_white_glyphs=False, y_pos=Y_OFFSET + BOARD_SIZE + 6, advantage=adv_white)


def draw_status_info(win, board, scroll_index, bot=None, debug_mode=False, last_depth=3):
    """Draws a single status line and a scrollable recent move history on the right side."""
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        status_text = f"Checkmate — {winner} wins"
    elif board.is_stalemate():
        status_text = "Stalemate"
    elif board.is_insufficient_material():
        status_text = "Draw (Insufficient Material)"
    elif board.is_game_over():
        status_text = "Draw"
    elif board.is_check():
        status_text = "Check"
    else:
        status_text = "White to move" if board.turn == chess.WHITE else "Black to move"
        
    color_neutral = (180, 185, 195)
    font_status = get_font("roboto", 24)
    text_surf = font_status.render(status_text, True, color_neutral)
    
    x_pos = 730
    y_status = Y_OFFSET + 30
    win.blit(text_surf, (x_pos, y_status))
    if board.is_game_over():
        hint_surf = font_ui_small.render("Press R to restart", True, COLOR_TEXT_MUTED)
        win.blit(hint_surf, (x_pos, y_status + 30))
    
    pairs = get_move_pairs(board)
    
    y_history_hdr = y_status + 65
    hdr_surf = font_ui_small.render("HISTORY", True, COLOR_TEXT_MUTED)
    win.blit(hdr_surf, (x_pos, y_history_hdr))
    
    max_visible_rows = 15  # Shrunk slightly from 20 to guarantee perfect layout spacing with Debug panel
    visible_pairs = pairs[scroll_index : scroll_index + max_visible_rows]
    
    y_curr = y_history_hdr + 25
    for i, (num, w, b) in enumerate(visible_pairs):
        y_row = y_curr + i * 22
        
        num_str = f"{num}."
        num_surf = font_hud_text.render(num_str, True, COLOR_TEXT_MUTED)
        win.blit(num_surf, (x_pos, y_row))
        
        w_surf = font_hud_text.render(w, True, COLOR_TEXT_MAIN)
        win.blit(w_surf, (x_pos + 50, y_row))
        
        if b:
            b_surf = font_hud_text.render(b, True, COLOR_TEXT_MAIN)
            win.blit(b_surf, (x_pos + 130, y_row))
            
    if len(pairs) > max_visible_rows:
        track_y = y_history_hdr + 25
        track_height = max_visible_rows * 22 - 4
        
        # Calculate scroll thumb position and size
        thumb_height = max(30, int(track_height * (max_visible_rows / len(pairs))))
        scrollable_range = len(pairs) - max_visible_rows
        thumb_y = track_y + int((track_height - thumb_height) * (scroll_index / scrollable_range))
        
        # Draw track & thumb
        pygame.draw.rect(win, (35, 36, 42), (x_pos + 200, track_y, 4, track_height), border_radius=2)
        pygame.draw.rect(win, (100, 105, 115), (x_pos + 200, thumb_y, 4, thumb_height), border_radius=2)

    # Draw Debug Metrics Panel
    if debug_mode and bot is not None:
        # Draw a beautiful amber gold panel for Debug Info
        debug_rect = (x_pos, Y_OFFSET + BOARD_SIZE - 95, 320, 95)
        pygame.draw.rect(win, (35, 36, 42), debug_rect, border_radius=6)
        pygame.draw.rect(win, COLOR_TEXT_ACCENT, debug_rect, 1, border_radius=6)
        
        # Title
        title_surf = font_ui_small.render("DEBUG METRICS (Press D to disable)", True, COLOR_TEXT_ACCENT)
        win.blit(title_surf, (x_pos + 12, Y_OFFSET + BOARD_SIZE - 87))
        
        # Stats
        method_str = f"Search Method: {bot.method.upper()}"
        depth_str = f"Search Depth: {last_depth}"
        nodes_str = f"Moves Considered: {bot.nodes_searched:,}"
        
        method_surf = font_hud_text.render(method_str, True, COLOR_TEXT_MAIN)
        depth_surf = font_hud_text.render(depth_str, True, COLOR_TEXT_MAIN)
        nodes_surf = font_hud_text.render(nodes_str, True, COLOR_TEXT_MAIN)
        
        win.blit(method_surf, (x_pos + 12, Y_OFFSET + BOARD_SIZE - 68))
        win.blit(depth_surf, (x_pos + 12, Y_OFFSET + BOARD_SIZE - 48))
        win.blit(nodes_surf, (x_pos + 12, Y_OFFSET + BOARD_SIZE - 28))
        
        if hasattr(bot, 'tt_hits'):
            tt_size = len(bot.transposition_table) if hasattr(bot, 'transposition_table') else 0
            tt_str = f"TT Size: {tt_size:,} | Hits: {bot.tt_hits:,}"
            tt_surf = font_ui_small.render(tt_str, True, COLOR_HEADER_GREEN)
            win.blit(tt_surf, (x_pos + 12, Y_OFFSET + BOARD_SIZE - 10))
    else:
        # If debug is off, show a small hint at the bottom
        hint_surf = font_ui_small.render("Press D to enable Debug Metrics", True, COLOR_TEXT_MUTED)
        win.blit(hint_surf, (x_pos, Y_OFFSET + BOARD_SIZE - 20))

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess")
    clock = pygame.time.Clock()

    load_piece_images()

    starting_fen = chess.STARTING_FEN

    bot = Agent(method="minimax_ab_qs_tt")
    sunfish_bot = UCIEngineAgent("engine/sunfish.py")
    board = chess.Board(starting_fen)
    board.starting_fen = starting_fen
    
    selected_square = None

    scroll_index = 0
    prev_move_count = 0
    
    debug_mode = True
    last_depth = 4

    run = True
    while run:

        curr_move_count = len(board.move_stack)
        if curr_move_count != prev_move_count:
            pairs = get_move_pairs(board)
            scroll_index = max(0, len(pairs) - 20)
            prev_move_count = curr_move_count

        if not board.is_game_over() and board.turn == chess.BLACK:
            pygame.time.delay(100)

            if bot.method == "sunfish":
                bot_move = sunfish_bot.find_move(board, depth=4)
            else:
                bot_move = bot.find_move(board)
            
            if bot_move:
                board.push(bot_move)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                elif event.key == pygame.K_r:
                    board.set_fen(board.starting_fen)
                    selected_square = None
                elif event.key == pygame.K_f:
                    fen = board.fen()
                    print(f"Current FEN: {fen}")
                elif event.key == pygame.K_d:
                    debug_mode = not debug_mode
                elif event.key == pygame.K_m:
                    if bot.method == "minimax_ab":
                        bot.method = "minimax_ab_qs"
                    elif bot.method == "minimax_ab_qs":
                        bot.method = "minimax_ab_qs_tt"
                    elif bot.method == "minimax_ab_qs_tt":
                        bot.method = "minimax"
                    elif bot.method == "minimax":
                        bot.method = "sunfish"
                    elif bot.method == "sunfish":
                        bot.method = "random"
                    else:
                        bot.method = "minimax_ab"
                elif event.key == pygame.K_UP:
                    scroll_index = max(0, scroll_index - 1)
                elif event.key == pygame.K_DOWN:
                    pairs = get_move_pairs(board)
                    scroll_index = min(max(0, len(pairs) - 20), scroll_index + 1)

            elif event.type == pygame.MOUSEWHEEL:
                pairs = get_move_pairs(board)
                scroll_index = max(0, min(max(0, len(pairs) - 20), scroll_index - event.y))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    if board.is_game_over():
                        pass  
                    else:
                     clicked_square = get_square_from_coords(event.pos)
                     
                     if clicked_square is not None:
                         piece = board.piece_at(clicked_square)
                         
                         if selected_square is None:
                             if piece is not None and piece.color == board.turn:
                                 selected_square = clicked_square
                         
                         else:
                             move = chess.Move(selected_square, clicked_square)
                             
                             if move in board.legal_moves:
                                 board.push(move)
                                 selected_square = None
                             elif chess.Move(selected_square, clicked_square, promotion=chess.QUEEN) in board.legal_moves:
                                 promotion_move = chess.Move(selected_square, clicked_square, promotion=chess.QUEEN)
                                 board.push(promotion_move)
                                 selected_square = None
                             elif piece is not None and piece.color == board.turn:
                                 selected_square = clicked_square
                             else:
                                 selected_square = None
                elif event.button == 4:
                    scroll_index = max(0, scroll_index - 1)
                elif event.button == 5: 
                    pairs = get_move_pairs(board)
                    scroll_index = min(max(0, len(pairs) - 20), scroll_index + 1)

        pairs = get_move_pairs(board)
        scroll_index = max(0, min(scroll_index, len(pairs) - 20))

        screen.fill(COLOR_BACKGROUND)
        
        draw_board_squares(screen, selected_square)
        draw_legal_highlights(screen, board, selected_square)
        draw_pieces(screen, board)
        draw_captured_pieces(screen, board)
        active_bot = sunfish_bot if bot.method == "sunfish" else bot
        draw_status_info(screen, board, scroll_index, bot=active_bot, debug_mode=debug_mode, last_depth=last_depth)

        pygame.display.update()
        clock.tick(60)

    sunfish_bot.quit()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()