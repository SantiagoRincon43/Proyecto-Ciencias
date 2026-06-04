/* ============================================================
 * Team 7 - Rescue Mission | Computer Sciences I 2026-I
 * Members: Rincon Arevalo Johan Santiago,
 *          Diaz Paez Juan David
 * File: linked_list.c
 * Description: Singly linked list that stores the rescue
 *              route as a sequence of (row, col) coordinates.
 * ============================================================ */

#include "linked_list.h"
#include <stdlib.h>

/* ---- Lifecycle ---- */

void list_init(LinkedList *l) {
    l->head = NULL;
    l->tail = NULL;
    l->size = 0;
}

void list_destroy(LinkedList *l) {
    list_clear(l);
}

/* ---- append: add a new cell at the END of the route in O(1) ---- */
void list_append(LinkedList *l, int row, int col) {
    RouteNode *node = (RouteNode *)malloc(sizeof(RouteNode));
    node->row  = row;
    node->col  = col;
    node->next = NULL;

    if (l->tail == NULL) {       /* list was empty */
        l->head = l->tail = node;
    } else {
        l->tail->next = node;
        l->tail       = node;
    }
    l->size++;
}

/* ---- remove_last: undo the last step (used during backtracking rollback) ---- */
void list_remove_last(LinkedList *l) {
    if (l->head == NULL) return;  /* nothing to remove */

    if (l->head == l->tail) {     /* only one node */
        free(l->head);
        l->head = l->tail = NULL;
    } else {
        /* Walk to the second-to-last node */
        RouteNode *cur = l->head;
        while (cur->next != l->tail)
            cur = cur->next;
        free(l->tail);
        l->tail       = cur;
        l->tail->next = NULL;
    }
    l->size--;
}

/* ---- clear: free every node and reset the list ---- */
void list_clear(LinkedList *l) {
    RouteNode *cur = l->head;
    while (cur != NULL) {
        RouteNode *nxt = cur->next;
        free(cur);
        cur = nxt;
    }
    l->head = l->tail = NULL;
    l->size = 0;
}

/* ---- size ---- */
int list_size(const LinkedList *l) {
    return l->size;
}

/* ---- to_arrays: export into parallel row[]/col[] arrays ---- */
int list_to_arrays(const LinkedList *l, int *rows, int *cols, int cap) {
    int idx = 0;
    RouteNode *cur = l->head;
    while (cur != NULL && idx < cap) {
        rows[idx] = cur->row;
        cols[idx] = cur->col;
        idx++;
        cur = cur->next;
    }
    return idx;
}
