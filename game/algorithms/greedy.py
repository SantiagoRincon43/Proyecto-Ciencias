# ============================================================
# Team 7 - Rescue Mission | Computer Sciences I 2026-I
# File: game/algorithms/greedy.py
# Description: Greedy rescue strategy.
#   At every step, pick the highest-urgency reachable survivor
#   and return the BFS path to get there.
# ============================================================

from collections import deque


def bfs_path(grid, start, goal):
    """
    BFS on the grid from 'start' to 'goal'.
    Returns the list of (row, col) steps from start to goal,
    or an empty list if goal is not reachable.

    grid[r][c] == 1  means collapsed (wall)
    Movement: 4 cardinal directions only.
    """
    rows = len(grid)
    cols = len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    # parent dict maps cell -> cell it was reached from
    parent = {}

    queue = deque()
    queue.append(start)
    visited[start[0]][start[1]] = True
    parent[start] = None

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up down left right

    while queue:
        cur = queue.popleft()

        if cur == goal:
            # Reconstruct path
            path = []
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            path.reverse()
            return path  # includes start; caller can skip path[0]

        for dr, dc in directions:
            nr, nc = cur[0] + dr, cur[1] + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if not visited[nr][nc] and grid[nr][nc] != 1:
                    visited[nr][nc] = True
                    parent[(nr, nc)] = cur
                    queue.append((nr, nc))

    return []  # no path found


def greedy_next_step(grid, agent_pos, survivors):
    """
    Choose the best survivor (highest urgency that is reachable)
    and return the NEXT single step the agent should take.

    Parameters:
        grid       : 2-D list (0=free, 1=collapsed, 2=survivor)
        agent_pos  : (row, col) tuple
        survivors  : list of dicts with keys 'id','row','col','urgency','rescued'

    Returns:
        (next_pos, target_survivor_id, full_path)
        next_pos             : (row, col) — the immediate next cell to move to
        target_survivor_id   : id of the chosen survivor
        full_path            : complete BFS path to that survivor

        Returns (None, None, []) if no survivor is reachable.
    """
    # Filter out already-rescued survivors
    active = [s for s in survivors if not s['rescued']]
    if not active:
        return None, None, []

    # Sort by urgency descending; ties broken by BFS distance (shorter = better)
    # We try from highest to lowest urgency until we find one that is reachable
    active.sort(key=lambda s: -s['urgency'])

    best_path = []
    best_id   = None

    for survivor in active:
        goal = (survivor['row'], survivor['col'])
        path = bfs_path(grid, agent_pos, goal)

        if path:
            # path[0] is agent_pos itself; we need at least 2 cells
            if len(path) > 1:
                best_path = path
                best_id   = survivor['id']
                break           # greedy: take the first (highest urgency) reachable one
            elif len(path) == 1:
                # agent is already on the survivor
                best_path = path
                best_id   = survivor['id']
                break

    if not best_path:
        return None, None, []

    # Next step is path[1] if we are not already at goal, else path[0]
    next_pos = best_path[1] if len(best_path) > 1 else best_path[0]
    return next_pos, best_id, best_path
