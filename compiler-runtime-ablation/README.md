# CRT v1.5.0 monitoring-only ablation (CRT151), 2026-11-27

This ablation answers whether the fragment-build penalty in the published CRT1411 paired Windows experiment is caused by the debug-event execution monitor. It concerns the experimental Windows compiler runtime only; the research codec is not involved.

## Design
One `Session` and the same 120 independently rooted revisions (6/8/9/10/11/12 changed groups × 20). Each revision is built **whole** and **fragment** by three arms, each arm with its own in-memory cache:

| Arm | Compiler identity | Debug-event monitor |
|---|---|---|
| `rehash` | rehash compiler executable every build | off |
| `pinned` | session file pins: compiler + all 138 policy files + gate + policy | off |
| `monitored` | the **same** pins | **on** (gated launch, staged read-locked source) |

`monitored − pinned` changes only the monitoring step. Arm order rotates through all six permutations by revision, so each pairwise order occurs in 60 of the 120 revisions. Every contrast is also reported split by which arm ran first.

Machine and toolchain: the same Windows PC and anchors as the published CRT1411 run. Snapshot Clang 19.1.5 (`20a8e84f…`), MSVC `link.exe` 14.44.35207 (`a364af80…`), scoped policy of 138 files. The drivers were compiled with Visual Studio's bundled clang++ 19.1.5.

## Results (median paired difference, ms; 120 pairs each)

| Contrast | Whole | Fragment |
|---|---:|---:|
| monitored − pinned (wall) | +173.2 (120/120 > 0) | +860.7 (120/120 > 0) |
| ↳ compile | +91.8 | +784.8 |
| ↳ link | +81.4 | +80.5 |
| rehash − pinned (wall) | +325.6 | +332.2 |
| ↳ identity check | +328.2 | +328.3 |
| rehash − monitored (wall), the published contrast | +152.7 (published +174.6) | −531.2 (published −469.6) |

- Monitor compile cost per fragment build is 84.1 ms per compiled group (least squares; per-size medians 82.3–84.0 ms from 6 to 12 groups). The monitor costs roughly 82 ms per monitored tool launch.
- Order effect: fragment monitor cost 860.7 ms (monitored first) vs 863.4 ms (pinned first); whole 172.6 vs 173.5 ms.
- 720/720 output executables independently verified against their source (34,816 native calls each). 87,914 monitor events, no rejection.

**Interpretation:** the fragment penalty is the monitor's per-launch overhead. Fragment builds launch 7–13 tools, which outweighs the fixed ~328 ms identity-rehash saving. The implied break-even of about 3–4 launches is a prediction, not a measurement.

## Limits
- One machine, one synthetic fixture, single run, no independent replication.
- **Peak memory is not comparable across arms.** `launched_peak_kib` is the directly launched process: the compiler or linker for `rehash`/`pinned`, but the gate for `monitored`.
- `security_acceptance_met: false`. This is a timing ablation, not a security evaluation.
- The 13 MB monitor event log is not included. It is available on request.

## Reproduce
Place these files into an extracted v1.5.0 kit (`src/` and the kit root), then from that root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_ablation_windows.ps1 -Snapshot <disposable LLVM snapshot> -ExternalDependency <VS Setup Configuration DLL> -ApprovedDependencies .\approved_dependencies.tsv -Trials 20
```

The linker path and SHA default to the original machine's. Supply your own with `-Linker` and `-TrustedLinkerSha`. `-HostClang` sets the compiler used to build the drivers.

SHA-256 of the files as served from this repository: `ablation_20261127.json` 4f5e2102dd03771c3f1fd7483f4b503f79adae27a3eefc2579e2b36b8ec56411 (LF line endings; the run machine's original CRLF file is ce35455a37b34e84c9168b581a7aabe606e4b95603ed859abdfdce88e0c6a1e2, with identical content) · `crt151_monitor_ablation.cpp` 563d4a2b2f6555497825a9310c109e3b7a14d06a07d3c2daff4cd8314f615924 · `ablation_report.py` 0c5736cf22243edaccb372501667c9f40493bef24826be2b0fab259a63b08c2b · `run_ablation_windows.ps1` 5f961397bbf916265e0c8887be90c3d9027693bfbadac5548bd6dbd17cfcb9dc
