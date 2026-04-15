"""
main.py  –  Punto de entrada del proyecto Shikaku.

Uso:
    python main.py           → lanza la interfaz gráfica
    python main.py --cli     → solucionador por consola (todos los puzzles)
    python main.py --cli 1   → solucionador por consola (puzzle índice 1)
"""

import sys
import time


def run_gui():
    from gui import ShikakuApp
    app = ShikakuApp()
    app.run()


def run_cli(puzzle_idx: int | None = None):
    from shikaku import EXAMPLE_PUZZLES, ShikakuSolver, ShikakuBoard, Clue

    puzzles = list(EXAMPLE_PUZZLES.items())
    if puzzle_idx is not None:
        if puzzle_idx < 0 or puzzle_idx >= len(puzzles):
            print(f"Índice inválido. Disponibles: 0 a {len(puzzles)-1}")
            sys.exit(1)
        puzzles = [puzzles[puzzle_idx]]

    for name, orig in puzzles:
        # Clonar tablero
        board = ShikakuBoard(
            orig.rows, orig.cols,
            [Clue(c.row, c.col, c.n) for c in orig.clues]
        )
        print(f"\n{'='*50}")
        print(f"Puzzle: {name}  ({board.rows}×{board.cols})")
        print(f"Pistas: {len(board.clues)}")

        solver = ShikakuSolver(board)
        t0 = time.perf_counter()
        ok = solver.solve()
        elapsed = time.perf_counter() - t0

        if ok:
            print(f"OK - Solución encontrada en {elapsed*1000:.2f} ms")
            print(f"  Nodos explorados: {solver.nodes_explored}")
            _print_board(board)
        else:
            print("X - No se encontró solución.")

    print()


def _print_board(board):
    """Imprime el tablero resuelto en la consola."""
    from shikaku import Rect

    grid = [["·"] * board.cols for _ in range(board.rows)]
    symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    for idx, rect in enumerate(board.solution):
        sym = symbols[idx % len(symbols)]
        for r, c in rect.cells():
            grid[r][c] = sym

    # Superponer números de pistas
    for cl in board.clues:
        grid[cl.row][cl.col] = str(cl.n) if cl.n < 10 else "*"

    header = "   " + "".join(f"{c:2}" for c in range(board.cols))
    print(header)
    for r, row in enumerate(grid):
        print(f"{r:2} " + " ".join(row))


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--cli" in args:
        args.remove("--cli")
        idx = int(args[0]) if args else None
        run_cli(idx)
    else:
        run_gui()
