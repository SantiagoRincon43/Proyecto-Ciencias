/* ============================================================
 * Team 7 - Rescue Mission | Computer Sciences I 2026-I
 * File: linked_list.h
 * Description: Singly linked list that stores the rescue
 *              route as a sequence of (row, col) coordinates.
 * ============================================================ */

#ifndef LINKED_LIST_H
#define LINKED_LIST_H

/* ---------- Node ---------- */
typedef struct RouteNode {
    int               row;
    int               col;
    struct RouteNode *next;
} RouteNode;

/* ---------- List ---------- */
typedef struct {
    RouteNode *head;
    RouteNode *tail;
    int        size;
} LinkedList;

/* Lifecycle */
void list_init   (LinkedList *l);
void list_destroy(LinkedList *l);

/* Operations */
void list_append     (LinkedList *l, int row, int col); /* O(1) */
void list_remove_last(LinkedList *l);                   /* O(n) */
void list_clear      (LinkedList *l);
int  list_size       (const LinkedList *l);

/* Serialisation helper:
 * Fills parallel arrays rows[] and cols[] (caller-allocated, size >= cap).
 * Returns the number of items written. */
int list_to_arrays(const LinkedList *l, int *rows, int *cols, int cap);

#endif /* LINKED_LIST_H */
