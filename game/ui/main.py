# ============================================================
# Team 7 - Rescue Mission | Computer Sciences I 2026-I
# File: game/ui/main.py
# Description: Pygame grid UI with HUD.
#   Controls: SPACE = next step | A = auto mode | R = reset
#             G = greedy mode   | B = backtracking mode
# Run: python game/ui/main.py   (from project root)
# ============================================================

import sys
import os
import time
import pygame
import random

# Add project root to path so imports work
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from game.algorithms.greedy      import greedy_next_step
from game.algorithms.backtracking import backtracking_solve, backtracking_full_path
from game.ui.bridge               import write_input, read_state, call_engine, init_state

# ─── CONSTANTS ───────────────────────────────────────────────
GRID_ROWS   = 10
GRID_COLS   = 10
CELL_SIZE   = 58          # pixels per cell
HUD_WIDTH   = 220
MARGIN      = 8

WIN_W = GRID_COLS * CELL_SIZE + HUD_WIDTH + MARGIN * 3
WIN_H = GRID_ROWS * CELL_SIZE + MARGIN * 2

FPS          = 30
AUTO_DELAY   = 0.45       # seconds between auto steps

# ─── COLOURS ─────────────────────────────────────────────────
BG          = (15,  23,  42)
CELL_FREE   = (30,  41,  59)
CELL_COLL   = (185, 28,  28)   # collapsed / impassable
CELL_SURV   = (234, 179,  8)   # survivor (base colour)
CELL_AGENT  = (6,  182, 212)   # agent
CELL_TRAIL  = (51,  65,  85)   # cells the agent walked through
CELL_PATH   = (99, 102, 241)   # planned path highlight
GRID_LINE   = (51,  65,  85)
HUD_BG      = (17,  24,  39)
TEXT_WHITE  = (248, 250, 252)
TEXT_MUTED  = (100, 116, 139)
TEXT_TEAL   = (34,  211, 238)
TEXT_GOLD   = (250, 204,  21)
TEXT_RED    = (239,  68,  68)
BORDER_TEAL = (8,  145, 178)

# ─── GAME STATE ──────────────────────────────────────────────
def make_grid():
    """Create a random 10×10 grid with collapsed cells and survivors."""
    grid = [[0] * GRID_COLS for _ in range(GRID_ROWS)]

    # Place collapsed cells (~18% of grid)
    collapsed_cells = set()
    while len(collapsed_cells) < 18:
        r = random.randint(0, GRID_ROWS - 1)
        c = random.randint(0, GRID_COLS - 1)
        if (r, c) != (0, 0):          # never block the start
            collapsed_cells.add((r, c))
            grid[r][c] = 1

    # Place survivors (6 survivors)
    survivors = []
    sid = 1
    placed = 0
    while placed < 6:
        r = random.randint(0, GRID_ROWS - 1)
        c = random.randint(0, GRID_COLS - 1)
        if grid[r][c] == 0 and (r, c) != (0, 0):
            urgency = random.randint(1, 10)
            grid[r][c] = 2
            survivors.append({
                "id": sid, "row": r, "col": c,
                "urgency": urgency, "rescued": False
            })
            sid += 1
            placed += 1

    return grid, survivors


class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid, self.survivors = make_grid()
        self.agent_pos   = (0, 0)
        self.rescued     = 0
        self.route       = [(0, 0)]     # cells visited (linked list mirror)
        self.algorithm   = "greedy"
        self.auto_mode   = False
        self.last_auto   = 0.0
        self.message     = "Press SPACE to step | A: auto | R: reset"
        self.game_over   = False

        # Backtracking: pre-compute full path at reset
        self.bt_path     = []
        self.bt_step_idx = 0
        self.bt_order    = []

        # Init state.json for bridge
        init_state(self.grid, self.survivors, self.agent_pos)

    def precompute_backtracking(self):
        self.bt_order = backtracking_solve(
            self.grid, self.agent_pos, self.survivors
        )
        self.bt_path = backtracking_full_path(
            self.grid, self.agent_pos, self.survivors, self.bt_order
        )
        self.bt_step_idx = 0
        self.message = f"Backtracking: will rescue {len(self.bt_order)} survivors"


# ─── DRAWING ─────────────────────────────────────────────────
def urgency_color(urgency):
    """Map urgency 1-10 to a yellow→red gradient."""
    t = (urgency - 1) / 9.0   # 0.0 … 1.0
    r = int(250 - (250 - 234) * (1 - t))
    g = int(204 - 204 * t)
    b = int(21  - 21  * t)
    return (r, g, b)


def draw_grid(surface, gs, planned_path):
    ox = MARGIN
    oy = MARGIN

    route_set = set(gs.route)

    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            x = ox + c * CELL_SIZE
            y = oy + r * CELL_SIZE
            rect = pygame.Rect(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2)

            cell_val = gs.grid[r][c]
            pos = (r, c)

            if pos == gs.agent_pos:
                color = CELL_AGENT
            elif cell_val == 1:
                color = CELL_COLL
            elif cell_val == 2:
                # Find survivor urgency
                surv = next((s for s in gs.survivors
                             if s['row'] == r and s['col'] == c
                             and not s['rescued']), None)
                color = urgency_color(surv['urgency']) if surv else CELL_FREE
            elif pos in route_set:
                color = CELL_TRAIL
            elif pos in planned_path:
                color = CELL_PATH
            else:
                color = CELL_FREE

            pygame.draw.rect(surface, color, rect, border_radius=4)

            # Urgency label on survivor cells
            if cell_val == 2 and pos != gs.agent_pos:
                surv = next((s for s in gs.survivors
                             if s['row'] == r and s['col'] == c
                             and not s['rescued']), None)
                if surv:
                    font_sm = pygame.font.SysFont("Arial", 13, bold=True)
                    lbl = font_sm.render(str(surv['urgency']), True, (15, 23, 42))
                    surface.blit(lbl, (x + CELL_SIZE - 18, y + 4))

            # Collapsed X
            if cell_val == 1:
                font_sm = pygame.font.SysFont("Arial", 16, bold=True)
                lbl = font_sm.render("X", True, (255, 255, 255))
                lrect = lbl.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                surface.blit(lbl, lrect)

            # Agent A
            if pos == gs.agent_pos:
                font_sm = pygame.font.SysFont("Arial", 17, bold=True)
                lbl = font_sm.render("A", True, (15, 23, 42))
                lrect = lbl.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                surface.blit(lbl, lrect)

    # Grid lines
    for r in range(GRID_ROWS + 1):
        y = oy + r * CELL_SIZE
        pygame.draw.line(surface, GRID_LINE, (ox, y), (ox + GRID_COLS * CELL_SIZE, y))
    for c in range(GRID_COLS + 1):
        x = ox + c * CELL_SIZE
        pygame.draw.line(surface, GRID_LINE, (x, oy), (x, oy + GRID_ROWS * CELL_SIZE))


def draw_hud(surface, gs, font_big, font_med, font_sm):
    hx = GRID_COLS * CELL_SIZE + MARGIN * 2
    hy = MARGIN
    hw = HUD_WIDTH
    hh = WIN_H - MARGIN * 2
    pygame.draw.rect(surface, HUD_BG, (hx, hy, hw, hh), border_radius=8)
    pygame.draw.rect(surface, BORDER_TEAL, (hx, hy, hw, hh), 1, border_radius=8)

    y = hy + 14

    def text(txt, color, fnt, indent=14):
        nonlocal y
        surf = fnt.render(txt, True, color)
        surface.blit(surf, (hx + indent, y))
        y += surf.get_height() + 4

    def sep():
        nonlocal y
        pygame.draw.line(surface, (51, 65, 85),
                         (hx + 10, y), (hx + hw - 10, y))
        y += 8

    text("RESCUE MISSION", TEXT_TEAL, font_big, indent=10)
    sep()

    # Algorithm
    text("Algorithm", TEXT_MUTED, font_sm)
    alg_color = TEXT_TEAL if gs.algorithm == "greedy" else TEXT_GOLD
    text(gs.algorithm.upper(), alg_color, font_med)
    sep()

    # Stats
    text("Rescued", TEXT_MUTED, font_sm)
    text(f"{gs.rescued} / {len(gs.survivors)}", TEXT_WHITE, font_med)
    y += 4

    text("Route length", TEXT_MUTED, font_sm)
    text(str(len(gs.route)), TEXT_WHITE, font_med)
    sep()

    # Survivor list
    text("Survivors", TEXT_MUTED, font_sm)
    active = sorted(
        [s for s in gs.survivors if not s['rescued']],
        key=lambda s: -s['urgency']
    )
    for s in active[:6]:
        clr = urgency_color(s['urgency'])
        text(f"[{s['urgency']}] ({s['row']},{s['col']})", clr, font_sm, indent=10)
    sep()

    # Controls
    text("Controls", TEXT_MUTED, font_sm)
    for line in ["SPACE  next step",
                 "A      auto mode",
                 "G      greedy",
                 "B      backtracking",
                 "R      reset"]:
        text(line, TEXT_MUTED, font_sm, indent=10)
    sep()

    # Status message
    text("Status", TEXT_MUTED, font_sm)
    # Word-wrap message
    words = gs.message.split()
    line_buf = ""
    for w in words:
        if font_sm.size(line_buf + w)[0] > hw - 24:
            text(line_buf.strip(), TEXT_WHITE, font_sm, indent=10)
            line_buf = w + " "
        else:
            line_buf += w + " "
    if line_buf.strip():
        text(line_buf.strip(), TEXT_WHITE, font_sm, indent=10)

    if gs.game_over:
        y += 10
        text("MISSION COMPLETE", TEXT_GOLD, font_med, indent=6)


# ─── STEP LOGIC ──────────────────────────────────────────────
def do_step(gs):
    """Execute one step of the active algorithm."""
    if gs.game_over:
        return

    if gs.algorithm == "greedy":
        next_pos, target_id, path = greedy_next_step(
            gs.grid, gs.agent_pos, gs.survivors
        )
        if next_pos is None:
            gs.game_over = True
            gs.message   = "No more reachable survivors!"
            return

        gs.agent_pos = next_pos
        gs.route.append(next_pos)

        # Check if we reached the survivor
        arrived = next((s for s in gs.survivors
                        if not s['rescued']
                        and (s['row'], s['col']) == next_pos), None)
        if arrived:
            arrived['rescued'] = True
            gs.grid[arrived['row']][arrived['col']] = 0
            gs.rescued += 1
            gs.message = f"Rescued survivor #{arrived['id']} (urgency {arrived['urgency']})"

            # Tell C++ engine to update its state
            write_input("rescue", gs.grid, gs.survivors,
                        gs.agent_pos[0], gs.agent_pos[1],
                        gs.rescued, gs.algorithm)
            call_engine()
        else:
            gs.message = f"Moving to {next_pos}"

    else:  # backtracking
        if not gs.bt_path:
            gs.game_over = True
            gs.message   = "Backtracking path exhausted."
            return

        if gs.bt_step_idx >= len(gs.bt_path):
            gs.game_over = True
            gs.message   = f"Backtracking done. Rescued {gs.rescued} survivors."
            return

        next_pos = gs.bt_path[gs.bt_step_idx]
        gs.bt_step_idx += 1
        gs.agent_pos = next_pos
        gs.route.append(next_pos)

        arrived = next((s for s in gs.survivors
                        if not s['rescued']
                        and (s['row'], s['col']) == next_pos), None)
        if arrived:
            arrived['rescued'] = True
            gs.grid[arrived['row']][arrived['col']] = 0
            gs.rescued += 1
            gs.message = f"Rescued survivor #{arrived['id']} (urgency {arrived['urgency']})"

    # Check win condition
    if all(s['rescued'] for s in gs.survivors):
        gs.game_over = True
        gs.message   = f"All {gs.rescued} survivors rescued!"


# ─── MAIN LOOP ───────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Rescue Mission — Team 7")
    clock  = pygame.time.Clock()

    font_big = pygame.font.SysFont("Arial", 15, bold=True)
    font_med = pygame.font.SysFont("Arial", 14, bold=True)
    font_sm  = pygame.font.SysFont("Arial", 12)

    gs = GameState()

    planned_path = set()  # cells highlighted as the planned BFS path

    while True:
        now = time.time()

        # ── Events ──────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    gs.reset()
                    planned_path = set()

                elif event.key == pygame.K_g:
                    gs.algorithm  = "greedy"
                    gs.message    = "Switched to GREEDY mode"

                elif event.key == pygame.K_b:
                    gs.algorithm = "backtracking"
                    gs.precompute_backtracking()
                    planned_path = set(gs.bt_path)

                elif event.key == pygame.K_a:
                    gs.auto_mode = not gs.auto_mode
                    gs.message   = "Auto ON" if gs.auto_mode else "Auto OFF"

                elif event.key == pygame.K_SPACE:
                    do_step(gs)
                    if gs.algorithm == "greedy":
                        _, _, path = greedy_next_step(
                            gs.grid, gs.agent_pos, gs.survivors)
                        planned_path = set(path)

        # ── Auto mode ───────────────────────────────────────
        if gs.auto_mode and not gs.game_over:
            if now - gs.last_auto >= AUTO_DELAY:
                do_step(gs)
                gs.last_auto = now
                if gs.algorithm == "greedy":
                    _, _, path = greedy_next_step(
                        gs.grid, gs.agent_pos, gs.survivors)
                    planned_path = set(path)

        # ── Draw ────────────────────────────────────────────
        screen.fill(BG)
        draw_grid(screen, gs, planned_path)
        draw_hud(screen, gs, font_big, font_med, font_sm)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
