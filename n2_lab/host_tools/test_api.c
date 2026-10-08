#include "n2_solver.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static unsigned checked;
static int rejected(const N2State *s) {
    uint8_t out[11], before[11], count = 0xa5;
    N2Stats stats = {0x1234, 0x56, 0x78};
    memset(out, 0xa5, sizeof out);
    memcpy(before, out, sizeof out);
    ++checked;
    return !n2_state_valid(s) && !n2_solve(s, out, &count, &stats)
        && !memcmp(out, before, sizeof out) && count == 0xa5
        && stats.search_nodes == 0x1234 && stats.solution_depth == 0x56
        && stats.prefix_depth == 0x78;
}
int main(void) {
    const N2State solved = {{0,1,2,3,4,5,6},{0,0,0,0,0,0}};
    N2State s;
    uint8_t out[11], count = 0xff;
    if (n2_solve(NULL, out, &count, NULL)
        || n2_solve(&solved, NULL, &count, NULL)
        || n2_solve(&solved, out, NULL, NULL)) return 1;
    if (!n2_solve(&solved, out, &count, NULL) || count != 0) return 2;
    if (!rejected(NULL)) return 3;
    for (unsigned i = 0; i < 7; ++i) {
        for (unsigned x = 7; x < 256; ++x) {
            s = solved; s.perm[i] = (uint8_t)x;
            if (!rejected(&s)) return 4;
        }
        for (unsigned j = 0; j < 7; ++j) if (i != j) {
            s = solved; s.perm[i] = (uint8_t)j;
            if (!rejected(&s)) return 5;
        }
    }
    for (unsigned i = 0; i < 6; ++i) for (unsigned x = 3; x < 256; ++x) {
        s = solved; s.twist[i] = (uint8_t)x;
        if (!rejected(&s)) return 6;
    }
    for (unsigned m = 9; m < 256; ++m) {
        s = solved;
        if (n2_apply_move(&s, (uint8_t)m) || memcmp(&s, &solved, sizeof s)) return 7;
    }
    for (unsigned m = 0; m < 9; ++m) {
        s = solved;
        if (!n2_apply_move(&s, (uint8_t)m)
            || !n2_solve(&s, out, &count, NULL) || count != 1
            || !n2_apply_move(&s, out[0]) || !n2_is_solved(&s)) return 8;
    }
    printf("PASS API invalid_states=%u invalid_moves=247 null_arguments=3 one_move=9\n", checked);
    return 0;
}
