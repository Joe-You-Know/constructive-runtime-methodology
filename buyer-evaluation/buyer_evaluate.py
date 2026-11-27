#!/usr/bin/env python3
"""Buyer-owned, offline CRT storage economics check. No checkout or network calls."""
import argparse,gzip,hashlib,json,math,os,random,tempfile,time
from pathlib import Path
PRICE=4.99
def sha(b):return hashlib.sha256(b).hexdigest()
def positive(s):
    n=float(s)
    if not math.isfinite(n) or n<0:raise argparse.ArgumentTypeError("must be finite and nonnegative")
    return n
def fixture(kind,n):
    if kind=="affine":return "".join(f"{i:08d},{3*i+7:012d},{5*i+11:012d}\n" for i in range(n)).encode()
    if kind=="ordinary":return "".join(f"record {i}: {random.Random(i).choice(['red','blue','green','orange'])}\n" for i in range(n)).encode()
    return random.Random(20261127).randbytes(n*35)
def evaluate(raw,encoded=None,decoded=None,*,copies=1,months=12,storage=0.0,transfers=0.0,egress=0.0,seconds=0.0,compute=0.0,overhead=0,security=False,windows=False):
    t=time.perf_counter(); gz=gzip.compress(raw,compresslevel=6,mtime=0); enc=time.perf_counter()-t
    t=time.perf_counter(); reconstructed=gzip.decompress(gz); dec=time.perf_counter()-t
    if reconstructed!=raw:raise RuntimeError("gzip round trip mismatch")
    result={"schema":"crt-buyer-evaluation-v1","sourceBytes":len(raw),"sourceSha256":sha(raw),"freeReference":{"codec":"gzip-6","encodedBytes":len(gz),"roundTripExact":True,"encodeSeconds":enc,"decodeSeconds":dec},"offer":{"priceUSD":PRICE,"experimental":True,"integratedSecurityAcceptancePassed":False,"platform":"Windows x64"},"candidate":None,"decision":"FREE_REFERENCE_UNTIL_MEASURED"}
    if encoded is None or decoded is None:return result
    exact=decoded==raw
    total=len(encoded)+overhead
    delta=len(gz)-total
    storage_savings=delta/1e9*copies*months*storage
    transfer_savings=delta/1e9*transfers*egress
    compute_cost=seconds/3600*compute
    net=storage_savings+transfer_savings-compute_cost-PRICE
    result["candidate"]={"encodedBytes":len(encoded),"declaredAdditionalBytes":overhead,"totalCandidateBytes":total,"decodedSha256":sha(decoded),"roundTripExact":exact,"bytesSavedVsGzip":delta,"storageSavingsUSD":storage_savings,"transferSavingsUSD":transfer_savings,"additionalComputeCostUSD":compute_cost,"netValueBeforeTaxUSD":net,"assumptions":{"copies":copies,"months":months,"storageUSDPerGBMonth":storage,"transfers":transfers,"egressUSDPerGB":egress,"additionalComputeSecondsTotal":seconds,"computeUSDPerHour":compute,"requiresIntegratedSecurity":security,"buyerConfirmsWindowsX64Compatibility":windows},"evidence":"Buyer-supplied files; codec identity, actual generation and declared overhead are not independently authenticated."}
    if not exact:result["decision"]="REJECT_ROUND_TRIP_MISMATCH"
    elif security:result["decision"]="REJECT_UNMET_SECURITY_REQUIREMENT"
    elif not windows:result["decision"]="FREE_REFERENCE_PLATFORM_NOT_CONFIRMED"
    elif net<=0:result["decision"]="FREE_REFERENCE_NONPOSITIVE_NET_VALUE"
    else:result["decision"]="POSITIVE_ESTIMATE_REQUIRES_BUYER_VALIDATION"
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path);p.add_argument("--fixture",choices=["affine","ordinary","random"],default="affine");p.add_argument("--records",type=int,default=2048)
    p.add_argument("--encoded",type=Path);p.add_argument("--decoded",type=Path)
    p.add_argument("--extra-bytes",type=int,default=0,help="All required decoder metadata, state, dictionary and other incremental bytes not included in encoded file")
    p.add_argument("--copies",type=positive,default=1);p.add_argument("--months",type=positive,default=12)
    p.add_argument("--storage-usd-gb-month",type=positive,default=0);p.add_argument("--transfers",type=positive,default=0);p.add_argument("--egress-usd-gb",type=positive,default=0)
    p.add_argument("--additional-compute-seconds",type=positive,default=0,help="Total additional compute vs gzip over full evaluation horizon")
    p.add_argument("--compute-usd-hour",type=positive,default=0);p.add_argument("--requires-integrated-security",action="store_true");p.add_argument("--windows-x64-compatible",action="store_true")
    a=p.parse_args()
    if a.records<1 or a.records>1000000 or a.extra_bytes<0:p.error("records must be 1..1000000; extra bytes nonnegative")
    if bool(a.encoded)!=bool(a.decoded):p.error("provide both candidate encoded and reconstructed file")
    def read(path):
        if path.stat().st_size>128*1024*1024:p.error("file exceeds 128 MiB evaluation cap")
        return path.read_bytes()
    raw=read(a.source) if a.source else fixture(a.fixture,a.records)
    result=evaluate(raw,read(a.encoded) if a.encoded else None,read(a.decoded) if a.decoded else None,copies=a.copies,months=a.months,storage=a.storage_usd_gb_month,transfers=a.transfers,egress=a.egress_usd_gb,seconds=a.additional_compute_seconds,compute=a.compute_usd_hour,overhead=a.extra_bytes,security=a.requires_integrated_security,windows=a.windows_x64_compatible)
    print(json.dumps(result,indent=2,allow_nan=False))
if __name__=="__main__":main()
