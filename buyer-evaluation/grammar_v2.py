"""Experimental CRT repeat/patch grammar. Bounded, offline, no fixture hints.
Not the released wire format. Python 3.11+.
"""
import hashlib, io, gzip, json, random, statistics, sys, time
from pathlib import Path
from crcodec.codec import uvar, read_uvar
from crcodec import general

MAGIC=b'CRTG2\x00'
MAX=1048576
SIZES=(512,1024,4096,16384,65536,262144,1048576)
MAX_PERIOD=128

def period(d):
    # Discover a short exact period from the bytes, not the fixture generator.
    if len(d)<16:return None
    prefix=d[:8];p=d.find(prefix,1,min(len(d),MAX_PERIOD+8))
    while 0<p<=MAX_PERIOD and p*2<=len(d):
        unit=d[:p]
        if (unit*((len(d)+p-1)//p))[:len(d)]==d:return unit
        p=d.find(prefix,p+1,min(len(d),MAX_PERIOD+8))
    return None

def commands(d,previous,unit):
    raw=b'\x00'+d
    best=(raw,previous,'raw')
    if unit is not None:
        c=b'\x01'+uvar(len(unit))+unit
        if len(c)<len(best[0]):best=(c,unit,'repeat')
        if previous is not None and len(previous)==len(unit):
            changes=[(i,v) for i,v in enumerate(unit) if v!=previous[i]]
            c=b'\x02'+uvar(len(changes))+bytes(x for pair in changes for x in pair)
            if len(c)<len(best[0]):best=(c,unit,'patch')
    # Retain original token grammar where profitable.
    t=general._construct_frame(d)
    c=b'\x03'+uvar(len(t))+t
    if len(c)<len(best[0]):best=(c,previous,'token')
    return best

def partition(d):
    # Estimate local costs, then encode chosen spans with sequential repeat state.
    # Not claimed globally optimal when patch state crosses a boundary.
    def visit(lo,hi):
        n=hi-lo;part=d[lo:hi];u=period(part)
        own=1+len(uvar(n))+min(n,len(uvar(len(u)))+len(u) if u else n)
        if n<=512 or u is not None:return own,[(lo,hi)]
        mid=lo+((n//2+511)//512)*512
        if mid>=hi:return own,[(lo,hi)]
        a,aa=visit(lo,mid);b,bb=visit(mid,hi)
        return (a+b,aa+bb) if a+b<own else (own,[(lo,hi)])
    return visit(0,len(d))[1] if d else []

def encode(d):
    if len(d)>MAX:raise ValueError('size limit')
    header=MAGIC+uvar(len(d))+hashlib.sha256(d).digest()
    best=None;best_stats=None
    plans=[(n,[(i,min(i+n,len(d))) for i in range(0,len(d),n)]) for n in SIZES]
    plans.append((0,partition(d)))
    for n,spans in plans:
        prev=None;out=bytearray(header+uvar(n));counts={}
        for lo,hi in spans:
            part=d[lo:hi]
            c,prev,label=commands(part,prev,period(part))
            if n==0:out+=uvar(len(part))
            out+=c;counts[label]=counts.get(label,0)+1
        if best is None or len(out)<len(best):
            best=bytes(out);best_stats={'frame':n or 'variable','frames':len(spans),'modes':counts}
    return best,best_stats

def decode(w,expected):
    s=io.BytesIO(w)
    def take(n):
        if n<0 or n>MAX:raise ValueError('read bound')
        b=s.read(n)
        if len(b)!=n:raise ValueError('truncated')
        return b
    if take(len(MAGIC))!=MAGIC:raise ValueError('magic')
    total=read_uvar(s)
    if total>MAX or take(32)!=expected:raise ValueError('source digest')
    fixed=read_uvar(s)
    if fixed not in (0,)+SIZES:raise ValueError('frame class')
    out=bytearray();prev=None
    while len(out)<total:
        n=min(fixed,total-len(out)) if fixed else read_uvar(s)
        if not 0<n<=total-len(out):raise ValueError('length')
        mode=take(1)[0]
        if mode==0:part=take(n)
        elif mode==1:
            p=read_uvar(s)
            if not 0<p<=min(MAX_PERIOD,n):raise ValueError('period')
            prev=take(p);part=(prev*((n+p-1)//p))[:n]
        elif mode==2:
            if prev is None:raise ValueError('missing repeat state')
            count=read_uvar(s)
            if count>len(prev):raise ValueError('patch count')
            u=bytearray(prev);last=-1
            for _ in range(count):
                i,v=take(2)
                if not last<i<len(u):raise ValueError('patch index')
                u[i]=v;last=i
            prev=bytes(u);p=len(prev)
            if p>n:raise ValueError('period larger than frame')
            part=(prev*((n+p-1)//p))[:n]
        elif mode==3:
            length=read_uvar(s)
            if not 0<length<n:raise ValueError('token length')
            part=general._expand_frame(take(length),n)
        else:raise ValueError('mode')
        if len(part)!=n:raise ValueError('output length')
        out+=part
    if s.read(1) or hashlib.sha256(out).digest()!=expected:raise ValueError('integrity')
    return bytes(out)

def fixture(block,seed):
    rng=random.Random(seed);parts=[]
    for i in range(MAX//block):
        if i%2:parts.append(rng.randbytes(block))
        else:
            rec=f"alpha,blue,{i//2:010d},17\n".encode()
            parts.append((rec*((block+len(rec)-1)//len(rec)))[:block])
    return b''.join(parts)

def main():
    cases=[(f'mixed-{b}-{seed}',fixture(b,seed)) for b in (512,4096,65536) for seed in (20261127,20261128,20261129)]
    cases += [('random-1MiB',random.Random(20261130).randbytes(MAX)),('repeat-1MiB',(b'not-a-csv-record!\x00'*MAX)[:MAX]),('shifted-mixed',b'x'*137+fixture(4096,20261130)[:-137]),('source-code',b'\n'.join(Path(p).read_bytes() for p in ['trial.py','crcodec/codec.py','crcodec/general.py'])),('odd-length',random.Random(42).randbytes(65537)),('empty',b'')]
    rows=[];negative=0
    for name,d in cases:
        digest=hashlib.sha256(d).digest()
        t=time.perf_counter();z=gzip.compress(d,compresslevel=6,mtime=0);ge=(time.perf_counter()-t)*1000
        t=time.perf_counter();assert gzip.decompress(z)==d;gd=(time.perf_counter()-t)*1000
        t=time.perf_counter();w,meta=encode(d);et=(time.perf_counter()-t)*1000
        t=time.perf_counter();assert decode(w,digest)==d;dt=(time.perf_counter()-t)*1000
        for bad in (w[:-1],w+b'x',w[:10]+bytes([w[10]^1])+w[11:]):
            try:decode(bad,digest)
            except Exception:negative+=1
            else:raise AssertionError('accepted corrupted stream')
        row=dict(case=name,source=len(d),sha256=digest.hex(),gzip=len(z),crt=len(w),encodedSha256=hashlib.sha256(w).hexdigest(),encodeMs=et,decodeMs=dt,gzipEncodeMs=ge,gzipDecodeMs=gd,exact=True,**meta)
        rows.append(row);print(json.dumps(row),flush=True)
    report=dict(schema='crt-grammar-v2-prototype',python=sys.version,sourceLimit=MAX,roundTrips=len(rows),negativeControls=negative,rows=rows,timingScope='single in-memory run per distinct input; no disk writes; selection cost included',commercialRuntimeEvaluated=False)
    Path('/tmp/grammar-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(rows),negative,flush=True)

if __name__=='__main__':main()
