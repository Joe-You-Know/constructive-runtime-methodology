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
