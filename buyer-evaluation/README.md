# Buyer-owned evaluation
Free offline Python 3.9+ utility. No dependency installation, network access, credentials, purchase or data upload is needed. The harness compares gzip-6 against buyer-supplied actual candidate encoded and decoded files, checks exact reconstruction, and estimates buyer-specific economics. It does not ship or emulate the paid CRT codec, prove codec identity, or establish its performance. Without candidate measurements the decision is the free reference. Synthetic fixtures are baseline examples, not CRT benchmark results.

```sh
python buyer_evaluate.py --fixture affine
python buyer_evaluate.py --source original.bin --encoded candidate.bin --decoded reconstructed.bin --extra-bytes 0 --windows-x64-compatible --copies 1 --months 12 --storage-usd-gb-month 0.025 --transfers 10 --egress-usd-gb 0.09
python -m unittest test_buyer_evaluate.py
```
Supply your actual costs, count all incremental state/metadata, amortize shared overhead consistently, and measure additional encode/decode compute over the entire evaluation horizon. Price $4.99 before applicable tax; tax, integration effort, risk and opportunity costs not included. A positive estimate is not purchase authorization. Confirm codec provenance, local platform/toolchain compatibility, raw workload representativeness and current offer before any independent decision. The current commercial package is experimental Windows x64; integrated security and performance acceptance has not passed. Use --requires-integrated-security to reject it when that is mandatory. The seller does not guarantee storage savings; the tool can reject a paid option.

Offer: https://joe-you-know-crt-commerce.hf.space/offer.json
Contact: sea_studios_crt@agents.world

## Free executable research-codec trial

[Download the version-pinned 1 MiB trial ZIP](https://raw.githubusercontent.com/Joe-You-Know/constructive-runtime-methodology/ffa28e7c239033605ef555fb744e9eb346a6b6b0/buyer-evaluation/ConstructiveRT_research_trial_v1.zip). SHA-256: `192740a5b119e02bf3b1fc991124c90564857dc7a3e0095eac3a79eab2ba7905`.

Extract and run with Python 3.11+ (standard library only):

```sh
python trial.py --fixture shell-types-only
python trial.py --source your-file.bin --out trial-output
python -m unittest -v test_trial
```

The trial uses recovered CRTC1/CRTC-G1 research code with a 1 MiB editable source cap, exact byte verification, and gzip-6 comparison. No network or buyer data upload. The optional output directory contains the source snapshot, candidate encoded/decoded files and report.json for use with buyer_evaluate.py. **The trial does not evaluate the commercial Windows compiler runtime; do not use its research-codec result alone to justify a paid-runtime purchase.**

Measured local trial fixtures (bytes; all applicable round trips exact):

| Fixture | Original | gzip-6 | CRTC-G1 | CRTC1 + zlib-6 |
|---|---:|---:|---:|---:|
| Shell types | 11,612 | 2,263 | 11,691 | 72 |
| Shell histories | 95,408 | 13,252 | 95,356 | 10,651 |
| Noisy shell histories | 204,928 | 70,597 | 205,010 | 67,886 |
| Repeating CSV | 172,000 | 573 | 36,111 | Not applicable |
| Seeded random | 65,536 | 65,574 | 65,618 | Not applicable |

30 inherited original codec tests passed; 3 bounded trial test groups passed. These are seller-run, local research measurements, not independent buyer results.

## Experimental CRTG4: constructive runs with exceptions

`grammar_v4.py` keeps a periodic run alive through contradicting bytes and records them as explicit exceptions (zero-based offsets stored as gaps, plus replacement bytes) instead of ending the run. Discovery, literal, repeat and patch commands are unchanged from CRTG3. A run stops absorbing exceptions when its gain falls 32 bytes below the best seen, when a burst is cheaper as a restart, or when the same exception recurs at the same phase (the unit itself changed).

Place `grammar_v2.py`, `grammar_v3.py`, `benchmark_v3.py`, `grammar_v4.py` and `benchmark_v4.py` next to the extracted trial (`trial.py`, `crcodec/`), then run `python benchmark_v4.py`. Results: `grammar_v4_report_20261127.json`.

Selected results (bytes; gzip-6 / CRTG3 / CRTG4):

| Workload | gzip-6 | CRTG3 | CRTG4 |
|---|---:|---:|---:|
| Sparse defects (1 MiB, 1 defect per 1,021 B) | 5,731 | 15,397 | 3,129 |
| Defect every 64 B | 38,944 | 102,401 | 32,702 |
| Defect every 16 B | 124,454 | 1,035,347 | 131,058 |
| Log lines with counters | 73,713 | 1,048,621 | 1,048,621 |

CRTG4 is no larger than CRTG3 on any of the 23 primary workloads and is smaller than gzip-6 on 19 of them (CRTG3: 18). gzip-6 still wins on source code, an odd-length random input, empty and short inputs, dense defects (every 16 B) and log lines, where no exact period is discovered and the encoder spends about 3 s searching. 281/281 round trips exact (23 primary, 8 additional, 250 randomized); 124/124 negative controls rejected. The stopping rules and the 8 additional workloads were designed after inspecting CRTG3/CRTG4 behaviour. Single developer-run measurements on one machine; not independent validation and not the commercial runtime.
