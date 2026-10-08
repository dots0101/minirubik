CC = gcc
CFLAGS = -O3 -std=c11 -Wall -Wextra -Wpedantic -Werror
SRC = n2_solver.c n2_core_data.c h48_policy_data.c h48_t_simple_data.c h48_s3_base.c h48_sigma_pr_data.c

all: test_n2_solver

test_n2_solver: $(SRC) test_n2_solver.c
	$(CC) $(CFLAGS) $(SRC) test_n2_solver.c -o $@

full_domain: $(SRC) test_full_domain.c
	$(CC) $(CFLAGS) $(SRC) test_full_domain.c -o $@

.PHONY: all
