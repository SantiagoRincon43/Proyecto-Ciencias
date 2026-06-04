# Rescue Mission — Team 7
**Computer Sciences I · Semester 2026-I**
Universidad Distrital Francisco José de Caldas

> Johan Santiago Rincón Arévalo · Juan David Díaz Páez

---

## How to run

### Requirements
- Python 3.9+
- Pygame (`pip install pygame`)
- GCC (MinGW on Windows, or system GCC on Linux/macOS)

### 1. Compile the C engine (optional — game works without it)

**Windows (MinGW):**
```bash
cd engine
gcc -o engine.exe main.c linked_list.c avl_tree.c
```

**Linux / macOS:**
```bash
cd engine
gcc -o engine main.c linked_list.c avl_tree.c
```

No external libraries required — only the C standard library (`stdlib.h`, `stdio.h`, `string.h`).

### 2. Run the game
```bash
# from the project root
python game/ui/main.py
```

---

## Controls
| Key | Action |
|-----|--------|
| `SPACE` | Execute one step |
| `A` | Toggle auto mode |
| `G` | Switch to Greedy algorithm |
| `B` | Switch to Backtracking algorithm |
| `R` | Reset / new random map |

---

## Project structure
```
rescue_mission/
├── engine/                  ← C core (structs only, no classes)
│   ├── main.c               ← entry point, JSON I/O, action dispatcher
│   ├── linked_list.c / .h   ← RouteNode + LinkedList structs
│   └── avl_tree.c   / .h    ← AVLNode + AVLTree + Survivor structs
├── game/
│   ├── algorithms/
│   │   ├── greedy.py        ← greedy BFS strategy
│   │   └── backtracking.py  ← exhaustive backtracking solver
│   └── ui/
│       ├── main.py          ← Pygame grid + HUD (entry point)
│       └── bridge.py        ← JSON file I/O between Python and C
└── data/
    ├── input.json           ← Python → C engine
    └── state.json           ← C engine → Python
```

---

## C engine — data structures

### `Survivor` (avl_tree.h)
Plain struct holding `id`, `row`, `col`, `urgency`, `rescued`.

### `AVLNode` / `AVLTree` (avl_tree.h / avl_tree.c)
Self-balancing AVL tree keyed by `urgency`.
All logic implemented with plain C functions that take a pointer to the struct.

| Operation | Complexity |
|-----------|-----------|
| `avl_insert` | O(log k) |
| `avl_remove` | O(log k) |
| `avl_get_max` | O(log k) |

### `RouteNode` / `LinkedList` (linked_list.h / linked_list.c)
Singly linked list of `(row, col)` cells representing the rescue route.

| Operation | Complexity |
|-----------|-----------|
| `list_append` | O(1) |
| `list_remove_last` | O(n) |
| `list_clear` | O(n) |

---

## Grid legend
| Symbol | Meaning |
|--------|---------|
| **A** (cyan) | Rescue agent |
| **number** (yellow→red) | Survivor with urgency level |
| **X** (red) | Collapsed / impassable cell |
| dark blue trail | Cells already visited |
| purple highlight | Planned path (next steps) |
