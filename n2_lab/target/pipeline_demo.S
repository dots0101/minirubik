/* A reproducible microscope for the actual policy_lookup routine.
 * H48 key 89011 -> policy 3, from the supplied distance-6 worked example.
 * The complete authored solver is included unchanged below. */
.option norvc
.option norelax
.text
.globl _start
_start:
    la sp, __stack_top
    li a0, 89011
    call policy_lookup
    li t0, 3
    bne a0, t0, fail
    la t1, pipeline_result
    sw a0, 0(t1)
    lw t2, 0(t1)
    add t3, t2, t2
    li t4, 6
    bne t3, t4, fail
    li a0, 0
    li a7, 93
    ecall
fail:
    li a0, 1
    li a7, 93
    ecall
.include "policy_excerpt.S"
.section .bss
.balign 4
pipeline_result: .space 4
