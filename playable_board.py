import pygame
import chess
import sys
import os

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

def get_font(name, size, bold=False):
    for font_option in [name, "dejavusans", "freesans", "segoeuisymbol", "arial", "courier"]:
        try:
            return pygame.font.SysFont(font_option, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)

font_ui_large = get_font("sans-serif", 26)
font_ui_medium = get_font("sans-serif", 17)
font_ui_small = get_font("sans-serif", 13)
font_pieces = get_font("dejavusans", 38)

font_hud_heading = get_font("sans-serif", 21, bold=True)
font_hud_text = get_font("sans-serif", 16)

def load_piece_images():
    """Loads piece images from assets/pieces directory and scales them."""
    global PIECE_IMAGES
    PIECE_IMAGES.clear()
    
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "pieces")
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

def draw_transparent_circle(surface, color, center, radius):
    """Draws a translucent circle with an alpha channel."""
    temp_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(temp_surf, color, (radius, radius), radius)
    surface.blit(temp_surf, (center[0] - radius, center[1] - radius))

def draw_transparent_circle_ring(surface, color, center, radius, width=6):
    """Draws a translucent circular ring (unfilled) with an alpha channel."""
    temp_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(temp_surf, color, (radius, radius), radius, width)
    surface.blit(temp_surf, (center[0] - radius, center[1] - radius))

def draw_board_squares(win, board, selected_square):
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
    """Draws the pieces on the board using PNGs with a robust styled unicode fallback."""
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

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess")
    clock = pygame.time.Clock()

    load_piece_images()

    board = chess.Board()
    
    selected_square = None

    run = True
    while run:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                elif event.key == pygame.K_r:
                    board.reset()
                    selected_square = None

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
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
                                last_move = move
                                selected_square = None
                            elif chess.Move(selected_square, clicked_square, promotion=chess.QUEEN) in board.legal_moves:
                                promotion_move = chess.Move(selected_square, clicked_square, promotion=chess.QUEEN)
                                board.push(promotion_move)
                                last_move = promotion_move
                                selected_square = None
                            elif piece is not None and piece.color == board.turn:
                                selected_square = clicked_square
                            else:
                                selected_square = None

        screen.fill(COLOR_BACKGROUND)
        
        draw_board_squares(screen, board, selected_square)
        draw_legal_highlights(screen, board, selected_square)
        draw_pieces(screen, board)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
