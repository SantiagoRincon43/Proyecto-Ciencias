/* ============================================================
 * Team 7 - Rescue Mission | Computer Sciences I 2026-I
 * File: avl_tree.c
 * Description: Self-balancing AVL tree that stores survivors
 *              ordered by urgency level (key).
 *              Guarantees O(log k) insert / delete / max-query.
 * ============================================================ */

#include "avl_tree.h"
#include <stdlib.h>

/* ---- Internal helpers ---- */

static int node_height(const AVLNode *n) {
    return n ? n->height : 0;
}

static int max2(int a, int b) {
    return a > b ? a : b;
}

static void update_height(AVLNode *n) {
    if (n)
        n->height = 1 + max2(node_height(n->left), node_height(n->right));
}

static int balance_factor(const AVLNode *n) {
    return n ? node_height(n->left) - node_height(n->right) : 0;
}

/* ---- Rotations ----
 *
 *  rotate_right: used when left subtree is too tall
 *
 *      y                x
 *     / \              / \
 *    x   T3   -->    T1   y
 *   / \                  / \
 *  T1  T2              T2  T3
 */
static AVLNode *rotate_right(AVLNode *y) {
    AVLNode *x  = y->left;
    AVLNode *T2 = x->right;

    x->right = y;
    y->left  = T2;

    update_height(y);
    update_height(x);
    return x;
}

/* rotate_left: mirror of rotate_right */
static AVLNode *rotate_left(AVLNode *x) {
    AVLNode *y  = x->right;
    AVLNode *T2 = y->left;

    y->left  = x;
    x->right = T2;

    update_height(x);
    update_height(y);
    return y;
}

/* balance: recompute height then apply the needed rotation(s) */
static AVLNode *balance_node(AVLNode *n) {
    update_height(n);
    int bf = balance_factor(n);

    /* Left-Left */
    if (bf > 1 && balance_factor(n->left) >= 0)
        return rotate_right(n);

    /* Left-Right */
    if (bf > 1 && balance_factor(n->left) < 0) {
        n->left = rotate_left(n->left);
        return rotate_right(n);
    }

    /* Right-Right */
    if (bf < -1 && balance_factor(n->right) <= 0)
        return rotate_left(n);

    /* Right-Left */
    if (bf < -1 && balance_factor(n->right) > 0) {
        n->right = rotate_right(n->right);
        return rotate_left(n);
    }

    return n; /* already balanced */
}

/* ---- Insert ----
 * Key = urgency; ties broken by id so we never overwrite. */
static AVLNode *insert_node(AVLNode *node, Survivor s) {
    if (!node) {
        AVLNode *n = (AVLNode *)malloc(sizeof(AVLNode));
        n->data   = s;
        n->left   = n->right = NULL;
        n->height = 1;
        return n;
    }

    if (s.urgency < node->data.urgency)
        node->left  = insert_node(node->left,  s);
    else if (s.urgency > node->data.urgency)
        node->right = insert_node(node->right, s);
    else {
        /* same urgency: use id as tiebreaker */
        if (s.id < node->data.id)
            node->left  = insert_node(node->left,  s);
        else
            node->right = insert_node(node->right, s);
    }

    return balance_node(node);
}

/* ---- Remove by id ---- */
static AVLNode *find_min(AVLNode *node) {
    while (node->left) node = node->left;
    return node;
}

static AVLNode *remove_node(AVLNode *node, int id) {
    if (!node) return NULL;

    /* Search by id (tree is ordered by urgency; we do a full search) */
    AVLNode *left_result  = remove_node(node->left,  id);
    AVLNode *right_result = remove_node(node->right, id);

    if (node->data.id == id) {
        /* Found the node to delete */
        if (!node->left || !node->right) {
            AVLNode *child = node->left ? node->left : node->right;
            free(node);
            return child;
        }
        /* Two children: replace with in-order successor */
        AVLNode *succ  = find_min(node->right);
        node->data     = succ->data;
        node->right    = remove_node(node->right, succ->data.id);
        return balance_node(node);
    }

    node->left  = left_result;
    node->right = right_result;
    return balance_node(node);
}

/* ---- Destroy (free all nodes) ---- */
static void destroy_node(AVLNode *node) {
    if (!node) return;
    destroy_node(node->left);
    destroy_node(node->right);
    free(node);
}

/* ---- getMax: rightmost node = highest urgency ---- */
static AVLNode *get_max_node(AVLNode *node) {
    if (!node) return NULL;
    while (node->right) node = node->right;
    return node;
}

/* ---- In-order traversal into flat array ---- */
static int inorder(const AVLNode *node, Survivor *out, int cap, int idx) {
    if (!node || idx >= cap) return idx;
    idx = inorder(node->left,  out, cap, idx);
    if (idx < cap) out[idx++] = node->data;
    idx = inorder(node->right, out, cap, idx);
    return idx;
}

/* ================================================================
 * Public API
 * ================================================================ */

void avl_init(AVLTree *t) {
    t->root = NULL;
}

void avl_destroy(AVLTree *t) {
    destroy_node(t->root);
    t->root = NULL;
}

void avl_insert(AVLTree *t, Survivor s) {
    t->root = insert_node(t->root, s);
}

void avl_remove(AVLTree *t, int id) {
    t->root = remove_node(t->root, id);
}

Survivor avl_get_max(const AVLTree *t) {
    AVLNode *m = get_max_node(t->root);
    /* Caller must check avl_is_empty before calling this */
    return m->data;
}

int avl_is_empty(const AVLTree *t) {
    return t->root == NULL;
}

int avl_to_array(const AVLTree *t, Survivor *out, int cap) {
    return inorder(t->root, out, cap, 0);
}
