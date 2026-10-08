#include "n2_solver.h"
#include "n2_core_data.h"
#include "h48_policy_data.h"
#include "h48_t_simple_data.h"
#include "h48_s3_base.h"
#include "h48_sigma_pr_data.h"

#include <limits.h>

typedef struct { uint8_t p[8]; uint8_t o[8]; } WorkState;
typedef struct { uint32_t qidx; uint8_t perm_sym; uint8_t stab_sym; } CanonInfo;
typedef struct { uint32_t key; uint8_t rep; uint8_t perm_sym; uint8_t stab_sym; } H48Canon;

static uint16_t rank_mul(uint16_t x, uint8_t m) {
    switch (m) {
    case 2: return (uint16_t)(x << 1);
    case 3: return (uint16_t)((x << 1) + x);
    case 4: return (uint16_t)(x << 2);
    case 5: return (uint16_t)((x << 2) + x);
    case 6: return (uint16_t)((x << 2) + (x << 1));
    case 7: return (uint16_t)((x << 3) - x);
    default: return x;
    }
}

static const uint8_t mod3_lut[13] = {0,1,2,0,1,2,0,1,2,0,1,2,0};
static uint8_t mod3_small(unsigned x) { return mod3_lut[x]; }
static void work_copy(const WorkState *s, WorkState *d) {
    unsigned i;
    for (i = 0; i < 8u; ++i) { d->p[i] = s->p[i]; d->o[i] = s->o[i]; }
}


static int expand_public(const N2State *in, WorkState *out) {
    uint8_t seen = 0; unsigned i, sum = 0;
    if (!in || !out) return 0;
    for (i = 0; i < 7; ++i) { uint8_t p = in->perm[i]; if (p >= 7u || (seen & (uint8_t)(1u << p))) return 0; seen = (uint8_t)(seen | (uint8_t)(1u << p)); out->p[i] = p; }
    if (seen != 0x7fu) return 0;
    for (i = 0; i < 6; ++i) { uint8_t o = in->twist[i]; if (o >= 3u) return 0; out->o[i] = o; sum += o; }
    { uint8_t r = mod3_small(sum); out->o[6] = (uint8_t)(r == 0u ? 0u : 3u - r); }
    out->p[7] = 7; out->o[7] = 0; return 1;
}
static void compress_public(const WorkState *in, N2State *out) { unsigned i; for (i = 0; i < 7; ++i) out->perm[i] = in->p[i]; for (i = 0; i < 6; ++i) out->twist[i] = in->o[i]; }
int n2_state_valid(const N2State *state) { WorkState w; return expand_public(state, &w); }
int n2_is_solved(const N2State *state) { unsigned i; if (!state) return 0; for (i = 0; i < 7; ++i) if (state->perm[i] != i) return 0; for (i = 0; i < 6; ++i) if (state->twist[i] != 0u) return 0; return 1; }

static const uint8_t pop7[128] = {
0,1,1,2,1,2,2,3,1,2,2,3,2,3,3,4,1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,
1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,
1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,
2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7};
static uint16_t perm_rank7(const uint8_t p[8]) { uint16_t r = 0; uint8_t used = 0; unsigned i; for (i = 0; i < 6u; ++i) { uint8_t v = p[i], below = (uint8_t)((1u << v) - 1u), less = (uint8_t)(v - pop7[used & below]); r = (uint16_t)(rank_mul(r, (uint8_t)(7u - i)) + less); used = (uint8_t)(used | (uint8_t)(1u << v)); } return r; }
static uint16_t ori_rank_after_sym(const WorkState *s, uint8_t sym) { uint16_t r = 0; uint8_t inv = n2_b8_sym_inv[sym]; unsigned np; for (np = 0; np < 6u; ++np) { uint8_t pos = n2_b8_sym_pos[(unsigned)inv * 8u + np], piece = s->p[pos]; unsigned ti = ((((unsigned)sym * 8u + pos) * 8u + piece) * 3u) + s->o[pos]; uint8_t o = n2_b8_sym_twist[ti]; r = (uint16_t)((r << 1) + r + o); } return r; }
static void state_move(const WorkState *s, uint8_t mi, WorkState *d) { unsigned i; for (i = 0; i < 8; ++i) { uint8_t q = n2_b8_move_src[(unsigned)mi * 8u + i], v; d->p[i] = s->p[q]; v = (uint8_t)(s->o[q] + n2_b8_move_delta[(unsigned)mi * 8u + i]); d->o[i] = (uint8_t)(v >= 3u ? v - 3u : v); } }
int n2_apply_move(N2State *state, uint8_t move_id) { WorkState a,b; if (move_id >= N2_MOVE_COUNT || !expand_public(state,&a)) return 0; state_move(&a,move_id,&b); compress_public(&b,state); return 1; }
static void symmetry_apply(const WorkState *in, uint8_t sym, WorkState *out) { unsigned pos; for (pos = 0; pos < 8; ++pos) { uint8_t np = n2_b8_sym_pos[(unsigned)sym * 8u + pos], piece = in->p[pos]; unsigned ti = ((((unsigned)sym * 8u + pos) * 8u + piece) * 3u) + in->o[pos]; out->p[np] = n2_b8_sym_pos[(unsigned)sym * 8u + piece]; out->o[np] = n2_b8_sym_twist[ti]; } }
static uint8_t exception_action(unsigned e) { uint8_t x = n2_b8_exc_aid[e >> 1]; return (uint8_t)((e & 1u) ? (x >> 4) : (x & 15u)); }
static uint8_t stabilizer_mask(uint8_t aid) { static const uint8_t m[14] = {0x01u,0x3fu,0x03u,0x03u,0x19u,0x05u,0x05u,0x21u,0x19u,0x3fu,0x05u,0x05u,0x03u,0x03u}; return m[aid]; }
static uint8_t popcount32(uint32_t x) { x = x - ((x >> 1) & 0x55555555u); x = (x & 0x33333333u) + ((x >> 2) & 0x33333333u); x = (x + (x >> 4)) & 0x0f0f0f0fu; x += x >> 8; x += x >> 16; return (uint8_t)(x & 0x3fu); }
static uint16_t mask_rank(const uint32_t *mask, uint16_t i) { uint16_t c=0; unsigned w,full=i>>5; for(w=0;w<full;++w)c=(uint16_t)(c+popcount32(mask[w])); if(i&31u)c=(uint16_t)(c+popcount32(mask[full]&((1u<<(i&31u))-1u))); return c; }
static const uint16_t action_offset[14] = {0,0,23,46,69,92,115,138,161,184,207,230,253,276};
static CanonInfo quotient_rank_from_meta(const WorkState *s, uint16_t meta) {
    CanonInfo ci; unsigned oi=meta>>3; uint8_t bs=(uint8_t)(meta&7u); uint16_t local; ci.perm_sym=bs; ci.stab_sym=0;
    if(oi<814u){local=ori_rank_after_sym(s,bs);ci.qidx=h48_common_base[oi]+local;return ci;}
    { unsigned e=oi-814u; uint8_t aid=exception_action(e),sm=stabilizer_mask(aid),h; WorkState q; uint16_t best=UINT16_MAX; symmetry_apply(s,bs,&q); for(h=0;h<6u;++h){uint16_t r;if(!(sm&(uint8_t)(1u<<h)))continue;r=ori_rank_after_sym(&q,h);if(r<best){best=r;ci.stab_sym=h;}} local=mask_rank(&n2_b8_action_mask[action_offset[aid]],best);ci.qidx=h48_exc_base[e]+local; }
    return ci;
}
static uint16_t quotient_perm_meta(const WorkState *s) { return n2_b8_pmeta[perm_rank7(s->p)]; }

static const uint8_t t_remtab[7][6] = {
    {1,2,3,4,5,6},{0,2,3,4,5,6},{0,1,3,4,5,6},{0,1,2,4,5,6},
    {0,1,2,3,5,6},{0,1,2,3,4,6},{0,1,2,3,4,5}
};
static void compact_T(const WorkState *s, WorkState *d) {
    int pos6 = 0;
    unsigned q, posp, twp, i, sumy = 0, sum;
    const uint8_t *rem, *remp;
    uint8_t y[5];
    uint32_t ctl;
    while (s->p[pos6] != 6u) ++pos6;
    q = (unsigned)pos6 * 3u + s->o[pos6];
    {
        uint8_t dst = h48_t_dst[q];
        posp = dst & 7u;
        twp = dst >> 3;
    }
    rem = t_remtab[pos6];
    remp = t_remtab[posp];

    d->p[7] = 7u;
    for (i = 0; i < 6u; ++i)
        d->p[remp[i]] = (uint8_t)(s->p[rem[h48_t_perm_R[q][i]]] ^ 1u);
    d->p[posp] = 6u;

    for (i = 0; i < 5u; ++i) { y[i] = s->o[rem[i]]; sumy += y[i]; }
    d->o[7] = 0u;
    d->o[posp] = (uint8_t)twp;
    sum = twp;
    ctl = h48_t_ori_ctl[q];
    for (i = 0; i < 5u; ++i) {
        uint8_t item = (uint8_t)(ctl & 31u);
        uint8_t si = item & 7u;
        unsigned term = si == 7u ? sumy : ((unsigned)y[si] << 1);
        uint8_t v = mod3_small((item >> 3) + term);
        d->o[remp[i]] = v;
        sum += v;
        ctl >>= 5;
    }
    {
        uint8_t r = mod3_small(sum);
        d->o[remp[5]] = (uint8_t)(r ? 3u - r : 0u);
    }
}
/* Pull back a single edge label; rows 0..5 are S3, rows 6..11 are T codes. */
static const uint8_t move_pullback[12][9] = {
    {0,1,2,3,4,5,6,7,8},
    {2,1,0,8,7,6,5,4,3},
    {5,4,3,2,1,0,8,7,6},
    {3,4,5,6,7,8,0,1,2},
    {6,7,8,0,1,2,3,4,5},
    {8,7,6,5,4,3,2,1,0},
    {2,1,0,5,4,3,8,7,6},
    {2,1,0,8,7,6,5,4,3},
    {5,4,3,2,1,0,8,7,6},
    {8,7,6,2,1,0,5,4,3},
    {5,4,3,8,7,6,2,1,0},
    {8,7,6,5,4,3,2,1,0},
};
static uint8_t t_sigma_code(const WorkState *s) {
    int pos = 0;
    uint16_t pr, idx, bit, byte, pair;
    uint8_t shift;
    while (s->p[pos] != 6u) ++pos;
    pr = perm_rank7(s->p);
    idx = (uint16_t)(((pr << 1) + pr) + s->o[pos]);
    bit = (uint16_t)((idx << 1) + idx);
    byte = (uint16_t)(bit >> 3);
    shift = (uint8_t)(bit & 7u);
    pair = (uint16_t)(h48_sigma_pr_3bit[byte] |
                      ((uint16_t)h48_sigma_pr_3bit[byte + 1u] << 8));
    return (uint8_t)((pair >> shift) & 7u);
}
static const uint8_t h48_len[8]={0,1,2,2,3,3,4,5};
static const uint8_t h48_word[8][5]={{0},{6},{1,6},{3,6},{6,1,6},{6,3,6},{1,6,3,6},{6,1,6,3,6}};
static H48Canon h48_canonicalize(const WorkState *s, uint16_t first_meta) {
    H48Canon h; WorkState r[8], a; uint16_t meta[8], min_oi; unsigned i;
    h.key = UINT32_MAX; h.rep = 0; h.perm_sym = 0; h.stab_sym = 0;
    work_copy(s, &r[0]);
    compact_T(s, &r[1]);
    symmetry_apply(s, 1, &a); compact_T(&a, &r[2]);
    symmetry_apply(s, 3, &a); compact_T(&a, &r[3]);
    symmetry_apply(&r[1], 1, &a); compact_T(&a, &r[4]);
    symmetry_apply(&r[1], 3, &a); compact_T(&a, &r[5]);
    symmetry_apply(&r[2], 3, &a); compact_T(&a, &r[6]);
    symmetry_apply(&r[4], 3, &a); compact_T(&a, &r[7]);
    meta[0] = first_meta; min_oi = (uint16_t)(meta[0] >> 3);
    for (i = 1; i < 8u; ++i) { uint16_t oi; meta[i] = quotient_perm_meta(&r[i]); oi = (uint16_t)(meta[i] >> 3); if (oi < min_oi) min_oi = oi; }
    for (i = 0; i < 8u; ++i) {
        if ((meta[i] >> 3) == min_oi) {
            CanonInfo ci = quotient_rank_from_meta(&r[i], meta[i]);
            if (ci.qidx < h.key) { h.key = ci.qidx; h.rep = (uint8_t)i; h.perm_sym = ci.perm_sym; h.stab_sym = ci.stab_sym; }
        }
    }
    return h;
}
/* The inverse of a composition acts in reverse order.  Record only
 * the state-dependent edge-map codes, not all nine possible edge labels. */
static uint8_t lift_policy_move(const WorkState *s, const H48Canon *h, uint8_t canonical_move) {
    WorkState scratch[2];
    const WorkState *cur = s;
    uint8_t codes[5], m;
    unsigned length = h48_len[h->rep], k;
    for (k = 0; k < length; ++k) {
        uint8_t op = h48_word[h->rep][k];
        codes[k] = op == 6u ? (uint8_t)(6u + t_sigma_code(cur)) : op;
        /* No transformed state is needed after the final edge-map code. */
        if (k + 1u < length) {
            WorkState *next = &scratch[k & 1u];
            if (op == 6u) compact_T(cur, next); else symmetry_apply(cur, op, next);
            cur = next;
        }
    }
    m = move_pullback[h->stab_sym][canonical_move];
    m = move_pullback[h->perm_sym][m];
    while (length != 0u) m = move_pullback[codes[--length]][m];
    return m;
}
static uint8_t policy_lookup(uint32_t key) {
    uint32_t x = key ^ (key >> 13) ^ (key << 7);
    uint32_t bucket = x & 0x3fffu;
    uint32_t y = key ^ (key >> 7) ^ (key << 9);
    uint32_t slot, word, first_word, rank, w;
    uint8_t b;
    y ^= y >> 5;
    slot = (((y >> 2) & 0x1ffffu) + h48_policy_disp[bucket]) & 0x1ffffu;
    word = slot >> 5;
    first_word = (slot / H48_POLICY_BLOCK_BITS) * H48_POLICY_WORDS_PER_BLOCK;
    rank = h48_policy_prefix[slot / H48_POLICY_BLOCK_BITS];
    for (w = first_word; w < word; ++w) rank += popcount32(h48_policy_used[w]);
    if (slot & 31u)
        rank += popcount32(h48_policy_used[word] & ((1u << (slot & 31u)) - 1u));
    b = h48_policy_dense[rank >> 1];
    return (uint8_t)((rank & 1u) ? (b >> 4) : (b & 15u));
}
static int work_solved(const WorkState *s){unsigned i;for(i=0;i<7u;++i)if(s->p[i]!=i)return 0;for(i=0;i<7u;++i)if(s->o[i]!=0u)return 0;return 1;}

int n2_solve(const N2State *state, uint8_t out[N2_MAX_DEPTH], uint8_t *count, N2Stats *stats) {
    WorkState cur;
    uint8_t k = 0;
    H48Canon hfirst;
    int have_first = 0;
    uint16_t pr;
    if (!state || !out || !count) return 0;
    if (n2_is_solved(state)) {
        *count = 0;
        if (stats) { stats->search_nodes = 0; stats->solution_depth = 0; stats->prefix_depth = 0; }
        return 1;
    }
    if (!expand_public(state, &cur)) return 0;
    pr = perm_rank7(cur.p);
    hfirst = h48_canonicalize(&cur, n2_b8_pmeta[pr]);
    have_first = 1;
    while (!work_solved(&cur)) {
        H48Canon h;
        uint8_t pol, m;
        WorkState next;
        if (k >= N2_MAX_DEPTH) return 0;
        if (have_first) { h = hfirst; have_first = 0; }
        else h = h48_canonicalize(&cur, quotient_perm_meta(&cur));
        pol = policy_lookup(h.key);
        if (pol >= 9u) return 0;
        m = lift_policy_move(&cur, &h, pol);
        if (m >= 9u) return 0;
        out[k++] = m;
        state_move(&cur, m, &next);
        work_copy(&next, &cur);
    }
    *count = k;
    if (stats) { stats->search_nodes = 0; stats->solution_depth = k; stats->prefix_depth = 0; }
    return 1;
}
