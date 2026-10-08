#ifndef N2_SOLVER_H
#define N2_SOLVER_H

#include <stdint.h>

#define N2_STATE_COUNT 3674160u
#define N2_MAX_DEPTH 11u
#define N2_MOVE_COUNT 9u

/* Fixed-reference-corner coordinates.
 * perm[0..6] is a permutation of 0..6.
 * twist[0..5] are base-3 digits.  twist[6] is implied by sum(twist[0..6]) == 0 mod 3.
 * Corner 7 is fixed at position 7 with twist 0.
 */
typedef struct {
    uint8_t perm[7];
    uint8_t twist[6];
} N2State;

/* Three movable faces opposite the fixed reference corner.
 * IDs are grouped by face; within a face: quarter, half, inverse-quarter.
 * The exact X/Y/Z-to-R/L/U/D/F/B naming is an external coordinate convention.
 */
enum {
    N2_X = 0, N2_X2 = 1, N2_X3 = 2,
    N2_Y = 3, N2_Y2 = 4, N2_Y3 = 5,
    N2_Z = 6, N2_Z2 = 7, N2_Z3 = 8
};

typedef struct {
    uint16_t search_nodes;
    uint8_t solution_depth;
    uint8_t prefix_depth;
} N2Stats;

int n2_state_valid(const N2State *state);
int n2_is_solved(const N2State *state);
int n2_apply_move(N2State *state, uint8_t move_id);

/* Exact HTM solver.  Returns 1 on success; the first *count entries of out are valid. */
int n2_solve(const N2State *state,
             uint8_t out[N2_MAX_DEPTH],
             uint8_t *count,
             N2Stats *stats);

#endif
