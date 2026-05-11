import pygame

WIDTH, HEIGHT = 1200, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = 80
BOARD_SIZE = ROWS * SQUARE_SIZE

BLACK = (0, 0, 0)
LIGHT_BROWN = (240, 217, 181)  
DARK_BROWN = (181, 136, 99)   

def draw_board(win):
    x_off = (WIDTH - BOARD_SIZE) // 2
    y_off = (HEIGHT - BOARD_SIZE) // 2

    win.fill(BLACK)

    for row in range(ROWS):
        for col in range(COLS):
            color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
            
            pygame.draw.rect(
                win, 
                color, 
                (x_off + col * SQUARE_SIZE, y_off + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            )

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chessbot")
    clock = pygame.time.Clock()
    
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        
        draw_board(screen)
        pygame.display.update()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()