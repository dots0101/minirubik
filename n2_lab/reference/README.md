# Balanced supplied C reference

`n2_solver.c` is copied unchanged from the user-supplied October 7 balanced archive: SHA-256 `8d356669f07a7d872f7a9a22322db60fc2630bd075fe41297842356df5bc67cc`. Five generated table C files are linked with it for the GCC reference and with authored assembly for the manual target. The source archive hash and method approval reported by the user are in evidence/integration.json.

The balanced lookup uses displacement, used bitmap, per-512-slot prefix and dense policy nibbles, plus three-bit T sigma with one guard byte. No sparse complete-path shortcut remains. Generated table symbols total94729 bytes; this is not the linked program footprint.

`host_oracle/full_distance.bin` and upstream_solver.c are host-only correctness references. They are never linked into the guest. Native tests validate exact distances and replay over all3674160 states. GNU target builds are controlled by tools/build.py and target/rv32.ld; no old prebuilt target in this directory is an execution route.

Use Run-Lab.ps1 -Action Check for the complete campaign. The Makefile offers native C tests only; RV32 compilation uses the project build tools so renderer, ABI and complete budget are shared.
