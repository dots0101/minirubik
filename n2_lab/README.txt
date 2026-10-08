Balanced H48 N2 Ripes lab — 2026-10-08 (GMT+8)

目前技術入口：docs/teaching_zh.md（完整中文）／docs/teaching_en.md（完整英文，少於100000字元）。
docs/report_en.html 是離線互動pipeline/LED教材；docs/completion_zh.html 是本機完成狀態。
正式要求對照 docs/requirements_audit.md；繳交資訊 docs/submission_record.md；AI及實際過程 docs/development_record.md。
完整交付操作說明：docs/delivery_zh.md。

Verified current results
  All 3674160 host states return exact shortest lengths and replay correctly.
  All 2644 deepest inputs pass individual fresh Ripes ISS runs for both implementations.
  Manual minimum/mean/maximum retired: 61829 / 67174.832 / 84164.
  GCC mean/maximum: 69392.088 / 84114. Manual wins2628, ties0, losses16.
  Official input21345671111111: manual65617, GCC67829 retired.
  CLI .text4776, GCC5052; course static CLI95280 / GUI95364 bytes.
  Complete GUI guest budget104412 bytes: loaded span100912 plus LED3500.
  Reserved stack400bytes manual /512bytes GCC /32bytes pipeline.
  All ELF opcodes RV32I; no undefined helpers, heap, recursion or floating point.

Quick GUI demonstration
  . .\Environment.ps1
  .\Run-Lab.ps1 -Action Gui
Choose 32-bit5-stage processor with forwarding and hazard detection; disable M/C.
Add exactly one LED Matrix, width35 height25, BASE0xf0000000.
Ctrl+O -> Executable(ELF) -> build/solver_gui.elf -> Run.
Expected actual solution: B' R D R B2 R B D2 B D R; PASS cases=1, exit0.
Actual move-buffer replay draws12frames, no stored animation or second framebuffer.

Pipeline microscope
Load build/pipeline_demo.elf. Set Settings Max.pipeline diagram cycles to1000.
Use Auto clock or Clock; FastRun does not preserve full diagram history.
At604detect load-use,605bubble,606WBforward,608add writeback.
Recorded current trace cycles0–616; 514retired /616cycles on5S.

Rebuild / verify / measure
  . .\Environment.ps1
  .\Run-Lab.ps1 -Action Build
  .\Run-Lab.ps1 -Action Check
  .\Run-Lab.ps1 -Action Measure
  .\Run-Lab.ps1 -Action Benchmark
Set N2_PYTHON, N2_RV_GCC, N2_RIPES if needed. Native tests need N2_HOST_CC/N2_HOST_CXX.
Environment.ps1 -InstallGcc can install the pinned verified compiler locally.
Prebuilt ELF GUI runs need only Ripes; the portable pinned archive is supplied.
Regenerate offline HTML: python tools/make_report.py
Check offline JS logic: node tools/check_report.js (DOM stub; not visual browser QA)
Audit frozen delivery: python tools/audit_delivery.py
Only GNU-built ELF is the verified route; flat.s inspection exports are not an alternative execution route.
Host oracles, diagnostics and HTML are not linked into the target. Diagnostic memory tests intentionally exceed production sizes.

The user reports teacher approval of H48. Technical preparation is complete locally.
Public GitHub/HackMD, personal authorship requirements/authorization, true reflection/history, submission accepted email and live interview remain human/external actions.
No accounts, publication, form submission, fake revisions, student authorship or formal acceptance are claimed.
