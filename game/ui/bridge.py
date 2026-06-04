# ============================================================
# Team 7 - Rescue Mission | Computer Sciences I 2026-I
# File: game/ui/bridge.py
# Description: File I/O bridge between Python and C++ engine.
#   Python writes input.json, C++ engine reads it, updates state,
#   and writes state.json, which Python reads back.
# ============================================================

import json
import subprocess
import os

# Paths relative to the game/ui/ folder
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_PATH  = os.path.join(BASE_DIR, "data", "input.json")
STATE_PATH  = os.path.join(BASE_DIR, "data", "state.json")
ENGINE_PATH = os.path.join(BASE_DIR, "engine", "engine.exe")  # Windows


def write_input(action, grid, survivors, agent_row, agent_col,
                rescued=0, algorithm="greedy",
                new_row=None, new_col=None):
    """
    Write input.json so the C++ engine knows what to process.

    action     : "rescue" | "move" | "reset" | "init"
    grid       : 2-D list
    survivors  : list of survivor dicts
    agent_row  : current agent row
    agent_col  : current agent col
    rescued    : how many have been rescued so far
    algorithm  : "greedy" or "backtracking"
    new_row/col: destination cell (only used when action == "move")
    """
    data = {
        "action":    action,
        "algorithm": algorithm,
        "agent_row": agent_row,
        "agent_col": agent_col,
        "rescued":   rescued,
        "grid":      grid,
        "survivors": survivors,
    }
    if new_row is not None:
        data["new_row"] = new_row
        data["new_col"] = new_col

    with open(INPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)


def read_state():
    """
    Read state.json written by the C++ engine.
    Returns a dict with keys: agent_pos, rescued, total,
                               route, survivors, grid
    Returns None if the file does not exist yet.
    """
    if not os.path.exists(STATE_PATH):
        return None
    try:
        with open(STATE_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def call_engine():
    """
    Run the C++ engine binary.
    The engine reads input.json and writes state.json.
    Returns True if the engine exited successfully.
    """
    if not os.path.exists(ENGINE_PATH):
        # Engine not compiled yet — run in pure-Python mode
        # (state.json will not be updated by C++, but the game still works)
        return False
    try:
        result = subprocess.run(
            [ENGINE_PATH],
            cwd=os.path.join(BASE_DIR, "engine"),
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def init_state(grid, survivors, agent_pos):
    """
    Write an initial state.json so the UI can render
    the board before the engine has ever been called.
    """
    state = {
        "agent_pos": list(agent_pos),
        "rescued":   0,
        "total":     len(survivors),
        "route":     [list(agent_pos)],
        "survivors": survivors,
        "grid":      grid,
    }
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
