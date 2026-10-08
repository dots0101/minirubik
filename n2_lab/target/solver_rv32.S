/* Authored RV32I implementation of the supplied balanced exact-policy solver (2026-10-07).
 * This is AI-assisted source, not a claim of student hand authorship.
 * ABI: n2_solve/n2_apply_move/n2_is_solved match reference/n2_solver.h.
 * All working states are 16-byte, aligned, fixed stack objects.
 */
.option norvc
.option norelax
.text
.globl n2_solve
.globl n2_apply_move
.globl n2_is_solved
.globl n2_state_valid

/* Six factoradic digits. Constant strides are explicit shifts and adds. */
.macro RANK_DIGIT offset, factor
    lbu t2, \offset(a0)
    sll t6, a2, t2
    addi t3, t6, -1
    and t3, t3, t1
    add t3, t5, t3
    lbu t3, 0(t3)
    sub t2, t2, t3
    .if \factor == 7
        slli t3, t0, 3
        sub t0, t3, t0
    .elseif \factor == 6
        slli t3, t0, 2
        slli t4, t0, 1
        add t0, t3, t4
    .elseif \factor == 5
        slli t3, t0, 2
        add t0, t3, t0
    .elseif \factor == 4
        slli t0, t0, 2
    .elseif \factor == 3
        slli t3, t0, 1
        add t0, t3, t0
    .else
        slli t0, t0, 1
    .endif
    add t0, t0, t2
    or t1, t1, t6
.endm
perm_rank7:
    /* At the first digit, used is empty and 0*7+p[0] is p[0]. */
    lbu t0, 0(a0)
    li t1, 1
    sll t1, t1, t0
    la t5, pop7
    li a2, 1
    RANK_DIGIT 1,6
    RANK_DIGIT 2,5
    RANK_DIGIT 3,4
    RANK_DIGIT 4,3
    RANK_DIGIT 5,2
    mv a0, t0
    ret

/* Read only the public 13-byte representation. */
n2_is_solved:
    beqz a0, .Lis_no
    li t0, 0
.Lis_perm:
    add t1, a0, t0
    lbu t2, 0(t1)
    bne t2, t0, .Lis_no
    addi t0, t0, 1
    li t3, 7
    bltu t0, t3, .Lis_perm
    addi t1, a0, 7
    li t0, 6
.Lis_ori:
    lbu t2, 0(t1)
    bnez t2, .Lis_no
    addi t1, t1, 1
    addi t0, t0, -1
    bnez t0, .Lis_ori
    li a0, 1
    ret
.Lis_no:
    li a0, 0
    ret

n2_state_valid:
    addi sp, sp, -32
    sw ra, 28(sp)
    mv a1, sp
    call expand_public
    lw ra, 28(sp)
    addi sp, sp, 32
    ret

expand_public:
    beqz a0, .Lexpand_bad
    li t0, 0
    li t1, 0
    li t5, 7
.Lexpand_p:
    add t2, a0, t0
    lbu t3, 0(t2)
    bgeu t3, t5, .Lexpand_bad
    li t4, 1
    sll t4, t4, t3
    and t6, t1, t4
    bnez t6, .Lexpand_bad
    or t1, t1, t4
    add t2, a1, t0
    sb t3, 0(t2)
    addi t0, t0, 1
    bltu t0, t5, .Lexpand_p
    sb t5, 7(a1)
    addi t1, a0, 7
    addi t2, a1, 8
    li t0, 6
    li t4, 0
    li t5, 3
.Lexpand_o:
    lbu t3, 0(t1)
    bgeu t3, t5, .Lexpand_bad
    sb t3, 0(t2)
    add t4, t4, t3
    addi t1, t1, 1
    addi t2, t2, 1
    addi t0, t0, -1
    bnez t0, .Lexpand_o
    la t0, mod3_lut
    add t0, t0, t4
    lbu t4, 0(t0)
    beqz t4, .Lexpand_zero
    sub t4, t5, t4
.Lexpand_zero:
    sb t4, 14(a1)
    sb zero, 15(a1)
    li a0, 1
    ret
.Lexpand_bad:
    li a0, 0
    ret

/* Aligned work-state copy: four words replace sixteen byte iterations. */
work_copy:
    lw t0, 0(a0)
    lw t1, 4(a0)
    lw t2, 8(a0)
    lw t3, 12(a0)
    sw t0, 0(a1)
    sw t1, 4(a1)
    sw t2, 8(a1)
    sw t3, 12(a1)
    ret

/* a0=source, a1=move, a2=destination. Never overwrite the source. */
state_move:
    slli t0, a1, 3
    la t1, n2_b8_move_src
    la t2, n2_b8_move_delta
    add t1, t1, t0
    add t2, t2, t0
    li t0, 0
.Lmove_loop:
    lbu t3, 0(t1)
    add t3, a0, t3
    lbu t4, 0(t3)
    add t5, a2, t0
    sb t4, 0(t5)
    lbu t4, 8(t3)
    lbu t3, 0(t2)
    add t4, t4, t3
    addi t3, t4, -3
    bltz t3, .Lmove_reduced
    mv t4, t3
.Lmove_reduced:
    sb t4, 8(t5)
    addi t1, t1, 1
    addi t2, t2, 1
    addi t0, t0, 1
    li t3, 8
    bltu t0, t3, .Lmove_loop
    ret

n2_apply_move:
    li t0, 9
    bgeu a1, t0, .Lapply_bad_leaf
    addi sp, sp, -32
    sw ra, 28(sp)
    sw s0, 24(sp)
    sw s1, 20(sp)
    mv s0, a0
    mv s1, a1
    mv a1, sp
    call expand_public
    beqz a0, .Lapply_bad
    /* Emit the 13 public bytes directly from the validated work state.
     * This removes the second WorkState and the compress pass. */
    slli t0, s1, 3
    la t1, n2_b8_move_src
    la t2, n2_b8_move_delta
    add t1, t1, t0
    add t2, t2, t0
    li t0, 0
.Lapply_compress:
    lbu t3, 0(t1)
    add t3, sp, t3
    lbu t4, 0(t3)
    add t5, s0, t0
    sb t4, 0(t5)
    li t6, 6
    bgeu t0, t6, .Lapply_next
    lbu t4, 8(t3)
    lbu t3, 0(t2)
    add t4, t4, t3
    addi t3, t4, -3
    bltz t3, .Lapply_ori
    mv t4, t3
.Lapply_ori:
    sb t4, 7(t5)
.Lapply_next:
    addi t1, t1, 1
    addi t2, t2, 1
    addi t0, t0, 1
    li t3, 7
    bltu t0, t3, .Lapply_compress
    li a0, 1
    j .Lapply_return
.Lapply_bad:
    li a0, 0
.Lapply_return:
    lw s1, 20(sp)
    lw s0, 24(sp)
    lw ra, 28(sp)
    addi sp, sp, 32
    ret
.Lapply_bad_leaf:
    li a0, 0
    ret

/* a1 is preserved so a common quotient returns its permutation frame. */
ori_rank_after_sym:
    la t0, n2_b8_sym_inv
    add t0, t0, a1
    lbu t0, 0(t0)
    slli t0, t0, 3
    la t1, n2_b8_sym_pos
    add t1, t1, t0
    slli t0, a1, 6
    slli t2, t0, 1
    add t0, t0, t2
    la t2, n2_b8_sym_twist
    add t2, t2, t0
    li t0, 0
    li t6, 6
.Lori_loop:
    lbu t3, 0(t1)
    add t4, a0, t3
    lbu t5, 0(t4)
    slli t3, t3, 3
    add t3, t3, t5
    slli t5, t3, 1
    add t3, t3, t5
    lbu t4, 8(t4)
    add t3, t3, t4
    add t3, t2, t3
    lbu t3, 0(t3)
    slli t4, t0, 1
    add t0, t0, t4
    add t0, t0, t3
    addi t1, t1, 1
    addi t6, t6, -1
    bnez t6, .Lori_loop
    mv a0, t0
    ret

symmetry_apply:
    slli t0, a1, 3
    la t1, n2_b8_sym_pos
    add t1, t1, t0
    slli t0, a1, 6
    slli t2, t0, 1
    add t0, t0, t2
    la t2, n2_b8_sym_twist
    add t2, t2, t0
    li a3, 0
.Lsym_loop:
    add t0, t1, a3
    lbu t3, 0(t0)
    add t3, a2, t3
    add t0, a0, a3
    lbu t4, 0(t0)
    add t5, t1, t4
    lbu t5, 0(t5)
    sb t5, 0(t3)
    slli t5, a3, 3
    add t5, t5, t4
    slli t6, t5, 1
    add t5, t5, t6
    lbu t4, 8(t0)
    add t5, t5, t4
    add t5, t2, t5
    lbu t5, 0(t5)
    sb t5, 8(t3)
    addi a3, a3, 1
    li t0, 8
    bltu a3, t0, .Lsym_loop
    ret

compact_T:
    addi sp, sp, -48
    sw s0, 12(sp)
    sw s1, 16(sp)
    sw s2, 20(sp)
    sw s3, 24(sp)
    sw s4, 28(sp)
    sw s5, 32(sp)
    sw s6, 36(sp)
    sw s7, 40(sp)
    sw s8, 44(sp)
    mv s0, a0
    mv s1, a1
    li t0, 0
    li t2, 6
.LT_find:
    add t1, s0, t0
    lbu t3, 0(t1)
    beq t3, t2, .LT_found
    addi t0, t0, 1
    j .LT_find
.LT_found:
    lbu t1, 8(t1)
    slli s4, t0, 1
    add s4, s4, t0
    add s4, s4, t1
    la t1, h48_t_dst
    add t1, t1, s4
    lbu t1, 0(t1)
    andi s5, t1, 7
    srli s6, t1, 3
    la s2, t_remtab
    slli t1, t0, 1
    add t1, t1, t0
    slli t1, t1, 1
    add s2, s2, t1
    la s3, t_remtab
    slli t1, s5, 1
    add t1, t1, s5
    slli t1, t1, 1
    add s3, s3, t1
    li t0, 7
    sb t0, 7(s1)
    la t1, h48_t_perm_R
    slli t0, s4, 1
    add t0, t0, s4
    slli t0, t0, 1
    add t1, t1, t0
    li t0, 0
.LT_perm:
    add t2, t1, t0
    lbu t2, 0(t2)
    add t2, s2, t2
    lbu t2, 0(t2)
    add t2, s0, t2
    lbu t2, 0(t2)
    xori t2, t2, 1
    add t3, s3, t0
    lbu t3, 0(t3)
    add t3, s1, t3
    sb t2, 0(t3)
    addi t0, t0, 1
    li t2, 6
    bltu t0, t2, .LT_perm
    add t0, s1, s5
    li t1, 6
    sb t1, 0(t0)
    sb s6, 8(t0)
    sb zero, 15(s1)
    li t0, 0
    li s7, 0
.LT_y:
    add t1, s2, t0
    lbu t1, 0(t1)
    add t1, s0, t1
    lbu t1, 8(t1)
    add t2, sp, t0
    sb t1, 0(t2)
    add s7, s7, t1
    addi t0, t0, 1
    li t1, 5
    bltu t0, t1, .LT_y
    la t0, h48_t_ori_ctl
    slli t1, s4, 2
    add t0, t0, t1
    lw s8, 0(t0)
    mv s4, s6
    li t0, 0
    la t6, mod3_lut
.LT_ori:
    andi t1, s8, 31
    andi t2, t1, 7
    li t3, 7
    beq t2, t3, .LT_sumy
    add t2, sp, t2
    lbu t2, 0(t2)
    slli t2, t2, 1
    j .LT_term
.LT_sumy:
    mv t2, s7
.LT_term:
    srli t1, t1, 3
    add t1, t1, t2
    add t1, t6, t1
    lbu t1, 0(t1)
    add t2, s3, t0
    lbu t2, 0(t2)
    add t2, s1, t2
    sb t1, 8(t2)
    add s4, s4, t1
    srli s8, s8, 5
    addi t0, t0, 1
    li t1, 5
    bltu t0, t1, .LT_ori
    add t0, t6, s4
    lbu t0, 0(t0)
    beqz t0, .LT_last
    li t1, 3
    sub t0, t1, t0
.LT_last:
    lbu t1, 5(s3)
    add t1, s1, t1
    sb t0, 8(t1)
    lw s0, 12(sp)
    lw s1, 16(sp)
    lw s2, 20(sp)
    lw s3, 24(sp)
    lw s4, 28(sp)
    lw s5, 32(sp)
    lw s6, 36(sp)
    lw s7, 40(sp)
    lw s8, 44(sp)
    addi sp, sp, 48
    ret

popcount32:
    srli t0, a0, 1
    li t1, 0x55555555
    and t0, t0, t1
    sub a0, a0, t0
    li t1, 0x33333333
    and t0, a0, t1
    srli a0, a0, 2
    and a0, a0, t1
    add a0, a0, t0
    srli t0, a0, 4
    add a0, a0, t0
    li t1, 0x0f0f0f0f
    and a0, a0, t1
    srli t0, a0, 8
    add a0, a0, t0
    srli t0, a0, 16
    add a0, a0, t0
    andi a0, a0, 63
    ret
mask_rank:
    addi sp, sp, -32
    sw ra, 28(sp)
    sw s0, 24(sp)
    sw s1, 20(sp)
    sw s2, 16(sp)
    sw s3, 12(sp)
    sw s4, 8(sp)
    mv s0, a0
    andi s1, a1, 31
    srli s2, a1, 5
    li s3, 0
    li s4, 0
.Lmask_loop:
    bgeu s4, s2, .Lmask_tail
    lw a0, 0(s0)
    call popcount32
    add s3, s3, a0
    addi s0, s0, 4
    addi s4, s4, 1
    j .Lmask_loop
.Lmask_tail:
    beqz s1, .Lmask_done
    li t0, 1
    sll t0, t0, s1
    addi t0, t0, -1
    lw a0, 0(s0)
    and a0, a0, t0
    call popcount32
    add s3, s3, a0
.Lmask_done:
    mv a0, s3
    lw s4, 8(sp)
    lw s3, 12(sp)
    lw s2, 16(sp)
    lw s1, 20(sp)
    lw s0, 24(sp)
    lw ra, 28(sp)
    addi sp, sp, 32
    ret

/* Return (qidx, permutation symmetry, stabilizer symmetry) in a0..a2. */
quotient_rank_from_meta:
    addi sp, sp, -64
    sw ra, 60(sp)
    sw s0, 56(sp)
    sw s1, 52(sp)
    sw s2, 48(sp)
    sw s3, 44(sp)
    sw s4, 40(sp)
    sw s5, 36(sp)
    sw s6, 32(sp)
    sw s7, 28(sp)
    mv s0, a0
    andi s1, a1, 7
    srli s2, a1, 3
    li t0, 814
    bgeu s2, t0, .Lquot_exception
    mv a1, s1
    call ori_rank_after_sym
    la t0, h48_common_base
    slli t1, s2, 2
    add t0, t0, t1
    lw t0, 0(t0)
    add a0, a0, t0
    li a2, 0
    j .Lquot_return
.Lquot_exception:
    addi s2, s2, -814
    la t0, n2_b8_exc_aid
    srli t1, s2, 1
    add t0, t0, t1
    lbu s3, 0(t0)
    andi t1, s2, 1
    beqz t1, .Lquot_low
    srli s3, s3, 4
.Lquot_low:
    andi s3, s3, 15
    la t0, stabilizer_masks
    add t0, t0, s3
    lbu s4, 0(t0)
    mv a0, s0
    mv a1, s1
    mv a2, sp
    call symmetry_apply
    li s5, 65535
    li s6, 0
    li s7, 0
.Lquot_stab:
    li t0, 1
    sll t0, t0, s7
    and t0, t0, s4
    beqz t0, .Lquot_next
    mv a0, sp
    mv a1, s7
    call ori_rank_after_sym
    bgeu a0, s5, .Lquot_next
    mv s5, a0
    mv s6, s7
.Lquot_next:
    addi s7, s7, 1
    li t0, 6
    bltu s7, t0, .Lquot_stab
    la t0, action_offset
    slli t1, s3, 1
    add t0, t0, t1
    lhu t0, 0(t0)
    slli t0, t0, 2
    la a0, n2_b8_action_mask
    add a0, a0, t0
    mv a1, s5
    call mask_rank
    la t0, h48_exc_base
    slli t1, s2, 2
    add t0, t0, t1
    lw t0, 0(t0)
    add a0, a0, t0
    mv a2, s6
.Lquot_return:
    mv a1, s1
    lw s7, 28(sp)
    lw s6, 32(sp)
    lw s5, 36(sp)
    lw s4, 40(sp)
    lw s3, 44(sp)
    lw s2, 48(sp)
    lw s1, 52(sp)
    lw s0, 56(sp)
    lw ra, 60(sp)
    addi sp, sp, 64
    ret

.macro MAKE_REP src, sym, dst
    addi a0, sp, \src
    li a1, \sym
    addi a2, sp, 128
    call symmetry_apply
    addi a0, sp, 128
    addi a1, sp, \dst
    call compact_T
.endm
/* a0=state, a1=known permutation metadata, a2=8-byte result. */
h48_canonicalize:
    addi sp, sp, -192
    sw ra, 188(sp)
    sw s0, 184(sp)
    sw s1, 180(sp)
    sw s2, 176(sp)
    sw s3, 172(sp)
    sw s4, 168(sp)
    mv s0, a0
    mv s1, a2
    sh a1, 144(sp)
    li t0, -1
    sw t0, 0(s1)
    sw zero, 4(s1)
    mv a1, sp
    call work_copy
    mv a0, s0
    addi a1, sp, 16
    call compact_T
    MAKE_REP 0,1,32
    MAKE_REP 0,3,48
    MAKE_REP 16,1,64
    MAKE_REP 16,3,80
    MAKE_REP 32,3,96
    MAKE_REP 64,3,112
    lhu t0, 144(sp)
    srli s3, t0, 3
    li s4, 1
.Lcanon_meta:
    slli t0, s4, 4
    add a0, sp, t0
    call perm_rank7
    slli a0, a0, 1
    la t0, n2_b8_pmeta
    add t0, t0, a0
    lhu t0, 0(t0)
    slli t1, s4, 1
    add t1, sp, t1
    sh t0, 144(t1)
    srli t0, t0, 3
    bgeu t0, s3, .Lcanon_meta_next
    mv s3, t0
.Lcanon_meta_next:
    addi s4, s4, 1
    li t0, 8
    bltu s4, t0, .Lcanon_meta
    li s4, 0
.Lcanon_choose:
    slli t0, s4, 1
    add t0, sp, t0
    lhu a1, 144(t0)
    srli t0, a1, 3
    bne t0, s3, .Lcanon_choose_next
    slli t0, s4, 4
    add a0, sp, t0
    call quotient_rank_from_meta
    lw t0, 0(s1)
    bgeu a0, t0, .Lcanon_choose_next
    sw a0, 0(s1)
    sb s4, 4(s1)
    sb a1, 5(s1)
    sb a2, 6(s1)
.Lcanon_choose_next:
    addi s4, s4, 1
    li t0, 8
    bltu s4, t0, .Lcanon_choose
    lw s4, 168(sp)
    lw s3, 172(sp)
    lw s2, 176(sp)
    lw s1, 180(sp)
    lw s0, 184(sp)
    lw ra, 188(sp)
    addi sp, sp, 192
    ret

t_sigma_code:
    addi sp, sp, -16
    sw ra, 12(sp)
    sw s0, 8(sp)
    mv s0, a0
    call perm_rank7
    li t0, 0
    li t2, 6
.Lsigma_find:
    add t1, s0, t0
    lbu t3, 0(t1)
    beq t3, t2, .Lsigma_found
    addi t0, t0, 1
    j .Lsigma_find
.Lsigma_found:
    lbu t1, 8(t1)
    slli t0, a0, 1
    add t0, t0, a0
    add t0, t0, t1
    slli t1, t0, 1
    add t0, t0, t1
    srli t2, t0, 3
    andi t0, t0, 7
    la t1, h48_sigma_pr_3bit
    add t1, t1, t2
    lbu a0, 0(t1)
    lbu t2, 1(t1)
    slli t2, t2, 8
    or a0, a0, t2
    srl a0, a0, t0
    andi a0, a0, 7
    lw s0, 8(sp)
    lw ra, 12(sp)
    addi sp, sp, 16
    ret

/* Pull only the selected move back through the recorded frames. */
lift_policy_move:
    addi sp, sp, -80
    sw ra, 76(sp)
    sw s0, 72(sp)
    sw s1, 68(sp)
    sw s2, 64(sp)
    sw s3, 60(sp)
    sw s4, 56(sp)
    sw s5, 52(sp)
    sw s6, 48(sp)
    mv s0, a0
    mv s6, a1
    mv s4, a2
    lbu t0, 4(s6)
    la t1, h48_len
    add t1, t1, t0
    lbu s2, 0(t1)
    slli t1, t0, 2
    add t0, t0, t1
    la s1, h48_word
    add s1, s1, t0
    li s3, 0
.Llift_record:
    bgeu s3, s2, .Llift_frames
    add t0, s1, s3
    lbu s5, 0(t0)
    mv a0, s0
    li t0, 6
    bne s5, t0, .Llift_simple_code
    call t_sigma_code
    addi a0, a0, 6
    j .Llift_store_code
.Llift_simple_code:
    mv a0, s5
.Llift_store_code:
    add t0, sp, s3
    sb a0, 0(t0)
    addi t0, s3, 1
    bgeu t0, s2, .Llift_record_next
    andi t0, s3, 1
    slli t0, t0, 4
    addi t0, t0, 16
    add a2, sp, t0
    sw a2, 8(sp)
    mv a0, s0
    li t0, 6
    bne s5, t0, .Llift_sym
    mv a1, a2
    call compact_T
    j .Llift_state_done
.Llift_sym:
    mv a1, s5
    call symmetry_apply
.Llift_state_done:
    lw s0, 8(sp)
.Llift_record_next:
    addi s3, s3, 1
    j .Llift_record
.Llift_frames:
    la t6, move_pullback
    lbu t0, 6(s6)
    slli t1, t0, 3
    add t0, t0, t1
    add t0, t0, s4
    add t0, t6, t0
    lbu s4, 0(t0)
    lbu t0, 5(s6)
    slli t1, t0, 3
    add t0, t0, t1
    add t0, t0, s4
    add t0, t6, t0
    lbu s4, 0(t0)
.Llift_reverse:
    beqz s2, .Llift_return
    addi s2, s2, -1
    add t0, sp, s2
    lbu t0, 0(t0)
    slli t1, t0, 3
    add t0, t0, t1
    add t0, t0, s4
    add t0, t6, t0
    lbu s4, 0(t0)
    j .Llift_reverse
.Llift_return:
    mv a0, s4
    lw s6, 48(sp)
    lw s5, 52(sp)
    lw s4, 56(sp)
    lw s3, 60(sp)
    lw s2, 64(sp)
    lw s1, 68(sp)
    lw s0, 72(sp)
    lw ra, 76(sp)
    addi sp, sp, 80
    ret

/* Original perfect hash, followed by rank of its occupied slot. */
policy_lookup:
    addi sp, sp, -32
    sw ra, 28(sp)
    sw s0, 24(sp)
    sw s1, 20(sp)
    sw s2, 16(sp)
    sw s3, 12(sp)
    srli t0, a0, 13
    slli t1, a0, 7
    xor t0, t0, a0
    xor t0, t0, t1
    li t1, 16383
    and t0, t0, t1
    la t1, h48_policy_disp
    add t0, t0, t1
    lbu t0, 0(t0)
    srli t1, a0, 7
    slli t2, a0, 9
    xor t1, t1, a0
    xor t1, t1, t2
    srli t2, t1, 5
    xor t1, t1, t2
    srli t1, t1, 2
    add t0, t0, t1
    li t1, 131071
    and t0, t0, t1
    andi s3, t0, 31
    srli t1, t0, 9
    slli t2, t1, 2
    la t3, h48_policy_prefix
    add t2, t2, t3
    lw s2, 0(t2)
    la t3, h48_policy_used
    slli t1, t1, 6
    add s1, t3, t1
    srli t0, t0, 5
    slli t0, t0, 2
    add s0, t3, t0
.Lpolicy_words:
    bgeu s1, s0, .Lpolicy_partial
    lw a0, 0(s1)
    call popcount32
    add s2, s2, a0
    addi s1, s1, 4
    j .Lpolicy_words
.Lpolicy_partial:
    beqz s3, .Lpolicy_dense
    li t0, 1
    sll t0, t0, s3
    addi t0, t0, -1
    lw a0, 0(s0)
    and a0, a0, t0
    call popcount32
    add s2, s2, a0
.Lpolicy_dense:
    srli t0, s2, 1
    la t1, h48_policy_dense
    add t0, t0, t1
    lbu a0, 0(t0)
    andi t0, s2, 1
    beqz t0, .Lpolicy_low
    srli a0, a0, 4
.Lpolicy_low:
    andi a0, a0, 15
    lw s3, 12(sp)
    lw s2, 16(sp)
    lw s1, 20(sp)
    lw s0, 24(sp)
    lw ra, 28(sp)
    addi sp, sp, 32
    ret

work_solved:
    li t0, 0
.Lwork_solved_loop:
    add t1, a0, t0
    lbu t2, 0(t1)
    bne t2, t0, .Lwork_not_solved
    lbu t2, 8(t1)
    bnez t2, .Lwork_not_solved
    addi t0, t0, 1
    li t1, 7
    bltu t0, t1, .Lwork_solved_loop
    li a0, 1
    ret
.Lwork_not_solved:
    li a0, 0
    ret

n2_solve:
    beqz a0, .Lsolve_bad_leaf
    beqz a1, .Lsolve_bad_leaf
    beqz a2, .Lsolve_bad_leaf
    /* Solved-state fast path has no stack frame or helper call. */
    li t0, 0
.Lsolve_identity:
    add t1, a0, t0
    lbu t2, 0(t1)
    bne t2, t0, .Lsolve_work
    addi t0, t0, 1
    li t3, 7
    bltu t0, t3, .Lsolve_identity
    li t0, 6
    addi t1, a0, 7
.Lsolve_zero_ori:
    lbu t2, 0(t1)
    bnez t2, .Lsolve_work
    addi t1, t1, 1
    addi t0, t0, -1
    bnez t0, .Lsolve_zero_ori
    sb zero, 0(a2)
    beqz a3, .Lsolve_ok_leaf
    sh zero, 0(a3)
    sb zero, 2(a3)
    sb zero, 3(a3)
.Lsolve_ok_leaf:
    li a0, 1
    ret
.Lsolve_bad_leaf:
    li a0, 0
    ret
.Lsolve_work:
    addi sp, sp, -80
    sw ra, 76(sp)
    sw s0, 72(sp)
    sw s1, 68(sp)
    sw s2, 64(sp)
    sw s3, 60(sp)
    sw s4, 56(sp)
    sw s5, 52(sp)
    sw s6, 48(sp)
    mv s1, a1
    mv s2, a2
    mv s3, a3
    mv s0, sp
    mv a1, sp
    call expand_public
    beqz a0, .Lsolve_bad
    mv a0, sp
    call perm_rank7
    mv s5, a0
    li s4, 0
    li s6, 1
.Lsolve_policy_loop:
    mv a0, s0
    call work_solved
    bnez a0, .Lsolve_success
    li t0, 11
    bgeu s4, t0, .Lsolve_bad
    bnez s6, .Lsolve_first_rank
    mv a0, s0
    call perm_rank7
    mv s5, a0
.Lsolve_first_rank:
    li s6, 0
    slli t0, s5, 1
    la t1, n2_b8_pmeta
    add t0, t1, t0
    lhu a1, 0(t0)
    mv a0, s0
    addi a2, sp, 32
    call h48_canonicalize
    lw a0, 32(sp)
    call policy_lookup
    li t0, 9
    bgeu a0, t0, .Lsolve_bad
    mv a2, a0
    mv a0, s0
    addi a1, sp, 32
    call lift_policy_move
    li t0, 9
    bgeu a0, t0, .Lsolve_bad
    add t0, s1, s4
    sb a0, 0(t0)
    mv a1, a0
    mv a0, s0
    addi a2, sp, 16
    call state_move
    addi a0, sp, 16
    mv a1, s0
    call work_copy
    addi s4, s4, 1
    j .Lsolve_policy_loop
.Lsolve_success:
    sb s4, 0(s2)
    beqz s3, .Lsolve_success_return
    sh zero, 0(s3)
    sb s4, 2(s3)
    sb zero, 3(s3)
.Lsolve_success_return:
    li a0, 1
    j .Lsolve_return
.Lsolve_bad:
    li a0, 0
.Lsolve_return:
    lw s6, 48(sp)
    lw s5, 52(sp)
    lw s4, 56(sp)
    lw s3, 60(sp)
    lw s2, 64(sp)
    lw s1, 68(sp)
    lw s0, 72(sp)
    lw ra, 76(sp)
    addi sp, sp, 80
    ret

.section .rodata
.balign 4
pop7:
.byte 0,1,1,2,1,2,2,3,1,2,2,3,2,3,3,4,1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5
.byte 1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6
.byte 1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6
.byte 2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7
mod3_lut: .byte 0,1,2,0,1,2,0,1,2,0,1,2,0
stabilizer_masks: .byte 1,63,3,3,25,5,5,33,25,63,5,5,3,3
.balign 2
action_offset: .half 0,0,23,46,69,92,115,138,161,184,207,230,253,276
t_remtab:
.byte 1,2,3,4,5,6, 0,2,3,4,5,6, 0,1,3,4,5,6, 0,1,2,4,5,6
.byte 0,1,2,3,5,6, 0,1,2,3,4,6, 0,1,2,3,4,5
move_pullback:
.byte 0,1,2,3,4,5,6,7,8, 2,1,0,8,7,6,5,4,3, 5,4,3,2,1,0,8,7,6
.byte 3,4,5,6,7,8,0,1,2, 6,7,8,0,1,2,3,4,5, 8,7,6,5,4,3,2,1,0
.byte 2,1,0,5,4,3,8,7,6, 2,1,0,8,7,6,5,4,3, 5,4,3,2,1,0,8,7,6
.byte 8,7,6,2,1,0,5,4,3, 5,4,3,8,7,6,2,1,0, 8,7,6,5,4,3,2,1,0
h48_len: .byte 0,1,2,2,3,3,4,5
h48_word:
.byte 0,0,0,0,0, 6,0,0,0,0, 1,6,0,0,0, 3,6,0,0,0
.byte 6,1,6,0,0, 6,3,6,0,0, 1,6,3,6,0, 6,1,6,3,6
