#ifndef H48_POLICY_DATA_H
#define H48_POLICY_DATA_H
#include <stdint.h>
#define H48_POLICY_BUCKETS 16384u
#define H48_POLICY_SLOTS 131072u
#define H48_POLICY_BLOCK_BITS 512u
#define H48_POLICY_WORDS_PER_BLOCK 16u
extern const uint8_t h48_policy_disp[H48_POLICY_BUCKETS];
extern const uint32_t h48_policy_used[4096];
extern const uint32_t h48_policy_prefix[256];
extern const uint8_t h48_policy_dense[38901];
#endif
