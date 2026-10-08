#include "n2_solver.h"
#include <stdint.h>
#include <stdio.h>

static uint32_t rng = 1u;
static uint32_t rnd(void)
{
    rng ^= rng << 13;
    rng ^= rng >> 17;
    rng ^= rng << 5;
    return rng;
}

static N2State solved_state(void)
{
    N2State s = {{0,1,2,3,4,5,6},{0,0,0,0,0,0}};
    return s;
}

int main(void)
{
    unsigned t;
    N2State z = solved_state();
    uint8_t sol[N2_MAX_DEPTH], n = 0;
    N2Stats st;

    if (!n2_state_valid(&z) || !n2_is_solved(&z)) return 2;
    if (!n2_solve(&z, sol, &n, &st) || n != 0) return 3;

    for (t = 0; t < 5000; ++t) {
        N2State s = solved_state(), check;
        unsigned len = 1u + (rnd() % 30u), i;
        uint8_t prev_face = 0xffu;
        for (i = 0; i < len; ++i) {
            uint8_t m;
            do m = (uint8_t)(rnd() % 9u); while ((uint8_t)(m / 3u) == prev_face);
            prev_face = (uint8_t)(m / 3u);
            if (!n2_apply_move(&s, m)) return 4;
        }
        check = s;
        if (!n2_solve(&s, sol, &n, &st) || n > N2_MAX_DEPTH) return 5;
        for (i = 0; i < n; ++i) if (!n2_apply_move(&check, sol[i])) return 6;
        if (!n2_is_solved(&check)) return 7;
    }

    puts("PASS n2 standalone random=5000");
    return 0;
}
