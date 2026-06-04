# ============================================================
# Team 7 - Rescue Mission | Computer Sciences I 2026-I
# File: game/algorithms/backtracking.py
# Description: Backtracking solver.
#   Tries all orderings of survivors and returns the sequence
#   that rescues the maximum number of them.
#   Prunes branches where the next survivor is unreachable.
# ============================================================

from collections import deque


def bfs_reachable(grid, start, goal):
    """Same BFS as in greedy — returns True/False only (faster)."""
    if start == goal:
        return True
    rows, cols = len(grid), len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    visited[start[0]][start[1]] = True
    queue = deque([start])
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    while queue:
        r, c = queue.popleft()
        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if not visited[nr][nc] and grid[nr][nc] != 1:
                    if (nr, nc) == goal:
                        return True
                    visited[nr][nc] = True
                    queue.append((nr, nc))
    return False


def backtracking_solve(grid, start_pos, survivors):
    """
    Find the ordering of survivors that maximises the rescue count.

    Parameters:
        grid      : 2-D list (0=free, 1=collapsed, 2=survivor)
        start_pos : (row, col) starting position of the agent
        survivors : list of dicts with 'id','row','col','urgency'

    Returns:
        best_order : list of survivor ids in the optimal rescue order
                     (may be shorter than total survivors if some
                      are unreachable from the optimal path)
    """
    active = [s for s in survivors if not s.get('rescued', False)]

    best_order = []   # best sequence found so far

    def backtrack(current_pos, remaining, current_order):
        nonlocal best_order

        # Update best if current sequence is longer
        if len(current_order) > len(best_order):
            best_order = list(current_order)

        # Try every remaining survivor as the next rescue
        for i, survivor in enumerate(remaining):
            goal = (survivor['row'], survivor['col'])

            # PRUNING: skip if no valid path exists from current position
            if not bfs_reachable(grid, current_pos, goal):
                continue

            # Choose this survivor next
            current_order.append(survivor['id'])
            new_remaining = remaining[:i] + remaining[i+1:]
            backtrack(goal, new_remaining, current_order)

            # BACKTRACK: undo the choice
            current_order.pop()

    backtrack(start_pos, active, [])
    return best_order


def backtracking_full_path(grid, start_pos, survivors, order):
    """
    Given an ordered list of survivor ids (from backtracking_solve),
    compute the complete BFS path the agent should follow.

    Returns a list of (row,col) cells from start to the last survivor.
    """
    from collections import deque

    def bfs_path(start, goal):
        if start == goal:
            return [start]
        rows, cols = len(grid), len(grid[0])
        visited = [[False]*cols for _ in range(rows)]
        visited[start[0]][start[1]] = True
        parent = {start: None}
        queue = deque([start])
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        while queue:
            cur = queue.popleft()
            for dr, dc in dirs:
                nr, nc = cur[0]+dr, cur[1]+dc
                if 0<=nr<rows and 0<=nc<cols:
                    if not visited[nr][nc] and grid[nr][nc] != 1:
                        visited[nr][nc] = True
                        parent[(nr,nc)] = cur
                        if (nr,nc) == goal:
                            # reconstruct
                            path, node = [], (nr,nc)
                            while node is not None:
                                path.append(node)
                                node = parent[node]
                            path.reverse()
                            return path
                        queue.append((nr,nc))
        return []

    id_to_survivor = {s['id']: s for s in survivors}
    full_path = [start_pos]
    current   = start_pos

    for sid in order:
        s    = id_to_survivor[sid]
        goal = (s['row'], s['col'])
        seg  = bfs_path(current, goal)
        if seg:
            full_path.extend(seg[1:])  # skip first cell (already in path)
            current = goal

    return full_path
