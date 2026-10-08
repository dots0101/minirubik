# Actual development and AI-use record

This record describes what happened in this Codex workspace. It is not a student-authored reflection and does not certify three student revisions.

## Preserved inputs

The October 5 original/v2 project archives and the October 6 engineering package remain separate from the current deliverable. The pre-integration code, notes, tools and evidence were retained under `work/legacy_20261006/`; `outputs/N2_RIPES_LAB_20261006.zip` remains unchanged.

The latest user-supplied balanced archive is `RUBIK_N2_H48_BALANCED_RECOMMENDED_CODEX_20261007.zip`, SHA-256 `7f3b4717a6be003a3b7b0641ec17ed4d606173bc1ab6b37b2441440f01309520`. Its `n2_solver.c` was copied unchanged: SHA-256 `8d356669f07a7d872f7a9a22322db60fc2630bd075fe41297842356df5bc67cc`.

## User decisions supported by the conversation

The user selected the supplied balanced version after considering time, space and implementation cost. The user clarified that the budget means all required guest memory, and explicitly requested the simplest LED implementation. The user reported receiving instructor approval for the H48 exact-policy method and instructed the agent to finish that version. The user requested English notes within 100,000 characters plus complete Chinese teaching material. These statements do not establish who authored the original solver or independently measured it.

## Engineering performed by Codex

The earlier sparse whole-path lookup was removed. RV32I code was ported to the dense bitmap/prefix rank policy and three-bit T sigma, preserving the supplied hash. The rank parity and sigma guard-byte edge cases were verified exhaustively. Stack reservation was made contiguous and conservative; the renderer became a zero-frame leaf with no additional framebuffer, snapshots, counter or delay loop. LED constants total 84 bytes. Linked code, all static sections, padding, stack and 3500 bytes of MMIO storage are included in the 104412-byte GUI budget.

The signed EXPECTED-byte fix permits 255 to mean unknown distance. Twelve actual Ripes runs validate that mode. All known vectors and all 2644 deepest cases were rerun on the linked programs. Host certificates independently establish distances, table integrity, symmetry structure, lifting, packing and end-to-end optimality. All sixteen manual losses are retained and profiled; none is hidden by replacing the comparison set.

The GUI pipeline trace was exported with sufficient history for 0–616 cycles. Every instruction row was matched to current machine code; the production lookup was extracted exactly rather than copied into a different demo algorithm. The new load-use event is 604 detection, 605 bubble, 606 forwarding, 608 add writeback. The offline viewer explains controls from pinned model wiring and labels that distinction explicitly. Actual renderer execution is checked against independent geometric expectations for every pixel and frame.

## Corrections and discarded artifacts

Old documentation treated static tables as the whole budget, showed a 59-cycle demo, described the sparse path shortcut as current, and reported the former official solution. Those materials have been moved out of the active project or replaced with current notes. The generated-table payload is 94729 bytes; the supplied C's larger static figure includes helper constants and is not the ELF total. Unused old RISC-V binaries/linker files and sparse rebuild scripts were archived rather than presented as current options. No rejected direct flat-assembly route is counted as passing.

An attempted native UI refresh was rejected by automatic approval review because of an earlier user Escape stop. Existing GUI screenshots and actual trace are retained, current CLI and independent execution supply the refreshed verification, and no new live-port screenshot is fabricated.

## Measurements and scope

The original supplied measurement files describe their own environment and are not reused as this machine's measurements. Current raw Ripes JSON/CSV/logs, native logs, compiler/image hashes, environment experiment and microbenchmarks are in evidence/. Host-only tools and oracles do not inflate the guest's linked footprint and are clearly labeled. Different models, renderer settings and compiler inlining are not combined into a spurious speed claim.

October 6 versus October 8 values use different algorithms. They document a genuine redesign, not a like-for-like assembly optimization series. Current manual versus GCC comparison does use the same supplied final C algorithm, tables, input, driver, compiler flags and renderer setting. The local record and original packages offer honest offline process evidence; if a formal assessor needs further student revisions or a supervised explanation, the student must provide them.

## Material AI-use log

| Task | Portion affected | Disposition |
|---|---|---|
| Integration and assembly | target RV32I port, driver, renderer, linker and build tools | Generated/edited by Codex; not claimed as student-authored |
| Verification | host/API/LED/trace checks, Ripes measurement orchestration | Agent-run; raw logs retained; student-independent measurements not invented |
| Documentation | mathematical/engineering synthesis, Chinese translation, English wording, tables and HTML | AI-written reference material, sources checked separately |
| Source review | course requirements and linked documentation | Retrieved/reviewed by agent, access failures listed |
| Student choices | supplied balanced version, whole-space contract, minimal renderer, reported method approval | Directly evidenced in user messages |
| Public submission and reflection | GitHub/HackMD/form/interview, personal reflection | Not performed or fabricated |

The assignment separately reserves state representation, search design/admissibility, every reported measurement, optimization reasoning, RV32I assembly and note analysis to the student. Disclosure alone does not waive that restriction. Instructor approval of H48 addresses the method, not automatically this distinct authorship requirement. The student should use this material to understand and verify the implementation, then complete the required work or obtain specific additional authorization.

## Reflection prompts for the student

Write your own account of what you understood, changed, measured and rejected; identify which parts came from the supplied package and which from this agent. Explain one actual bug, one memory/time tradeoff, and why a distance-preserving symmetry still needs move lifting. Report thin or offline history honestly. Do not replace this section with a fabricated first-person development narrative.

## Actual fork and initial clone — 2026-10-08

The user created the public dots0101/minirubik fork and performed the local clone. They reported starting SHA `231796cc48868f4ea276f652139b6bebbad0cd02`; GitHub public metadata and local read-only Git checks confirmed parent=sysprog21/minirubik, branch main, this HEAD and a clean working tree. Baseline C is identical after checkout line-ending normalization. Fork metadata has been inserted into the teaching notes and submission record. No import commit, pushed assignment tag or accepted submission is claimed at this point.

## Git byte preservation — 2026-10-08

Before the first assignment commit, Codex found that the raw GUI TSV and measurement JSON contain CRLF bytes. Git normalization would change the saved trace hash. A scoped `.gitattributes` containing `* -text` now preserves every delivered file on add and checkout. Publish-Package.ps1 includes that file for future imports. Read-only check-attr and filtered-versus-raw hash-object checks confirmed no conversion of the saved GUI trace. This preparation did not stage, commit or push the user's repository.
