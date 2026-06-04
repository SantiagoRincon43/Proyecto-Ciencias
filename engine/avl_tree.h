/* ============================================================
 * Team 7 - Rescue Mission | Computer Sciences I 2026-I
 * File: avl_tree.h
 * Description: Self-balancing AVL tree (C with structs).
 *              Stores survivors ordered by urgency level.
 *              Guarantees O(log k) insert / delete / max-query.
 * ============================================================ */

#ifndef AVL_TREE_H
#define AVL_TREE_H

/* ---------- Survivor ---------- */
typedef struct {
    int urgency;    /* key: 1-10, higher = more urgent */
    int row;
    int col;
    int id;
    int rescued;    /* 0 = no, 1 = yes */
} Survivor;

/* ---------- AVL node ---------- */
typedef struct AVLNode {
    Survivor        data;
    struct AVLNode *left;
    struct AVLNode *right;
    int             height;
} AVLNode;

/* ---------- AVL tree ---------- */
typedef struct {
    AVLNode *root;
} AVLTree;

/* Lifecycle */
void avl_init   (AVLTree *t);
void avl_destroy(AVLTree *t);

/* Operations */
void      avl_insert  (AVLTree *t, Survivor s);
void      avl_remove  (AVLTree *t, int id);
Survivor  avl_get_max (const AVLTree *t);   /* highest urgency */
int       avl_is_empty(const AVLTree *t);

/* Serialisation helper:
 * Fills 'out' (caller-allocated array of at least 'cap' elements)
 * with an in-order traversal.  Returns the number of items written. */
int avl_to_array(const AVLTree *t, Survivor *out, int cap);

#endif /* AVL_TREE_H */
