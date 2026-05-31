import pygame, random, sys
from pygame.locals import *

# === CONFIGURACIÓN ===
TILE_SIZE = 40
GRID_WIDTH = 13
GRID_HEIGHT = 13
MINES_COUNT = 40
WIDTH = TILE_SIZE * GRID_WIDTH
HEIGHT = TILE_SIZE * GRID_HEIGHT

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MineSweeper")
clock = pygame.time.Clock()

# === COLORES ===
WHITE = (255, 255, 255)
GRAY = (225, 225, 225)
DARK_GRAY = (80, 80, 80)
DARKER_GRAY = (30, 30, 30)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 180, 0)

# Paleta estilo clásico
NUMBER_COLORS = {
    1: (0, 100, 255),     # Turquesa
    2: (0, 200, 0),       # Verde
    3: (255, 0, 0),       # Rojo
    4: (0, 0, 128),       # Azul oscuro
    5: (182, 128, 0),     # Marrón rojizo
    6: (0, 128, 128),     # Cian oscuro
    7: (0, 0, 0),         # Negro
    8: (128, 128, 128),   # Gris
}

font = pygame.font.SysFont(None, 40)

# === SPRITE BASE ===
class Sprite:
    def process(self): pass
    def draw(self): pass

# === CELDA ===
class Tile(Sprite):
    def __init__(self, x, y):
        self.grid_x = x
        self.grid_y = y
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.adjacent_mines = 0

    def draw(self):
        pygame.draw.rect(screen, DARK_GRAY if self.is_revealed else GRAY, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)

        # Si el juego terminó, y la mina es revelada, la pintamos en negro
        if self.is_revealed:
            if self.is_mine:
                # Si el juego terminó, colorea la mina de negro, si no está marcada con bandera
                color = BLACK if manager.game_over else DARKER_GRAY
                pygame.draw.circle(screen, color, self.rect.center, TILE_SIZE // 4)
            elif self.adjacent_mines > 0:
                text = font.render(str(self.adjacent_mines), True, NUMBER_COLORS[self.adjacent_mines])
                screen.blit(text, text.get_rect(center=self.rect.center))
        elif self.is_flagged:
            pygame.draw.circle(screen, RED, self.rect.center, TILE_SIZE // 4)

        # Si la mina no está revelada y el juego terminó, dibujarla en negro
        if manager.game_over and self.is_mine and not self.is_revealed:
            pygame.draw.circle(screen, BLACK, self.rect.center, TILE_SIZE // 4)  # Dibuja en negro


    def reveal(self):
        if self.is_flagged or self.is_revealed:
            return
        self.is_revealed = True
        manager.revealed_count += 1
        if self.adjacent_mines == 0 and not self.is_mine:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = self.grid_x + dx, self.grid_y + dy
                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                        neighbor = grid[ny][nx]
                        if not neighbor.is_revealed:
                            neighbor.reveal()

# === MANAGER ===
class GameManager(Sprite):
    def __init__(self):
        self.reset()

    def reset(self):
        global grid
        self.grid_ready = False
        self.game_over = False
        self.victory = False
        self.revealed_count = 0
        grid = [[Tile(x, y) for x in range(GRID_WIDTH)] for y in range(GRID_HEIGHT)]

    def place_mines(self, first_click_tile):
        safe_zone = self.get_neighbors(first_click_tile) | {first_click_tile}
        all_tiles = set(tile for row in grid for tile in row)  # Convertimos all_tiles a un set
        candidates = all_tiles - safe_zone  # Ahora usamos un set para restar safe_zone

        visited = set()  # Iniciamos visited antes de usarlo
        placed = 0

        while placed < MINES_COUNT:
            # Decidimos aleatoriamente si colocar una mina suelta o un cluster
            if random.random() < 0.2:  # 20% de chance de que sea un cluster
                start = random.choice(list(candidates))  # Seleccionamos aleatoriamente de los candidatos
                if start in visited:
                    continue
                cluster_size = random.randint(3, 5)
                cluster = self.generate_mine_cluster(start, candidates - visited, cluster_size)
                for tile in cluster:
                    tile.is_mine = True
                placed += len(cluster)
                visited.update(cluster)  # Actualizamos visited después de colocar las minas
            else:  # 50% de chance de que sea una mina suelta
                start = random.choice(list(candidates))
                if start in visited:
                    continue
                start.is_mine = True
                placed += 1
                visited.add(start)  # Marcamos la mina suelta como visitada

        self.calculate_adjacency()
        self.grid_ready = True

    def generate_mine_cluster(self, start_tile, candidates, max_size):  # NUEVO
        cluster = set([start_tile])
        frontier = [start_tile]

        while frontier and len(cluster) < max_size:
            current = frontier.pop()
            for neighbor in self.get_neighbors(current):
                if neighbor in candidates and neighbor not in cluster:
                    cluster.add(neighbor)
                    frontier.append(neighbor)
                    if len(cluster) >= max_size:
                        break
        return cluster

    def calculate_adjacency(self):
        for row in grid:
            for tile in row:
                count = 0
                for neighbor in self.get_neighbors(tile):
                    if neighbor.is_mine:
                        count += 1
                tile.adjacent_mines = count

    def get_neighbors(self, tile):
        neighbors = set()
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = tile.grid_x + dx, tile.grid_y + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    neighbors.add(grid[ny][nx])
        return neighbors

    def process_click(self, mouse_pos, right_click=False):
        if self.game_over or self.victory:
            return

        for row in grid:
            for tile in row:
                if tile.rect.collidepoint(mouse_pos):
                    if not self.grid_ready:
                        self.place_mines(tile)
                    if right_click:
                        if not tile.is_revealed:
                            tile.is_flagged = not tile.is_flagged
                    else:
                        if not tile.is_revealed and not tile.is_flagged:
                            tile.reveal()
                            if tile.is_mine:
                                self.game_over = True
                                self.reveal_all_tiles()
                    self.check_victory()
                    return

    def check_victory(self):
        total_tiles = GRID_WIDTH * GRID_HEIGHT
        if self.revealed_count == total_tiles - MINES_COUNT:
            self.victory = True

    def draw(self):
        for row in grid:
            for tile in row:
                tile.draw()
        if self.game_over:
            self.show_message("Game Over!", RED)
        elif self.victory:
            self.show_message("You Win!", GREEN)

    def show_message(self, text, color):
        # Renderizar el texto
        render = font.render(text, True, WHITE)  # Color blanco para el texto
        text_rect = render.get_rect(center=(WIDTH // 2, HEIGHT // 2))  # Centrar el texto

        # Crear un fondo sólido detrás del texto
        background_rect = pygame.Rect(text_rect.x - 10, text_rect.y - 10, text_rect.width + 20, text_rect.height + 20)
        
        # Dibujar el fondo sólido (puedes cambiar el color de fondo a lo que prefieras)
        pygame.draw.rect(screen, color, background_rect)

        # Dibujar el texto encima del fondo
        screen.blit(render, text_rect)

    def reveal_all_tiles(self):
        for row in grid:
            for tile in row:
                tile.is_revealed = True

# === INSTANCIACIÓN ===
manager = GameManager()

# === LOOP PRINCIPAL ===
while True:
    deltaT = clock.tick(60) / 1000.0
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:  # Left
                manager.process_click(event.pos, right_click=False)
            elif event.button == 3:  # Right
                manager.process_click(event.pos, right_click=True)
        elif event.type == KEYDOWN:
            if event.key == K_r:
                manager.reset()
            elif event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

    manager.draw()
    pygame.display.flip()
