# Current balanced verification tools

These are host-only programs, never linked into the RV32I target. Run the complete suite from the lab root with `Run-Lab.ps1 -Action Check`, using native GCC/G++, Python3 and the pinned Ripes/GNU compiler.

| Tool | Complete check |
|---|---|
| check_distance_certificate.c |3674160 states,33067440 edges, unique root, edge distance bounds, descending neighbors, diameter11 |
| verify_structure.c | Root-fixing A/B/T graph automorphisms, H48 group, eight cosets,77802 orbits, every policy descent |
| verify_tables.c | S3/quotient metadata, masks, local move maps, exception table, collision-free policy slots |
| verify_affine.py |21 T affine inverse identities |
| verify_packed.c | All77802 policy values against preserved unpacked slot data;15120 sigma codes;bitmap/prefix;parities/offsets |
| test_adapter.c |5040 permutation and729 orientation components under all9 moves |
| test_api.c | Native public API contracts and invalid inputs |
| rv32_verify.cpp | Independent RV32 API/ABI,6859 calls;all2644 d11;1281 stratified |
| trace_examples.c | Generic six-step and official eleven-step canonicalization/lifting traces |

Python tools/verify_led.py separately executes current production renderer using tools/rv32_trace.py and compares4331 MMIO stores/12frames with independently derived geometry. tools/profile_losses.py uses dynamic PC attribution for every manual loss and reconciles the one-count pinned ISS finalization offset. Neither host interpreter is called Ripes in the report.

Raw successful outputs are in evidence/. The original full-domain distance array remains in reference/host_oracle/. The independent unpacked payload binaries here are host references, not an expanded runtime policy. Old sparse-path rebuilders and their Bash entry points were archived outside the current package.
