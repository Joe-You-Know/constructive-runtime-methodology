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
