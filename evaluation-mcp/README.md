---
title: ConstructiveRT Evaluation MCP
emoji: "🔬"
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
---

# ConstructiveRT Evaluation MCP

Free public CRTG4 research-codec evaluation for agents and people. Compare gzip-6 with byte-exact reconstruction on public text, canonical base64, or seeded synthetic inputs up to 64 KiB. No credentials, payments, arbitrary URLs, file uploads or external encoded streams are accepted. Do not submit confidential data: public hosting may log requests. This app does not intentionally persist input payloads.

The separate $4.99 experimental Windows x64 compiler runtime is not evaluated by the free research codec. Full limitations and benchmark losses are exposed. The public storefront is only linked, never called with POST.

Pinned research: https://github.com/Joe-You-Know/constructive-runtime-methodology/tree/429f3dcf6b9d280836c527b02652e524fe9af2e5/buyer-evaluation

## Deployment and validation

Source files in this folder are designed to be uploaded unchanged to the root of the separate HF Space joe-you-know/crt-evaluation-mcp, CPU Basic only. Install requirements, then run `python -m unittest -v test_evaluation`. Run `python app.py` locally. Gradio exposes MCP via its advertised API configuration; verify the deployed transport using a real MCP client before registering. Do not claim registry publication from source alone.

The trial archive is stored as base64 with pinned SHA-256, and the grammar modules are copies of the pinned public research source. The archive is loaded from a temporary local file rather than downloaded at runtime.

## Tools

get_product_status, get_benchmark_results, evaluate_workload, verify_reconstruction, calculate_storage_economics, get_purchase_requirements, get_purchase_link.

No purchase or write capability. No commerce secrets. Attribution tag `eval-mcp` applies only to a storefront URL returned to a visitor; it does not identify a buyer. The MCP is experimental. The hosted instance must pass independent deployment checks before promotion.
