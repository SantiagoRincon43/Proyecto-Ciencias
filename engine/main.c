/* ============================================================
 * Team 7 - Rescue Mission | Computer Sciences I 2026-I
 * File: main.c
 * Description: C engine entry point.
 *   - Reads  data/input.json  (sent by Python)
 *   - Manages LinkedList (route) and AVLTree (survivors)
 *   - Writes data/state.json (read by Python to render)
 *
 * Build (Windows, MinGW / any GCC):
 *   gcc -o engine.exe main.c linked_list.c avl_tree.c
 *
 * Build (Linux / macOS):
 *   gcc -o engine main.c linked_list.c avl_tree.c
 *
 * No external libraries required — only C standard library.
 * ============================================================ */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include "linked_list.h"
#include "avl_tree.h"

/* ================================================================
 * Limits
 * ================================================================ */
#define MAX_GRID_ROWS  64
#define MAX_GRID_COLS  64
#define MAX_SURVIVORS  64
#define MAX_ROUTE      4096
#define MAX_FILE_SIZE  65536

/* ================================================================
 * Tiny JSON helpers (no external library)
 * ================================================================ */

/* Read an entire file into buf (null-terminated).
 * Returns 0 on success, -1 on error. */
static int read_file(const char *path, char *buf, int cap) {
    FILE *f = fopen(path, "r");
    if (!f) { fprintf(stderr, "Cannot open %s\n", path); return -1; }
    int n = (int)fread(buf, 1, cap - 1, f);
    buf[n] = '\0';
    fclose(f);
    return 0;
}

/* Find the value of an integer field "key": number in a JSON string.
 * Returns the integer, or def_val if the key is absent. */
static int json_get_int(const char *json, const char *key, int def_val) {
    /* Build search pattern  "key": */
    char search[128];
    snprintf(search, sizeof(search), "\"%s\":", key);
    const char *pos = strstr(json, search);
    if (!pos) return def_val;
    pos += strlen(search);
    while (*pos == ' ' || *pos == '\n' || *pos == '\r') pos++;
    return atoi(pos);
}

/* Extract a string field "key": "value" into out (max len outlen).
 * Returns 0 on success, -1 if not found. */
static int json_get_str(const char *json, const char *key,
                        char *out, int outlen) {
    char search[128];
    snprintf(search, sizeof(search), "\"%s\":", key);
    const char *pos = strstr(json, search);
    if (!pos) { out[0] = '\0'; return -1; }
    pos += strlen(search);
    while (*pos && *pos != '"') pos++;
    if (!*pos) { out[0] = '\0'; return -1; }
    pos++; /* skip opening quote */
    int i = 0;
    while (*pos && *pos != '"' && i < outlen - 1)
        out[i++] = *pos++;
    out[i] = '\0';
    return 0;
}

/* ================================================================
 * Parse survivors array from JSON
 * "survivors": [{"id":1,"row":2,"col":3,"urgency":8,"rescued":false}, ...]
 * Returns count of survivors parsed.
 * ================================================================ */
static int parse_survivors(const char *json, Survivor *out, int cap) {
    const char *pos = strstr(json, "\"survivors\":");
    if (!pos) return 0;
    pos = strchr(pos, '[');
    if (!pos) return 0;

    int count = 0;
    while (count < cap) {
        pos = strchr(pos, '{');
        if (!pos) break;

        /* Extract fields from this object */
        const char *close = strchr(pos, '}');
        if (!close) break;

        /* Copy object into a small buffer for safe parsing */
        char obj[256];
        int len = (int)(close - pos + 1);
        if (len >= (int)sizeof(obj)) { pos = close + 1; continue; }
        strncpy(obj, pos, len);
        obj[len] = '\0';

        Survivor s;
        s.id      = json_get_int(obj, "id",      0);
        s.row     = json_get_int(obj, "row",     0);
        s.col     = json_get_int(obj, "col",     0);
        s.urgency = json_get_int(obj, "urgency", 1);
        /* "rescued" is a JSON boolean — treat non-zero as rescued */
        const char *rp = strstr(obj, "\"rescued\":");
        s.rescued = 0;
        if (rp) {
            rp += strlen("\"rescued\":");
            while (*rp == ' ') rp++;
            if (strncmp(rp, "true", 4) == 0) s.rescued = 1;
        }

        out[count++] = s;
        pos = close + 1;
    }
    return count;
}

/* ================================================================
 * Parse 2-D grid  "grid": [[0,1,...], ...]
 * Fills grid[r][c], sets *rows and *cols.
 * ================================================================ */
static void parse_grid(const char *json,
                        int grid[MAX_GRID_ROWS][MAX_GRID_COLS],
                        int *rows, int *cols) {
    *rows = 0; *cols = 0;
    const char *pos = strstr(json, "\"grid\":");
    if (!pos) return;
    pos = strchr(pos, '[');   /* outer [ */
    if (!pos) return;
    pos++;                    /* step past outer [ */

    while (*rows < MAX_GRID_ROWS) {
        /* find next row array */
        const char *row_start = strchr(pos, '[');
        const char *row_end   = strchr(pos, ']');
        if (!row_start || !row_end || row_end < row_start) break;

        /* check we haven't hit the outer ] */
        const char *outer_close = strchr(pos, ']');
        if (outer_close && outer_close == row_end &&
            strchr(pos, '[') == NULL) break;

        int c = 0;
        const char *p = row_start + 1;
        while (p < row_end && c < MAX_GRID_COLS) {
            while (*p == ' ' || *p == '\n' || *p == '\r') p++;
            if (*p == ']') break;
            grid[*rows][c++] = atoi(p);
            while (*p && *p != ',' && *p != ']') p++;
            if (*p == ',') p++;
        }
        if (*cols < c) *cols = c;
        (*rows)++;

        pos = row_end + 1;
        /* stop at outer closing bracket */
        const char *next_open  = strchr(pos, '[');
        const char *outer_cl2  = strchr(pos, ']');
        if (!next_open || (outer_cl2 && outer_cl2 < next_open)) break;
    }
}

/* ================================================================
 * Write state.json
 * ================================================================ */
static void write_state_json(
    const char    *path,
    const LinkedList *route,
    const AVLTree    *tree,
    int agent_row, int agent_col,
    int rescued,   int total,
    int grid[MAX_GRID_ROWS][MAX_GRID_COLS],
    int grid_rows, int grid_cols)
{
    FILE *f = fopen(path, "w");
    if (!f) { fprintf(stderr, "Cannot write %s\n", path); return; }

    fprintf(f, "{\n");

    /* agent position */
    fprintf(f, "  \"agent_pos\": [%d, %d],\n", agent_row, agent_col);
    fprintf(f, "  \"rescued\": %d,\n", rescued);
    fprintf(f, "  \"total\": %d,\n", total);

    /* route (linked list) */
    int route_rows[MAX_ROUTE], route_cols[MAX_ROUTE];
    int rlen = list_to_arrays(route, route_rows, route_cols, MAX_ROUTE);
    fprintf(f, "  \"route\": [");
    for (int i = 0; i < rlen; i++) {
        fprintf(f, "[%d,%d]", route_rows[i], route_cols[i]);
        if (i + 1 < rlen) fprintf(f, ", ");
    }
    fprintf(f, "],\n");

    /* survivors still in the AVL tree */
    Survivor svs[MAX_SURVIVORS];
    int slen = avl_to_array(tree, svs, MAX_SURVIVORS);
    fprintf(f, "  \"survivors\": [");
    for (int i = 0; i < slen; i++) {
        fprintf(f, "{\"id\":%d,\"row\":%d,\"col\":%d,\"urgency\":%d,\"rescued\":%s}",
            svs[i].id, svs[i].row, svs[i].col, svs[i].urgency,
            svs[i].rescued ? "true" : "false");
        if (i + 1 < slen) fprintf(f, ", ");
    }
    fprintf(f, "],\n");

    /* grid */
    fprintf(f, "  \"grid\": [\n");
    for (int r = 0; r < grid_rows; r++) {
        fprintf(f, "    [");
        for (int c = 0; c < grid_cols; c++) {
            fprintf(f, "%d", grid[r][c]);
            if (c + 1 < grid_cols) fprintf(f, ", ");
        }
        fprintf(f, "]");
        if (r + 1 < grid_rows) fprintf(f, ",");
        fprintf(f, "\n");
    }
    fprintf(f, "  ]\n");

    fprintf(f, "}\n");
    fclose(f);
}

/* ================================================================
 * Main
 * ================================================================ */
int main(void) {
    const char *input_path = "../data/input.json";
    const char *state_path = "../data/state.json";

    /* --- Read input.json --- */
    static char json_buf[MAX_FILE_SIZE];
    if (read_file(input_path, json_buf, MAX_FILE_SIZE) != 0)
        return 1;

    char action[32];
    json_get_str(json_buf, "action", action, sizeof(action));

    int agent_row = json_get_int(json_buf, "agent_row", 0);
    int agent_col = json_get_int(json_buf, "agent_col", 0);
    int rescued   = json_get_int(json_buf, "rescued",   0);

    /* --- Parse grid --- */
    static int grid[MAX_GRID_ROWS][MAX_GRID_COLS];
    int grid_rows = 0, grid_cols = 0;
    parse_grid(json_buf, grid, &grid_rows, &grid_cols);

    /* --- Parse survivors --- */
    static Survivor survivors[MAX_SURVIVORS];
    int total = parse_survivors(json_buf, survivors, MAX_SURVIVORS);

    /* --- Rebuild AVL tree from unrescued survivors --- */
    AVLTree tree;
    avl_init(&tree);
    for (int i = 0; i < total; i++) {
        if (!survivors[i].rescued)
            avl_insert(&tree, survivors[i]);
    }

    /* --- Linked list for the route --- */
    LinkedList route;
    list_init(&route);

    /* --- Process action --- */
    if (strcmp(action, "rescue") == 0 && !avl_is_empty(&tree)) {
        Survivor top = avl_get_max(&tree);
        top.rescued  = 1;
        avl_remove(&tree, top.id);
        list_append(&route, agent_row, agent_col);
        rescued++;
        agent_row = top.row;
        agent_col = top.col;
        list_append(&route, agent_row, agent_col);

    } else if (strcmp(action, "move") == 0) {
        int new_row = json_get_int(json_buf, "new_row", agent_row);
        int new_col = json_get_int(json_buf, "new_col", agent_col);
        agent_row = new_row;
        agent_col = new_col;
        list_append(&route, agent_row, agent_col);
    }

    /* --- Write state.json --- */
    write_state_json(state_path, &route, &tree,
                     agent_row, agent_col,
                     rescued, total,
                     grid, grid_rows, grid_cols);

    /* --- Cleanup --- */
    avl_destroy(&tree);
    list_destroy(&route);

    printf("Engine: state written OK\n");
    return 0;
}
