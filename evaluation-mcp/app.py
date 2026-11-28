"""Public, credential-free CRTG4 research evaluation. No purchase or write operations."""
import base64
import binascii
import gzip
import hashlib
import json
import math
import random
import re
import sys
import tempfile
import time
import threading
import uuid
from collections import Counter
from datetime import datetime, timezone
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PIN = "429f3dcf6b9d280836c527b02652e524fe9af2e5"
ARTIFACTS = "https://github.com/Joe-You-Know/constructive-runtime-methodology/tree/" + PIN + "/buyer-evaluation"
STOREFRONT = "https://joe-you-know-crt-commerce.hf.space/"
OFFER = STOREFRONT + "offer.json"
MAX = 65536
LIMIT_B64 = 4 * ((MAX + 2) // 3)
SCOPE = "Free experimental Python research codec; not the paid Windows compiler runtime."
TRIAL_SHA = "192740a5b119e02bf3b1fc991124c90564857dc7a3e0095eac3a79eab2ba7905"

# The archive is the publicly published, pinned research trial; no runtime download.
_archive = base64.b64decode("".join((ROOT / "trial.zip.b64").read_text().split()), validate=True)
if hashlib.sha256(_archive).hexdigest() != TRIAL_SHA:
    raise RuntimeError("Pinned research trial archive digest mismatch")
_vendor = tempfile.TemporaryDirectory(prefix="crt-research-")
_zip = Path(_vendor.name) / "trial.zip"
_zip.write_bytes(_archive)
sys.path.insert(0, str(_zip))
import grammar_v4 as codec
REPORT = json.loads((ROOT / "benchmark-summary.json").read_text())

# Only aggregate counters; no source bytes, hashes, addresses, identifiers, or user agents.
_USAGE_EPOCH = uuid.uuid4().hex
_USAGE_STARTED = datetime.now(timezone.utc).isoformat()
_USAGE_LOCK = threading.Lock()
_PURPOSES = ("unspecified", "external-evaluation", "operator-test")
_USAGE = {p: Counter() for p in _PURPOSES}

def _purpose(purpose):
    if purpose not in _PURPOSES:
        raise ValueError("unsupported declared purpose")
    return purpose

def _count(purpose, event):
    with _USAGE_LOCK:
        _USAGE[_purpose(purpose)][event] += 1

def get_usage_summary() -> dict:
    """Read anonymous process-lifetime event counters without incrementing them. Caller purpose is self-declared, not verified identity."""
    with _USAGE_LOCK:
        counts = {p: dict(c) for p, c in _USAGE.items()}
    return {"schema": "crt-eval-usage-v1", "epoch": _USAGE_EPOCH, "started_at": _USAGE_STARTED,
            "as_of": datetime.now(timezone.utc).isoformat(), "counts": counts,
            "coverage": "Since this process started; resets on restart, no historical reconstruction. Counts are events, not unique people or verified independent buyers. All declared purposes are unverified.",
            "privacy": "Application records only aggregate counts; no input data, hashes, IP, user agent, or caller ID. Host request logging is outside this scope."}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def get_product_status() -> dict:
    """Read the fixed public live product-status endpoint. Never creates an order."""
    try:
        req = urllib.request.Request(OFFER, headers={"Accept": "application/json"})
        with urllib.request.build_opener(NoRedirect).open(req, timeout=5) as response:
            raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError("response bound")
        offer = json.loads(raw)
        if not isinstance(offer, dict):
            raise ValueError("invalid offer")
        fields = ("purchase_available", "mode", "security_acceptance_met", "managed_tax_scope_accepted", "currency", "unit_amount", "price_cents", "version", "platform")
        return {"status": "retrieved", "source": OFFER, "offer": {k: offer[k] for k in fields if k in offer}, "scope": SCOPE}
    except (OSError, ValueError, TypeError):
        return {"status": "unavailable", "source": OFFER, "purchase_available": None, "scope": SCOPE}

def get_benchmark_results() -> dict:
    """Get the pinned developer-run CRTG4 benchmark sizes, including losses and controls."""
    return {"scope": SCOPE, "independent_validation": False, "artifacts": ARTIFACTS, **REPORT}

def _source(kind: str, payload: str, size_bytes: int, seed: int) -> bytes:
    if not isinstance(payload, str) or len(payload) > LIMIT_B64:
        raise ValueError("payload exceeds service limit")
    if kind == "text":
        if len(payload) > MAX:
            raise ValueError("text exceeds service limit")
        d = payload.encode("utf-8")
    elif kind == "base64":
        try:
            d = base64.b64decode(payload, validate=True)
        except (ValueError, binascii.Error):
            raise ValueError("invalid base64") from None
        if base64.b64encode(d).decode("ascii") != payload:
            raise ValueError("noncanonical base64")
    else:
        if type(size_bytes) is not int or not 0 <= size_bytes <= MAX:
            raise ValueError("fixture size must be 0..65536")
        if type(seed) is not int or not 0 <= seed <= 2147483647:
            raise ValueError("seed must be 0..2147483647")
        if payload:
            raise ValueError("synthetic fixtures do not accept a payload")
        rng = random.Random(seed)
        if kind in ("repeat", "sparse-defects"):
            d = bytearray((b"abc1234!" * ((size_bytes + 7) // 8))[:size_bytes])
            if kind == "sparse-defects":
                for i in range(0, size_bytes, 1021):
                    d[i] = rng.randrange(256)
            d = bytes(d)
        elif kind == "random":
            d = rng.randbytes(size_bytes)
        elif kind == "mixed":
            out = bytearray()
            for i in range(0, size_bytes, 1024):
                n = min(1024, size_bytes - i)
                out.extend((b"record-00000001\n" * ((n+15)//16))[:n] if i//1024 % 2 == 0 else rng.randbytes(n))
            d = bytes(out)
        else:
            raise ValueError("unsupported workload")
    if len(d) > MAX:
        raise ValueError("decoded input exceeds 65536 bytes")
    return d

def _measure(d: bytes) -> dict:
    digest = hashlib.sha256(d).digest()
    t = time.perf_counter_ns()
    g = gzip.compress(d, compresslevel=6, mtime=0)
    gt = (time.perf_counter_ns() - t) / 1e6
    t = time.perf_counter_ns()
    w, stats = codec.encode(d)
    ct = (time.perf_counter_ns() - t) / 1e6
    t = time.perf_counter_ns()
    recovered = codec.decode(w, digest)
    dt = (time.perf_counter_ns() - t) / 1e6
    if recovered != d or gzip.decompress(g) != d:
        raise RuntimeError("exact recovery failed")
    return {"scope": SCOPE, "source_bytes": len(d), "source_sha256": digest.hex(),
            "gzip6_bytes": len(g), "crtg4_bytes": len(w), "crtg4_sha256": hashlib.sha256(w).hexdigest(),
            "exact_crtg4_recovery": True, "exact_gzip_recovery": True,
            "size_preference": "CRTG4" if len(w) < len(g) else "gzip-6" if len(g) < len(w) else "tie",
            "crtg4_minus_gzip_bytes": len(w)-len(g),
            "gzip_encode_ms": gt, "crtg4_encode_ms": ct, "crtg4_decode_ms": dt,
            "timing_scope": "Single in-memory fixed-order observation; not a controlled performance benchmark.",
            "metadata": "CRTG4 size includes embedded 32-byte digest; expected digest is independently computed for verification.",
            "codec_modes": stats["modes"], "periodic_runs": stats["periodicRuns"], "exceptions": stats["exceptions"],
            "purchase_recommendation": "None; free research result does not establish paid runtime suitability."}

def evaluate_workload(kind: str = "sparse-defects", payload: str = "", size_bytes: int = 65536, seed: int = 54, purpose: str = "unspecified") -> dict:
    """Compare CRTG4 and gzip-6 on nonconfidential text/base64 or synthetic fixtures (max 64 KiB). No input storage by this app; public hosting may log requests."""
    _purpose(purpose)
    result = _measure(_source(kind, payload, size_bytes, seed))
    _count(purpose, "evaluation_completed")
    _count(purpose, "evaluation_size_" + {"CRTG4": "win", "gzip-6": "loss", "tie": "tie"}[result["size_preference"]])
    return result

def verify_reconstruction(source_base64: str, expected_sha256: str) -> dict:
    """Reconstruct a fresh CRTG4 stream from public source bytes and compare an independently supplied SHA-256. Does not accept arbitrary encoded streams."""
    d = _source("base64", source_base64, 0, 0)
    if not isinstance(expected_sha256, str) or not re.fullmatch("[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("expected SHA-256 must be 64 hexadecimal characters")
    actual = hashlib.sha256(d).hexdigest()
    if actual != expected_sha256.lower():
        return {"verified": False, "reason": "source digest mismatch", "scope": SCOPE}
    w, _ = codec.encode(d)
    recovered = codec.decode(w, bytes.fromhex(expected_sha256))
    return {"verified": recovered == d, "source_sha256": actual, "encoded_sha256": hashlib.sha256(w).hexdigest(), "encoded_bytes": len(w), "scope": SCOPE}

def calculate_storage_economics(gzip_bytes: int, crtg4_bytes: int, copies: int = 1, usd_per_gb_month: float = 0.02, months: int = 1) -> dict:
    """Estimate storage-only cost from measured encoded sizes; decimal GB. Does not extrapolate codec speed or paid product benefits."""
    if any(type(v) is not int or not 0 <= v <= 10**12 for v in (gzip_bytes, crtg4_bytes)):
        raise ValueError("byte sizes must be integers 0..10^12")
    if type(copies) is not int or not 1 <= copies <= 10**6 or type(months) is not int or not 1 <= months <= 120:
        raise ValueError("copies or months out of range")
    if type(usd_per_gb_month) not in (int, float) or not math.isfinite(usd_per_gb_month) or not 0 <= usd_per_gb_month <= 1000:
        raise ValueError("invalid storage rate")
    g = gzip_bytes * copies / 1e9 * usd_per_gb_month * months
    c = crtg4_bytes * copies / 1e9 * usd_per_gb_month * months
    return {"gzip_storage_usd": g, "crtg4_storage_usd": c, "difference_usd": g-c, "bytes_saved": (gzip_bytes-crtg4_bytes)*copies,
            "excluded": "Compute, transfer, verification, dependencies and license; supplied sizes only.", "scope": SCOPE}

def get_purchase_requirements() -> dict:
    """Read the separate experimental runtime's purchase requirements and limits. No checkout initiation."""
    return {"product": "ConstructiveRT v1.5.0 experimental Windows x64 compiler runtime", "listed_price_usd": 4.99,
            "price_note": "One-time listed price before applicable tax; verify current live offer.",
            "requirements": "Compatible Windows x64 and local toolchain/trust setup; independently authorized buyer payment.",
            "security_acceptance": "Integrated security/performance acceptance not established.",
            "research_codec_included_in_paid_offer": False, "automatic_purchase": False,
            "offer": OFFER, "addendum": STOREFRONT+"release/v1.5.0/addendum.json", "scope": SCOPE}

def get_purchase_link(purpose: str = "unspecified") -> dict:
    """Return an attributed public storefront URL only if the fixed live offer reports purchasing available. Never posts to checkout."""
    _purpose(purpose)
    _count(purpose, "purchase_link_requested")
    status = get_product_status()
    if status.get("status") != "retrieved" or status["offer"].get("purchase_available") is not True:
        return {"available": None if status.get("status") != "retrieved" else False, "url": None, "source": OFFER}
    _count(purpose, "purchase_link_returned")
    return {"available": True, "url": STOREFRONT+"?src=eval-mcp", "source": OFFER, "scope": SCOPE,
            "warning": "Separate experimental compiler runtime; no purchase or buyer recommendation is implied."}

def assess_runtime_fit(platform: str = "other", compatible_compiler_workflow: bool = False,
                       toolchain_ready: bool = False, accepts_experimental_limits: bool = False,
                       requires_production_security: bool = True, buyer_authorized: bool = False,
                       wants_experimental_evaluation: bool = False, purpose: str = "unspecified") -> dict:
    """Assess declared fit for the separate paid experimental compiler runtime, not CRTG4. Returns a storefront only for a compatible, explicitly authorized experimental evaluation. No order creation."""
    _purpose(purpose)
    flags = (compatible_compiler_workflow, toolchain_ready, accepts_experimental_limits,
             requires_production_security, buyer_authorized, wants_experimental_evaluation)
    if any(type(v) is not bool for v in flags):
        raise ValueError("explicit boolean answers required")
    if platform not in ("Windows x64", "other", "unknown"):
        raise ValueError("unsupported platform answer")
    blockers = []
    if platform != "Windows x64": blockers.append("Windows x64 required")
    if not compatible_compiler_workflow: blockers.append("compatible compiler workflow not established")
    if not toolchain_ready: blockers.append("local toolchain and trust setup not ready")
    if not accepts_experimental_limits: blockers.append("experimental limitations not accepted")
    if requires_production_security: blockers.append("integrated production security acceptance is not established")
    if not buyer_authorized: blockers.append("buyer payment authorization not declared")
    if not wants_experimental_evaluation: blockers.append("no explicit intent to evaluate paid runtime")
    _count(purpose, "runtime_fit_assessed")
    result = {"scope": SCOPE, "self_declared": True, "eligible_to_consider": not blockers, "blockers": blockers,
              "url": None, "warning": "A fit result is not a purchase recommendation, proof of buyer authorization, or evidence of runtime savings. Review the release addendum before a separate, voluntary purchase.",
              "addendum": STOREFRONT+"release/v1.5.0/addendum.json", "free_evaluation": ARTIFACTS}
    if blockers:
        _count(purpose, "runtime_fit_not_ready")
        return result
    _count(purpose, "runtime_fit_declared_ready")
    status = get_product_status()
    if status.get("status") == "retrieved" and status["offer"].get("purchase_available") is True:
        result["url"] = STOREFRONT+"?src=eval-mcp-fit"
        _count(purpose, "qualified_link_returned")
    else:
        result["offer_unavailable"] = True
    return result

def build_ui():
    import gradio as gr
    with gr.Blocks(title="ConstructiveRT Evaluation MCP", analytics_enabled=False) as demo:
        gr.Markdown("# ConstructiveRT — free research evaluation\nCompare byte-exact CRTG4 and gzip-6. Maximum public input: 64 KiB. Use only nonconfidential data. No purchase needed. The paid Windows compiler runtime is separate. No input persistence is implemented; hosting may retain request logs. Anonymous aggregate event counts reset on restart; declared purpose is optional and unverified.")
        kind = gr.Dropdown(["sparse-defects","repeat","mixed","random","text","base64"], value="sparse-defects", label="Workload")
        payload = gr.Textbox(label="Public text or canonical base64 (blank for fixtures)")
        size = gr.Number(value=65536, precision=0, label="Synthetic bytes")
        seed = gr.Number(value=54, precision=0, label="Synthetic seed")
        purpose = gr.Dropdown(list(_PURPOSES), value="unspecified", label="Optional declared purpose (not identity verification)")
        out = gr.JSON(label="Evaluation")
        gr.Button("Evaluate").click(evaluate_workload,[kind,payload,size,seed,purpose],out,api_name="evaluate_workload",concurrency_id="codec",concurrency_limit=1)
        with gr.Accordion("Verification and economics", open=False):
            s = gr.Textbox(label="Public source base64")
            h = gr.Textbox(label="Expected SHA-256")
            v = gr.JSON()
            gr.Button("Verify").click(verify_reconstruction,[s,h],v,api_name="verify_reconstruction",concurrency_id="codec",concurrency_limit=1)
            g = gr.Number(value=5731,precision=0,label="gzip bytes")
            c = gr.Number(value=3129,precision=0,label="CRTG4 bytes")
            copies = gr.Number(value=1,precision=0,label="Copies")
            rate = gr.Number(value=0.02,label="USD/GB-month")
            months = gr.Number(value=1,precision=0,label="Months")
            e = gr.JSON()
            gr.Button("Estimate").click(calculate_storage_economics,[g,c,copies,rate,months],e,api_name="calculate_storage_economics")
        with gr.Accordion("Separate paid runtime suitability",open=False):
            plat = gr.Dropdown(["Windows x64","other","unknown"],value="unknown",label="Platform")
            workflow = gr.Checkbox(label="I have a compatible compiler workflow",value=False)
            toolchain = gr.Checkbox(label="Local toolchain and trust setup are ready",value=False)
            experimental = gr.Checkbox(label="I accept the experimental limitations",value=False)
            production = gr.Checkbox(label="I require production security acceptance",value=True)
            authorized = gr.Checkbox(label="I have independent authorization to pay",value=False)
            intent = gr.Checkbox(label="I intend to evaluate the separate paid runtime",value=False)
            fit = gr.JSON()
            gr.Button("Assess runtime fit").click(assess_runtime_fit,[plat,workflow,toolchain,experimental,production,authorized,intent,purpose],fit,api_name="assess_runtime_fit")
        with gr.Accordion("Purchase link",open=False):
            link = gr.JSON()
            gr.Button("Purchase link").click(get_purchase_link,[purpose],link,api_name="get_purchase_link")
        for title, fn in [("Live product status",get_product_status),("Published benchmarks",get_benchmark_results),("Purchase requirements",get_purchase_requirements),("Anonymous usage summary",get_usage_summary)]:
            with gr.Accordion(title,open=False):
                j = gr.JSON()
                gr.Button(title).click(fn,[],j,api_name=fn.__name__)
    return demo.queue(max_size=8, default_concurrency_limit=1)

if __name__ == "__main__":
    build_ui().launch(mcp_server=True, share=False, show_error=False)
