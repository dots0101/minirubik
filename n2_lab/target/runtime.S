#ifndef MODE
#define MODE 0
#endif
#ifndef RENDER
#define RENDER 0
#endif
#ifndef EXPECTED
#define EXPECTED 11
#endif
.option norvc
.option norelax
.text
.globl _start
_start:
    la sp, __stack_top
    li s11, 0
#if RENDER
    call led_clear
#endif
#if MODE == 0
    la a0, input_string
    la a1, input_state
    call parse_upstream
    beqz a0, input_error
    la t0, expected_depth
    lb a0, 0(t0)
    call solve_and_replay
    beqz a0, test_error
    li s11, 1
#elif MODE == 2
    li s8, 0
    la s9, test_vectors
.Lvectors:
    mv a0, s9
    la a1, input_state
    call parse_upstream
    beqz a0, input_error
    lbu a0, 15(s9)
    call solve_and_replay
    beqz a0, test_error
    addi s11, s11, 1
    addi s9, s9, 16
    addi s8, s8, 1
    li t0, TEST_VECTOR_COUNT
    bltu s8, t0, .Lvectors
#endif
    la a0, pass_message
    li a7, 4
    ecall
    mv a0, s11
    li a7, 1
    ecall
    la a0, newline
    li a7, 4
    ecall
    li a0, 0
    li a7, 93
    ecall
test_error:
    la a0, fail_message
    li a7, 4
    ecall
    li a0, 1
    li a7, 93
    ecall
input_error:
    la a0, input_message
    li a7, 4
    ecall
    li a0, 2
    li a7, 93
    ecall

/* The adapter is a graph conjugacy, not a guessed renumbering.
 * Upstream indices 0..6 map to 3,1,5,2,0,4,6. Orientations are unchanged.
 * Validate all seven orientation digits before dropping the dependent one.
 */
parse_upstream:
    la t6, upstream_map
    li t0, 0
    li t1, 0
.Lparse_perm:
    add t2, a0, t0
    lbu t2, 0(t2)
    addi t2, t2, -49
    li t3, 7
    bgeu t2, t3, .Lparse_bad
    li t3, 1
    sll t3, t3, t2
    and t4, t1, t3
    bnez t4, .Lparse_bad
    or t1, t1, t3
    add t2, t6, t2
    lbu t2, 0(t2)
    add t3, t6, t0
    lbu t3, 0(t3)
    add t3, a1, t3
    sb t2, 0(t3)
    addi t0, t0, 1
    li t3, 7
    bltu t0, t3, .Lparse_perm
    li t0, 0
    li t1, 0
.Lparse_ori:
    add t2, a0, t0
    lbu t2, 7(t2)
    addi t2, t2, -49
    li t3, 3
    bgeu t2, t3, .Lparse_bad
    add t1, t1, t2
    add t3, t6, t0
    lbu t3, 0(t3)
    li t4, 6
    bgeu t3, t4, .Lparse_ori_next
    add t3, a1, t3
    sb t2, 7(t3)
.Lparse_ori_next:
    addi t0, t0, 1
    li t3, 7
    bltu t0, t3, .Lparse_ori
    lbu t0, 14(a0)
    bnez t0, .Lparse_bad
.Lparse_mod:
    addi t1, t1, -3
    bgez t1, .Lparse_mod
    li t0, -3
    bne t1, t0, .Lparse_bad
    li a0, 1
    ret
.Lparse_bad:
    li a0, 0
    ret

/* In-program correctness gate: expected optimal length and actual replay. */
solve_and_replay:
    addi sp, sp, -32
    sw ra, 28(sp)
    sw s0, 24(sp)
    sw s1, 20(sp)
    sw s2, 16(sp)
    sw s3, 12(sp)
    mv s3, a0
    la a0, input_state
    la a1, output_moves
    la a2, output_count
    li a3, 0
    call n2_solve
    beqz a0, .Lreplay_bad
    la t0, output_count
    lbu s2, 0(t0)
    bgez s3, .Lreplay_expected
    li t0, 12
    bgeu s2, t0, .Lreplay_bad
    j .Lreplay_copy
.Lreplay_expected:
    bne s2, s3, .Lreplay_bad
.Lreplay_copy:
    la t0, input_state
    la s0, replay_state
    lw t1, 0(t0)
    lw t2, 4(t0)
    lw t3, 8(t0)
    lbu t4, 12(t0)
    sw t1, 0(s0)
    sw t2, 4(s0)
    sw t3, 8(s0)
    sb t4, 12(s0)
#if RENDER
    mv a0, s0
    call render_cube
#endif
    li s1, 0
.Lreplay_loop:
    bgeu s1, s2, .Lreplay_check
    la t0, output_moves
    add t0, t0, s1
    lbu a1, 0(t0)
    mv a0, s0
    call n2_apply_move
    beqz a0, .Lreplay_bad
#if RENDER
    mv a0, s0
    call render_cube
#endif
    addi s1, s1, 1
    j .Lreplay_loop
.Lreplay_check:
    mv a0, s0
    call n2_is_solved
    beqz a0, .Lreplay_bad
#if MODE == 0
    la a0, solution_message
    li a7, 4
    ecall
    li s1, 0
.Lprint_moves:
    bgeu s1, s2, .Lprint_done
    la t0, output_moves
    add t0, t0, s1
    lbu t0, 0(t0)
    slli t0, t0, 2
    la t1, move_names
    add a0, t1, t0
    li a7, 4
    ecall
    addi s1, s1, 1
    j .Lprint_moves
.Lprint_done:
    la a0, newline
    li a7, 4
    ecall
#endif
    li a0, 1
    j .Lreplay_return
.Lreplay_bad:
    li a0, 0
.Lreplay_return:
    lw s3, 12(sp)
    lw s2, 16(sp)
    lw s1, 20(sp)
    lw s0, 24(sp)
    lw ra, 28(sp)
    addi sp, sp, 32
    ret

#if RENDER
/* No framebuffer, snapshots, animation delay or renderer stack frame. */
led_clear:
    li t0, LED_MATRIX_0_BASE
    li t1, (LED_MATRIX_0_WIDTH * LED_MATRIX_0_HEIGHT)
.Lled_clear:
    sw zero, 0(t0)
    addi t0, t0, 4
    addi t1, t1, -1
    bnez t1, .Lled_clear
    ret
render_cube:
    li a6, 0
    li t0, 6
    addi t1, a0, 7
.Lled_sum:
    lbu t2, 0(t1)
    add a6, a6, t2
    addi t1, t1, 1
    addi t0, t0, -1
    bnez t0, .Lled_sum
.Lled_mod:
    addi a6, a6, -3
    bgez a6, .Lled_mod
    addi a6, a6, 3
    beqz a6, .Lled_start
    li t0, 3
    sub a6, t0, a6
.Lled_start:
    li a1, 0
    li a2, LED_MATRIX_0_BASE
.Lled_sticker:
    la t0, facelet_slots
    add t0, t0, a1
    lbu t0, 0(t0)
    andi t1, t0, 7
    srli t0, t0, 3
    li t2, 7
    li t3, 0
    beq t1, t2, .Lled_color
    add t2, a0, t1
    lbu t2, 0(t2)
    li t3, 6
    beq t1, t3, .Lled_dependent
    add t3, a0, t1
    lbu t3, 7(t3)
    j .Lled_color
.Lled_dependent:
    mv t3, a6
.Lled_color:
    add t0, t0, t3
    addi t3, t0, -3
    bltz t3, .Lled_slot
    mv t0, t3
.Lled_slot:
    slli t3, t2, 1
    add t2, t2, t3
    add t2, t2, t0
    la t3, cubie_colors
    add t2, t2, t3
    lbu t2, 0(t2)
    slli t2, t2, 2
    la t3, rgb_colors
    add t2, t2, t3
    lw a3, 0(t2)
    srli t0, a1, 2
    slli t0, t0, 1
    la t1, face_offsets
    add t0, t0, t1
    lhu t0, 0(t0)
    andi t1, a1, 1
    slli t1, t1, 2
    add t0, t0, t1
    andi t1, a1, 2
    beqz t1, .Lled_address
    addi t0, t0, 105
.Lled_address:
    slli t0, t0, 2
    add a4, a2, t0
    li a5, 3
.Lled_row:
    sw a3, 0(a4)
    sw a3, 4(a4)
    sw a3, 8(a4)
    sw a3, 12(a4)
    addi a4, a4, (LED_MATRIX_0_WIDTH * 4)
    addi a5, a5, -1
    bnez a5, .Lled_row
    addi a1, a1, 1
    li t0, 24
    bltu a1, t0, .Lled_sticker
    ret
#endif

.section .rodata
.balign 4
.globl input_string
input_string: .asciz "21345671111111"
.globl expected_depth
expected_depth: .byte EXPECTED
upstream_map: .byte 3,1,5,2,0,4,6
.balign 2
pass_message: .asciz "PASS cases="
fail_message: .asciz "FAIL solve/replay\n"
input_message: .asciz "FAIL input\n"
newline: .asciz "\n"
#if MODE == 0
solution_message: .asciz "Solution: "
move_names: .ascii "R' \0R2 \0R \0\0D' \0D2 \0D \0\0B' \0B2 \0B \0\0"
#endif
#if RENDER
.balign 4
facelet_slots:
.byte 6,2,7,3, 14,23,20,13, 15,19,21,9, 11,18,17,8, 10,22,16,12, 5,1,4,0
cubie_colors:
.byte 5,3,4, 5,2,3, 0,4,3, 0,3,2, 5,4,1, 5,1,2, 0,1,4, 0,2,1
.balign 4
rgb_colors: .word 0xffffff,0xff8000,0x00d060,0xff2020,0x2080ff,0xffff00
face_offsets: .half 9,245,254,263,272,499
#endif
.section .bss
.balign 4
input_state: .space 13
output_moves: .space 11
replay_state: .space 13
output_count: .space 1
