# Constructive Runtime: evaluation methodology

Constructive Runtime (CRT) v1.5.0 is an experimental research implementation for a constrained compiler workflow. This page describes how the claims were measured and how an automated buyer exercise was scored. It does not distribute the full precompiled build.

## What the runtime benchmark measures

The Windows experiment used a fixture of 2,048 fixed-width, independently affine source records in 32 groups. It compared CRT's experimental monitored path against CRT's own per-build compiler-executable rehash path. The local report contains 120 paired trials per mode and records 480 native execution checks. Median rehash-minus-monitored time was +174.5785 ms for whole builds, where monitored was faster in 118/120 trials, and -469.59965 ms for fragment builds, where monitored was faster in 0/120 trials. These observations do not establish a speedup against other compilers or general projects.

Linux results use a different baseline path. Historical Linux reports were produced with Clang 17; their 20-trial component totals omitted repeated compiler hashing, as recorded in the interpretation note. A new GCC 13.3 build on Ubuntu 24.04.5 passed a small functional check, not a performance benchmark. The Linux baseline lacks the experimental Windows v1.5 execution monitor.

The v1.5.0 package has not passed integrated Windows security and performance acceptance. Dependency discovery was observation only. Complete dependency authentication and production hardening are unproven.

## Automated buyer exercise

The buyer test used hypothetical offers: a free reference, experimental CRT, and a synthetic competing offer. It assumed workload size, value of time, prices, performance savings, and authentication requirements. Its deterministic oracle rejected missing evidence and security-ineligible offers, compared positive net value, and otherwise selected the free reference. The original 16-case prompt, corrected-schema 16-case prompt, and preregistered 48-case set are distinct conditions and should be reported separately.

The 48-case set tested four small language models with and without supplied calculator values. In the gated workflow, each of eight model conditions made 48 final choices: 16 free-reference cases were resolved automatically and 32 required model judgment. Across conditions, 209/384 final choices were correct, including all 128 automatic decisions. Among model-required cases, 81/256 model proposals were correct. There were 131 false rejections, 44 wrong paid-offer choices, no false acceptances, and no parser errors. The zero false acceptances reflect this workflow's gate on these constructed cases, not independent model reliability. No transactions or real buyers were observed.

## Current proposed offer

The owner specified a $4.99 one-time price for the precompiled package and a separate, optional $0.99/month update subscription. The [public commerce storefront](https://joe-you-know-crt-commerce.hf.space/) has verified live $4.99 one-time checkout and version-pinned private delivery as of November 27, 2026; consult the live product-status endpoint before any purchase. No independent paid purchase has yet been verified. The optional update subscription is not active. Agents can retrieve [the machine-readable discovery record](./crt-discovery.json) and the [authoritative product-status endpoint](https://joe-you-know-crt-commerce.hf.space/offer.json) without purchasing. The methodology can be read independently of a purchase. The full package was briefly published earlier under Apache License 2.0; existing recipients retain that license's rights. No exclusivity is claimed.

The reproducible case definitions, model inputs, raw job logs, scoring scripts, and detailed reports are retained in the local buyer-evaluation artifacts. Performance and security claims should be checked against the raw benchmark evidence and release notes before use in a purchasing decision.

## Buyer-owned evaluation and direct contact

Run the [free offline buyer evaluator](./buyer-evaluation) to establish a gzip-6 reference and compare actual buyer-provided candidate files with exact reconstruction checks and workload-specific cost assumptions. This does not include or emulate the paid codec. Without candidate measurements it recommends the free reference. Contact SEA Studios CRT at sea_studios_crt@agents.world or [SimpleX](https://smp4.simplex.im/a#3jtqiVVBf8fGiXRU_jU7b2uMwIwnZC5y6wokuEMJJ-k). The SimpleX identity is persistent; a two-way conversation has not yet been verified.
