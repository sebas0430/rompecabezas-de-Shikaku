"""
gui.py  –  Interfaz gráfica del rompecabezas Shikaku usando Pygame.

Modos:
  - Humano: el jugador hace clic para definir rectángulos.
  - Sintético: el solucionador de backtracking resuelve el tablero.
"""

from __future__ import annotations
import sys
import time
import threading
import copy
import pygame
from shikaku import (
    ShikakuBoard, ShikakuSolver, Clue, Rect, EXAMPLE_PUZZLES
)

# ---------------------------------------------------------------------------
# Paleta de colores - Premium Dark Theme
# ---------------------------------------------------------------------------
BG          = (15, 17, 26)      # Deep Midnight
PANEL_BG    = (24, 26, 38)      # Sleek Charcoal
SIDE_BAR_L  = (35, 38, 55)      # Side bar border
ACCENT      = (78, 150, 255)    # Modern Cyan-Blue
ACCENT_LOW  = (40, 60, 100)
GRID_LINE   = (40, 42, 58)
GRID_BOLD   = (65, 70, 95)
WHITE       = (245, 245, 250)
BLACK       = (10, 10, 15)
TEXT_DIM    = (140, 150, 175)
TEXT_MAIN   = (220, 230, 255)
CLUE_BG     = (32, 35, 50)
CLUE_BORDER = (60, 65, 90)
NUMBER_COL  = (255, 255, 255)

RECT_COLORS = [
    (100, 180, 255), (140, 110, 250), (255, 110, 150),
    (110, 230, 180), (255, 180, 100), (200, 130, 255),
    (130, 255, 240), (255, 240, 110), (255, 150, 110),
]

BTN_NORMAL  = (50, 55, 80)
BTN_HOVER   = (70, 110, 230)
BTN_PRIMARY = (78, 120, 255)
BTN_DANGER  = (220, 70, 85)
BTN_SUCCESS = (50, 180, 110)

MSG_OK     = (80, 220, 130)
MSG_ERR    = (255, 90, 110)
MSG_INFO   = (130, 170, 255)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def draw_rounded_rect(surface, color, rect, radius=8, border=0, border_color=BLACK):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)


def draw_text_centered(surface, font, text, color, rect):
    surf = font.render(text, True, color)
    x = rect[0] + (rect[2] - surf.get_width()) // 2
    y = rect[1] + (rect[3] - surf.get_height()) // 2
    surface.blit(surf, (x, y))


# ---------------------------------------------------------------------------
# Botón simple
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, x, y, w, h, label, font, color=BTN_NORMAL, hover_color=BTN_HOVER, primary=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.font = font
        self.color = color if not primary else BTN_PRIMARY
        self.hover_color = hover_color if not primary else (90, 140, 255)
        self.hovered = False
        self.enabled = True
        self.primary = primary

    def draw(self, surface):
        col = self.hover_color if (self.hovered and self.enabled) else self.color
        if not self.enabled:
            col = tuple(c * 0.5 for c in self.color)
        
        # Subtle shadow
        shadow_rect = self.rect.move(0, 2)
        pygame.draw.rect(surface, (10, 10, 15), shadow_rect, border_radius=8)
        
        draw_rounded_rect(surface, col, self.rect, radius=8)
        
        # Shiny top border for primary buttons
        if self.primary and not self.hovered:
            shine = pygame.Rect(self.rect.x, self.rect.y, self.rect.w, self.rect.h // 2)
            s = pygame.Surface((shine.width, shine.height), pygame.SRCALPHA)
            s.fill((255, 255, 255, 20))
            surface.blit(s, (shine.x, shine.y))
            
        text_col = WHITE if self.enabled else (120, 120, 130)
        draw_text_centered(surface, self.font, self.label, text_col, self.rect)

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event) -> bool:
        return (self.enabled and
                event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and
                self.rect.collidepoint(event.pos))


# ---------------------------------------------------------------------------
# Selector de puzzle (menú lateral)
# ---------------------------------------------------------------------------
class PuzzleSelector:
    def __init__(self, x, y, w, font_sm):
        self.x = x
        self.y = y
        self.w = w
        self.font = font_sm
        self.names = list(EXAMPLE_PUZZLES.keys())
        self.selected = 0
        self.item_h = 32

    def draw(self, surface):
        for i, name in enumerate(self.names):
            rect = pygame.Rect(self.x, self.y + i * self.item_h, self.w, self.item_h - 6)
            is_sel = (i == self.selected)
            color = BTN_PRIMARY if is_sel else BTN_NORMAL
            tc = WHITE if is_sel else TEXT_DIM
            
            draw_rounded_rect(surface, color, rect, radius=6)
            if is_sel:
                # Active indicator
                pygame.draw.rect(surface, ACCENT, rect, 2, border_radius=6)
            
            draw_text_centered(surface, self.font, name, tc, rect)

    def click(self, pos) -> bool:
        for i in range(len(self.names)):
            rect = pygame.Rect(self.x, self.y + i * self.item_h, self.w, self.item_h - 4)
            if rect.collidepoint(pos):
                self.selected = i
                return True
        return False

    @property
    def current_board(self) -> ShikakuBoard:
        orig = EXAMPLE_PUZZLES[self.names[self.selected]]
        return ShikakuBoard(
            orig.rows, orig.cols,
            [Clue(c.row, c.col, c.n) for c in orig.clues]
        )


# ---------------------------------------------------------------------------
# Vista del tablero
# ---------------------------------------------------------------------------
class BoardView:
    CELL = 60   # tamaño de celda en píxeles

    def __init__(self, board: ShikakuBoard, ox: int, oy: int):
        self.board = board
        self.ox = ox   # offset x en pantalla
        self.oy = oy   # offset y en pantalla
        self.cell = self.CELL

        # Estado del jugador humano
        self.player_rects: list[Rect] = []       # rectángulos confirmados
        self.start_cell: tuple[int, int] | None = None  # celda de inicio del arrastre
        self.hover_cell: tuple[int, int] | None = None

        # Colores asignados a cada rectángulo
        self._color_map: dict[int, tuple] = {}
        self._color_idx = 0

    # ---- conversión píxel ↔ celda ----
    def px_to_cell(self, px, py) -> tuple[int, int] | None:
        c = (px - self.ox) // self.cell
        r = (py - self.oy) // self.cell
        if 0 <= r < self.board.rows and 0 <= c < self.board.cols:
            return r, c
        return None

    def cell_rect(self, r, c) -> pygame.Rect:
        return pygame.Rect(
            self.ox + c * self.cell,
            self.oy + r * self.cell,
            self.cell, self.cell
        )

    # ---- asignación de colores ----
    def _next_color(self) -> tuple:
        col = RECT_COLORS[self._color_idx % len(RECT_COLORS)]
        self._color_idx += 1
        return col

    def _get_color(self, idx: int) -> tuple:
        if idx not in self._color_map:
            self._color_map[idx] = self._next_color()
        return self._color_map[idx]

    # ---- dibujo ----
    def draw(self, surface, font_num, font_sm, show_solution=False):
        rows, cols = self.board.rows, self.board.cols
        cell = self.cell

        # Outer Board Shadow/Border
        outer_rect = pygame.Rect(self.ox - 4, self.oy - 4, cols * cell + 8, rows * cell + 8)
        pygame.draw.rect(surface, GRID_BOLD, outer_rect, border_radius=10)
        board_surf_rect = pygame.Rect(self.ox, self.oy, cols * cell, rows * cell)
        pygame.draw.rect(surface, BG, board_surf_rect)

        # Draw rects
        rects_to_draw = self.board.solution if show_solution else self.player_rects
        for idx, rect in enumerate(rects_to_draw):
            col = self._get_color(idx)
            px = pygame.Rect(
                self.ox + rect.col * cell + 4,
                self.oy + rect.row * cell + 4,
                rect.w * cell - 8,
                rect.h * cell - 8,
            )
            # Semi-transparent fill
            s = pygame.Surface((px.width, px.height), pygame.SRCALPHA)
            alpha_col = (*col, 180)
            pygame.draw.rect(s, alpha_col, (0, 0, px.width, px.height), border_radius=8)
            surface.blit(s, (px.x, px.y))
            # Border
            pygame.draw.rect(surface, col, px, 2, border_radius=8)

        # Drag preview
        if self.start_cell and self.hover_cell and not show_solution:
            r1, c1 = self.start_cell
            r2, c2 = self.hover_cell
            rmin, rmax = min(r1, r2), max(r1, r2)
            cmin, cmax = min(c1, c2), max(c1, c2)
            preview = pygame.Rect(
                self.ox + cmin * cell + 4,
                self.oy + rmin * cell + 4,
                (cmax - cmin + 1) * cell - 8,
                (rmax - rmin + 1) * cell - 8,
            )
            s = pygame.Surface((preview.width, preview.height), pygame.SRCALPHA)
            s.fill((78, 150, 255, 60))
            surface.blit(s, (preview.x, preview.y))
            pygame.draw.rect(surface, ACCENT, preview, 2, border_radius=8)

        # Grid lines (Subtle)
        for r in range(rows + 1):
            width = 2 if r == 0 or r == rows else 1
            col_line = GRID_BOLD if width == 2 else GRID_LINE
            pygame.draw.line(surface, col_line,
                             (self.ox, self.oy + r * cell),
                             (self.ox + cols * cell, self.oy + r * cell), width)
        for c in range(cols + 1):
            width = 2 if c == 0 or c == cols else 1
            col_line = GRID_BOLD if width == 2 else GRID_LINE
            pygame.draw.line(surface, col_line,
                             (self.ox + c * cell, self.oy),
                             (self.ox + c * cell, self.oy + rows * cell), width)

        # Clue Numbers with Glow
        for clue in self.board.clues:
            r, c, n = clue.row, clue.col, clue.n
            cr = self.cell_rect(r, c)
            # Clue Background Card
            inset = pygame.Rect(cr.x + 8, cr.y + 8, cr.w - 16, cr.h - 16)
            pygame.draw.rect(surface, CLUE_BG, inset, border_radius=6)
            pygame.draw.rect(surface, CLUE_BORDER, inset, 1, border_radius=6)
            
            txt = font_num.render(str(n), True, NUMBER_COL)
            tx = cr.x + (cell - txt.get_width()) // 2
            ty = cr.y + (cell - txt.get_height()) // 2
            surface.blit(txt, (tx, ty))

    # ---- interacción del jugador ----
    def handle_mousedown(self, pos):
        cell = self.px_to_cell(*pos)
        if cell:
            self.start_cell = cell

    def handle_mousemove(self, pos):
        self.hover_cell = self.px_to_cell(*pos)

    def handle_mouseup(self, pos) -> str:
        """
        Confirma el rectángulo en construcción.
        Devuelve un mensaje de estado.
        """
        if not self.start_cell:
            return ""
        end_cell = self.px_to_cell(*pos)
        if not end_cell:
            self.start_cell = None
            return ""

        r1, c1 = self.start_cell
        r2, c2 = end_cell
        self.start_cell = None

        rmin, rmax = min(r1, r2), max(r1, r2)
        cmin, cmax = min(c1, c2), max(c1, c2)
        h = rmax - rmin + 1
        w = cmax - cmin + 1
        new_rect = Rect(rmin, cmin, h, w)

        # Validar que el rectángulo contiene exactamente una pista
        clues_inside = [
            cl for cl in self.board.clues
            if new_rect.contains(cl.row, cl.col)
        ]
        if len(clues_inside) != 1:
            return "⚠ El rectángulo debe contener exactamente una pista."

        clue = clues_inside[0]
        if new_rect.area != clue.n:
            return f"⚠ Área incorrecta: dibujaste {new_rect.area}, la pista pide {clue.n}."

        # Verificar solapamiento
        for existing in self.player_rects:
            if existing.overlaps(new_rect):
                return "⚠ Este rectángulo se solapa con otro ya definido."

        # Eliminar si ya había un rectángulo para esa pista
        self.player_rects = [
            rx for rx in self.player_rects
            if not any(rx.contains(cl.row, cl.col) for cl in clues_inside)
        ]

        self.player_rects.append(new_rect)
        return f"✓ Rectángulo {h}×{w} = {new_rect.area} añadido."

    def clear(self):
        self.player_rects.clear()
        self.start_cell = None
        self._color_map.clear()
        self._color_idx = 0

    def player_solved(self) -> bool:
        self.board.solution = self.player_rects[:]
        return self.board.is_solved()


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------
PANEL_W = 210   # ancho del panel lateral
MARGIN  = 24

class ShikakuApp:
    WIN_W = 860
    WIN_H = 720

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIN_W, self.WIN_H), pygame.RESIZABLE)
        pygame.display.set_caption("Shikaku  –  Análisis de Algoritmos 2026-10")

        self.font_title = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.font_num   = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_btn   = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.font_sm    = pygame.font.SysFont("Segoe UI", 13)
        self.font_msg   = pygame.font.SysFont("Segoe UI", 14)

        self.selector = PuzzleSelector(MARGIN, 110, PANEL_W - MARGIN, self.font_sm)
        self._load_board()

        self.human_mode = True    # True = humano, False = sintético
        self.solving = False      # hilo de resolución activo
        self.solved  = False
        self.msg     = ""
        self.msg_color = MSG_INFO
        self.solve_time: float = 0.0
        self.nodes_explored: int = 0

        # Botones
        bx = MARGIN
        self._build_buttons()

        self.clock = pygame.time.Clock()

    def _build_buttons(self):
        bx = MARGIN
        self.btn_human  = Button(bx, 450, 80, 34, "Humano",   self.font_btn)
        self.btn_auto   = Button(bx + 92, 450, 90, 34, "Sintético", self.font_btn)
        self.btn_solve  = Button(bx, 510, PANEL_W - MARGIN, 36, "SOLUCIONAR", self.font_btn, primary=True)
        self.btn_clear  = Button(bx, 556, PANEL_W - MARGIN - 4, 36, "LIMPIAR",  self.font_btn, color=BTN_DANGER)
        self.btn_check  = Button(bx, 602, PANEL_W - MARGIN - 4, 36, "VERIFICAR", self.font_btn, color=BTN_SUCCESS)
        self.buttons = [self.btn_human, self.btn_auto, self.btn_solve, self.btn_clear, self.btn_check]

    def _load_board(self):
        board = self.selector.current_board
        # Calcular posición del tablero (centrado en el área derecha)
        avail_w = self.WIN_W - PANEL_W - MARGIN * 2
        avail_h = self.WIN_H - MARGIN * 2
        cell = min(avail_w // board.cols, avail_h // board.rows, BoardView.CELL)
        bw = board.cols * cell
        bh = board.rows * cell
        ox = PANEL_W + MARGIN + (avail_w - bw) // 2
        oy = MARGIN + (avail_h - bh) // 2
        self.view = BoardView(board, ox, oy)
        self.view.cell = cell
        self.solved = False
        self.msg = "Selecciona un puzzle y elige tu modo."
        self.msg_color = MSG_INFO
        self.solve_time = 0.0
        self.nodes_explored = 0

    def run(self):
        while True:
            dt = self.clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.buttons:
                btn.update(mouse_pos)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self._handle_event(event)

            self._draw()
            pygame.display.flip()

    def _handle_event(self, event):
        # Selector de puzzle
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.selector.click(event.pos):
                self._load_board()
                return

        # Botones
        if self.btn_human.is_clicked(event):
            self.human_mode = True
            self.msg = "Modo humano: arrastra para dibujar rectángulos."
            self.msg_color = MSG_INFO
        elif self.btn_auto.is_clicked(event):
            self.human_mode = False
            self.msg = "Modo sintético: pulsa ▶ Resolver."
            self.msg_color = MSG_INFO
        elif self.btn_clear.is_clicked(event):
            self.view.clear()
            self.view.board.solution = []
            self.solved = False
            self.msg = "Tablero limpiado."
            self.msg_color = MSG_INFO
        elif self.btn_solve.is_clicked(event) and not self.solving:
            if self.human_mode:
                # Verificar solución del jugador
                if self.view.player_solved():
                    self.solved = True
                    self.msg = "🎉 ¡Correcto! Resolviste el Shikaku."
                    self.msg_color = MSG_OK
                else:
                    self.msg = "Aún no está completo o hay errores."
                    self.msg_color = MSG_ERR
            else:
                self._run_solver()
        elif self.btn_check.is_clicked(event):
            if self.human_mode:
                if self.view.player_solved():
                    self.solved = True
                    self.msg = "🎉 ¡Correcto!"
                    self.msg_color = MSG_OK
                else:
                    self.msg = "Hay errores o faltan rectángulos."
                    self.msg_color = MSG_ERR

        # Interacción con el tablero (modo humano)
        if self.human_mode and not self.solved:
            board_r = pygame.Rect(self.view.ox, self.view.oy,
                                  self.view.board.cols * self.view.cell,
                                  self.view.board.rows * self.view.cell)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if board_r.collidepoint(event.pos):
                    self.view.handle_mousedown(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.view.handle_mousemove(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                msg = self.view.handle_mouseup(event.pos)
                if msg:
                    self.msg = msg
                    self.msg_color = MSG_OK if msg.startswith("✓") else MSG_ERR

    def _run_solver(self):
        """Lanza el solucionador en un hilo separado para no bloquear la UI."""
        self.solving = True
        self.msg = "⏳ Resolviendo…"
        self.msg_color = MSG_INFO
        self.view.clear()
        self.view.board.solution = []

        def worker():
            solver = ShikakuSolver(self.view.board)
            t0 = time.perf_counter()
            success = solver.solve()
            elapsed = time.perf_counter() - t0
            self.solve_time = elapsed
            self.nodes_explored = solver.nodes_explored
            if success:
                self.solved = True
                self.msg = f"✓ Resuelto en {elapsed*1000:.1f} ms  ({solver.nodes_explored} nodos)"
                self.msg_color = MSG_OK
            else:
                self.msg = "✗ No se encontró solución."
                self.msg_color = MSG_ERR
            self.solving = False

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _draw(self):
        self.screen.fill(BG)

        # ---- Panel lateral ----
        panel = pygame.Rect(0, 0, PANEL_W, self.WIN_H)
        pygame.draw.rect(self.screen, PANEL_BG, panel)
        pygame.draw.line(self.screen, GRID_LINE, (PANEL_W, 0), (PANEL_W, self.WIN_H), 1)

        # Título
        t = self.font_title.render("Shikaku", True, (40, 60, 120))
        self.screen.blit(t, (MARGIN, 20))
        t2 = self.font_sm.render("Análisis de Algoritmos", True, (100, 110, 140))
        self.screen.blit(t2, (MARGIN, 48))
        t3 = self.font_sm.render("Javeriana 2026-10", True, (100, 110, 140))
        self.screen.blit(t3, (MARGIN, 65))

        # Puzzles disponibles
        t4 = self.font_sm.render("SELECCIONAR NIVEL", True, ACCENT)
        self.screen.blit(t4, (MARGIN, 92))
        self.selector.draw(self.screen)

        # Etiqueta modo
        t5 = self.font_sm.render("MODO DE JUEGO", True, ACCENT)
        self.screen.blit(t5, (MARGIN, 430))

        # Botones de modo (resalta el activo)
        self.btn_human.color = BTN_PRIMARY if self.human_mode else BTN_NORMAL
        self.btn_auto.color  = BTN_PRIMARY if not self.human_mode else BTN_NORMAL

        for btn in self.buttons:
            btn.draw(self.screen)

        # Mensaje de estado
        if self.msg:
            lines = self.msg.split("\n")
            y_msg = 655
            for line in lines:
                ms = self.font_msg.render(line, True, self.msg_color)
                self.screen.blit(ms, (MARGIN, y_msg))
                y_msg += 18

        # Leyenda de controles (modo humano)
        if self.human_mode:
            hints = [
                "Arrastra para crear rectangulos",
            ]
            y_h = self.WIN_H - 30
            for h in hints:
                hs = self.font_sm.render(h, True, TEXT_DIM)
                self.screen.blit(hs, (MARGIN, y_h))

        # ---- Tablero ----
        show_sol = (not self.human_mode) and self.solved
        self.view.draw(self.screen, self.font_num, self.font_sm, show_solution=show_sol)
        if self.human_mode:
            self.view.draw(self.screen, self.font_num, self.font_sm, show_solution=False)
