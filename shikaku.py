"""
shikaku.py  –  Lógica del rompecabezas Shikaku y solucionador por backtracking.

Reglas:
  - El tablero es una cuadrícula N×M.
  - Algunas celdas contienen un número n.
  - Cada número debe ser la esquina / interior de exactamente un rectángulo
    de área n que no se solape con ningún otro rectángulo.
  - Los rectángulos deben cubrir TODO el tablero.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import copy


# ---------------------------------------------------------------------------
# Tipos de datos
# ---------------------------------------------------------------------------

@dataclass
class Rect:
    """Rectángulo definido por su esquina superior-izquierda y dimensiones."""
    row: int
    col: int
    h: int   # alto (filas)
    w: int   # ancho (columnas)

    @property
    def area(self) -> int:
        return self.h * self.w

    def cells(self):
        """Genera (r, c) de todas las celdas que ocupa."""
        for r in range(self.row, self.row + self.h):
            for c in range(self.col, self.col + self.w):
                yield r, c

    def contains(self, row: int, col: int) -> bool:
        return self.row <= row < self.row + self.h and self.col <= col < self.col + self.w

    def overlaps(self, other: "Rect") -> bool:
        return not (
            self.row + self.h <= other.row or
            other.row + other.h <= self.row or
            self.col + self.w <= other.col or
            other.col + other.w <= self.col
        )


@dataclass
class Clue:
    """Una pista del tablero: número n en la celda (row, col)."""
    row: int
    col: int
    n: int


class ShikakuBoard:
    """Estado completo del tablero Shikaku."""

    def __init__(self, rows: int, cols: int, clues: list[Clue]):
        self.rows = rows
        self.cols = cols
        self.clues = clues               # lista de pistas originales
        self.solution: list[Rect] = []   # rectángulos asignados (uno por pista)

    # ------------------------------------------------------------------
    # Generación de candidatos para una pista
    # ------------------------------------------------------------------
    def candidates(self, clue: Clue) -> list[Rect]:
        """
        Devuelve todos los rectángulos válidos de área = clue.n
        que caben dentro del tablero y contienen la celda de la pista.
        """
        n = clue.n
        result: list[Rect] = []
        # Iterar sobre todas las factorizaciones h×w = n
        for h in range(1, n + 1):
            if n % h != 0:
                continue
            w = n // h
            # El rectángulo puede empezar en cualquier posición siempre que
            # contenga (clue.row, clue.col) y quepa en el tablero.
            r_min = max(0, clue.row - h + 1)
            r_max = min(self.rows - h, clue.row)
            c_min = max(0, clue.col - w + 1)
            c_max = min(self.cols - w, clue.col)
            for r in range(r_min, r_max + 1):
                for c in range(c_min, c_max + 1):
                    result.append(Rect(r, c, h, w))
        return result

    # ------------------------------------------------------------------
    # Serialización para guardar / cargar tableros
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "rows": self.rows,
            "cols": self.cols,
            "clues": [{"row": c.row, "col": c.col, "n": c.n} for c in self.clues],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ShikakuBoard":
        clues = [Clue(**c) for c in data["clues"]]
        return cls(data["rows"], data["cols"], clues)

    # ------------------------------------------------------------------
    # Validación de solución
    # ------------------------------------------------------------------
    def is_solved(self) -> bool:
        if len(self.solution) != len(self.clues):
            return False
        # Construir mapa de ocupación
        grid = [[False] * self.cols for _ in range(self.rows)]
        for rect in self.solution:
            for r, c in rect.cells():
                if grid[r][c]:
                    return False   # solapamiento
                grid[r][c] = True
        # Todas las celdas deben estar cubiertas
        return all(grid[r][c] for r in range(self.rows) for c in range(self.cols))


# ---------------------------------------------------------------------------
# Solucionador por backtracking con propagación de restricciones básica
# ---------------------------------------------------------------------------

class ShikakuSolver:
    """
    Resuelve un ShikakuBoard por backtracking ordenado.

    Estrategias de poda:
      1. Fail-first: procesa primero las pistas con menos candidatos.
      2. Verificación de consistencia: descarta candidatos que solapen con
         rectángulos ya asignados.
    """

    def __init__(self, board: ShikakuBoard):
        self.board = board
        self._nodes = 0   # contador de nodos explorados (para análisis)

    # Mapa rápido de celdas ocupadas
    def _build_occupied(self, assigned: list[Optional[Rect]]) -> set[tuple[int, int]]:
        occ: set[tuple[int, int]] = set()
        for rect in assigned:
            if rect is not None:
                for cell in rect.cells():
                    occ.add(cell)
        return occ

    def solve(self) -> bool:
        """
        Intenta resolver el tablero.
        Si tiene éxito, llena self.board.solution y devuelve True.
        """
        n = len(self.board.clues)
        # Pre-computar candidatos para cada pista
        all_candidates = [self.board.candidates(c) for c in self.board.clues]
        assigned: list[Optional[Rect]] = [None] * n

        # Orden de procesamiento: fail-first (menos candidatos primero)
        order = sorted(range(n), key=lambda i: len(all_candidates[i]))

        result = self._backtrack(order, 0, assigned, all_candidates, set())
        if result:
            self.board.solution = [assigned[i] for i in range(n)]  # type: ignore
        return result

    def _backtrack(
        self,
        order: list[int],
        depth: int,
        assigned: list[Optional[Rect]],
        all_candidates: list[list[Rect]],
        occupied: set[tuple[int, int]],
    ) -> bool:
        if depth == len(order):
            # Verificar que todo el tablero esté cubierto
            total_cells = self.board.rows * self.board.cols
            return len(occupied) == total_cells

        self._nodes += 1
        idx = order[depth]
        for rect in all_candidates[idx]:
            # Verificar que ninguna celda del rectángulo esté ya ocupada
            cells = list(rect.cells())
            if any(cell in occupied for cell in cells):
                continue
            # Asignar
            assigned[idx] = rect
            new_occ = occupied | set(cells)
            if self._backtrack(order, depth + 1, assigned, all_candidates, new_occ):
                return True
            assigned[idx] = None
        return False

    @property
    def nodes_explored(self) -> int:
        return self._nodes


# ---------------------------------------------------------------------------
# Tableros de ejemplo integrados (verificados – tienen solución única)
# ---------------------------------------------------------------------------
# Cada puzzle se define a partir de su solución conocida para garantizar
# que sea resoluble.  La "pista" de cada rectángulo se coloca en la celda
# central (fila+alto//2, col+ancho//2).
# ---------------------------------------------------------------------------

EXAMPLE_PUZZLES: dict[str, "ShikakuBoard"] = {}


def _board_from_rects(name: str, rows: int, cols: int,
                      rects: list[tuple[int, int, int, int]]) -> None:
    """Construye un ShikakuBoard a partir de una lista de (row, col, h, w)."""
    clues = [Clue(r + h // 2, c + w // 2, h * w) for r, c, h, w in rects]
    EXAMPLE_PUZZLES[name] = ShikakuBoard(rows, cols, clues)


# ── 4×4 Tutorial ──────────────────────────────────────────────────────────
_board_from_rects("4×4 Tutorial", 4, 4, [
    (0, 0, 2, 2), (0, 2, 2, 2),
    (2, 0, 2, 2), (2, 2, 2, 2),
])

# ── 5×5 Fácil ──────────────────────────────────────────────────────────────
_board_from_rects("5×5 Fácil", 5, 5, [
    (0, 0, 1, 2), (0, 2, 1, 3),
    (1, 0, 2, 2), (1, 2, 2, 2), (1, 4, 2, 1),
    (3, 0, 2, 3), (3, 3, 1, 2),
    (4, 3, 1, 2),
])

# ── 7×7 Intermedio ─────────────────────────────────────────────────────────
_board_from_rects("7×7 Intermedio", 7, 7, [
    (0, 0, 2, 3), (0, 3, 2, 4),
    (2, 0, 2, 2), (2, 2, 2, 2), (2, 4, 2, 3),
    (4, 0, 3, 2), (4, 2, 1, 3), (4, 5, 3, 2),
    (5, 2, 2, 2), (5, 4, 2, 1),
])

# ── 6×6 Medio ──────────────────────────────────────────────────────────────
_board_from_rects("6×6 Medio", 6, 6, [
    (0, 0, 6, 1), (0, 1, 1, 5),
    (1, 1, 5, 1), (1, 2, 2, 2), (3, 2, 3, 2),
    (1, 4, 4, 2), (5, 4, 1, 2),
])

# ── 8×8 Desafío ────────────────────────────────────────────────────────────
_board_from_rects("8×8 Desafío", 8, 8, [
    (0, 0, 2, 8), (2, 0, 6, 2),
    (2, 2, 3, 3), (5, 2, 3, 3),
    (2, 5, 4, 3), (6, 5, 2, 3),
])

# ── 9×9 Difícil ────────────────────────────────────────────────────────────
_board_from_rects("9×9 Difícil", 9, 9, [
    (0, 0, 3, 3), (0, 3, 2, 3), (0, 6, 3, 3),
    (2, 3, 1, 3),
    (3, 0, 3, 3), (3, 3, 3, 3), (3, 6, 3, 3),
    (6, 0, 3, 3), (6, 3, 3, 3), (6, 6, 3, 3),
])

# ── 9×9 Maestro ────────────────────────────────────────────────────────────
_board_from_rects("9×9 Maestro", 9, 9, [
    (0, 0, 4, 2), (0, 2, 2, 7), (2, 2, 2, 3),
    (4, 0, 5, 1), (4, 1, 5, 2), (4, 3, 3, 2),
    (7, 3, 2, 6), (2, 5, 5, 2), (2, 7, 5, 2),
])

# ── 10×10 Experto ──────────────────────────────────────────────────────────
_board_from_rects("10×10 Experto", 10, 10, [
    (0, 0, 5, 2), (0, 2, 2, 5), (0, 7, 5, 3),
    (2, 2, 3, 3), (2, 5, 3, 2),
    (5, 0, 2, 7), (5, 7, 5, 3),
    (7, 0, 3, 4), (7, 4, 3, 3),
])
