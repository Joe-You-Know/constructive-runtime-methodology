"""Constructive runs with explicit exceptions, experimental CRTG4; Python 3.11+.

CRTG3 ends a periodic run at the first byte that contradicts it. CRTG4 may
instead keep the run and record the contradicting bytes as exceptions:

    repeat <unit> for <n> bytes, except at positions p1, p2, ... use bytes v1, v2, ...

Positions are zero-based offsets inside the run, stored as gaps from the
previous exception. A run stops absorbing exceptions once the running gain
falls STOP bytes below the best gain seen, so dense contradiction (noise, a
genuinely new pattern) still ends the run.

Discovery, literals, repeat and patch commands are unchanged from CRTG3.
No fixed data frames, no seed or external dictionary. Not a production codec.
Requires crcodec from the published CRT research trial.
"""
import hashlib,io
from crcodec.codec import uvar
from crcodec import general
import grammar_v3 as v3

MAGIC=b'CRTG4\x00'
MAX=v3.MAX
MAX_PERIOD=v3.MAX_PERIOD
MIN_RUN=v3.MIN_RUN
STOP=32          # stop absorbing exceptions once gain is this far below best
CHUNK=65536      # comparison window against the tiled unit
RESTART=8        # approx. cost of literal header + zero-edit patch to resume the unit

def first_mismatch(d,a,limit,tile,origin,p):
    """First position >= a (and < limit) where d differs from the unit tiled from origin."""
    step=max(p,64)
    while a<limit:
        k=min(step,limit-a,CHUNK)
        ph=(a-origin)%p
        if d[a:a+k]==tile[ph:ph+k]:
            a+=k;step=min(step*2,CHUNK);continue
        lo,hi=0,k
        while lo+1<hi:
            m=(lo+hi)//2
            if d[a:a+m]==tile[ph:ph+m]:lo=m
            else:hi=m
        return a+lo
    return limit

def base_cost(p):
    # mode + length (<=3) + subtype + period + unit + exception count (<=3)
    return 1+3+1+len(uvar(p))+p+3

def extend(d,i,unit,length):
    """Grow a clean run of `length` bytes at i by absorbing exceptions while profitable.
    Returns (length, exceptions) with exceptions as [(offset_in_run, byte)].

    Three stopping rules:
    * gain falls STOP bytes below the best seen (noise, or the relationship ended);
    * a cluster of adjacent exceptions costs more than restarting the run after it
      (a burst is cheaper as a literal plus a zero-edit patch of the same unit);
    * the same exception recurs at the same phase in consecutive periods
      (the unit itself changed; a CRTG3 patch describes that once, not per period).
    """
    n=len(d);p=len(unit)
    tile=unit*((CHUNK+2*p)//p+1)
    exc=[];cost=0;last=-1
    best=(length-base_cost(p),length,0)
    hist=[best]                  # hist[j]: best ending that uses only exceptions < j
    cluster=0;cluster_cost=0     # current run of adjacent exceptions
    streak=0                     # consecutive same-phase, same-value recurrences
    pos=i+length
    while pos<n:
        rel=pos-i;v=d[pos];gap=rel-last-1;c=len(uvar(gap))+1
        if exc and gap<=1:cluster+=1;cluster_cost+=c
        else:cluster=len(exc);cluster_cost=c
        if exc and rel-exc[-1][0]==p and v==exc[-1][1]:streak+=1
        else:streak=0
        cost+=c;exc.append((rel,v));last=rel
        span=rel-exc[cluster][0]+1
        if cluster_cost>span+RESTART:best=hist[cluster];break
        if streak>=2:best=hist[len(exc)-1-streak];break
        end=first_mismatch(d,pos+1,n,tile,i,p)
        gain=(end-i)-base_cost(p)-cost
        if gain>best[0]:best=(gain,end-i,len(exc))
        elif gain<best[0]-STOP:break
        hist.append(best)
        pos=end
    return best[1],exc[:best[2]]

def run_cmd(n,unit,prev,exc):
    """Encode one run. Without exceptions this is exactly CRTG3's repeat/patch."""
    if not exc:return v3.repeat(n,unit,prev)
    h=uvar(n)
    base=b'\x00'+uvar(len(unit))+unit
    if prev is not None and len(prev)==len(unit):
        edits=[(k,v) for k,v in enumerate(unit) if v!=prev[k]]
        patch=b'\x01'+uvar(len(edits))+bytes(x for e in edits for x in e)
        if len(patch)<len(base):base=patch
    body=bytearray(uvar(len(exc)));last=-1
    for rel,v in exc:
        body+=uvar(rel-last-1);body.append(v);last=rel
    return b'\x04'+h+base+bytes(body),'exception'

def encode(d):
    if len(d)>MAX:raise ValueError('size bound')
    header=MAGIC+uvar(len(d))+hashlib.sha256(d).digest()
    out=bytearray(header);i=start=0;prev=None;counts={};runs=[];exceptions=0
    def add(cmd,mode):
        if mode:
            out.extend(cmd);counts[mode]=counts.get(mode,0)+1
    while i+MIN_RUN<=len(d):
        r=v3.discover(d,i)
        if r is None:i+=1;continue
        n,unit=r
        n,exc=extend(d,i,unit,n)
        cmd,mode=run_cmd(n,unit,prev,exc)
        if len(cmd)+2>=n:i+=1;continue
        add(*v3.literal(d[start:i]))
        add(cmd,mode)
        runs.append((i,n,len(unit),mode,len(exc)));exceptions+=len(exc)
        prev=unit;i+=n;start=i
    add(*v3.literal(d[start:]))
    fallback,mode=v3.literal(d)
    if len(header)+len(fallback)<len(out):
        out=bytearray(header+fallback);counts={mode:1} if mode else {};runs=[];exceptions=0
    return bytes(out),dict(modes=counts,periodicRuns=len(runs),exceptions=exceptions,runSample=runs[:12])

def decode(w,expected):
    s=io.BytesIO(w)
    def take(n):
        if not 0<=n<=MAX:raise ValueError('read bound')
        b=s.read(n)
        if len(b)!=n:raise ValueError('truncated')
        return b
    def var():
        # Canonical bounded unsigned varint; at most 3 bytes for the 1 MiB cap.
        value=0
        for i in range(3):
            b=take(1)[0];value|=(b&127)<<(7*i)
            if b<128:
                if value>MAX or (i and b==0):raise ValueError('varint')
                return value
        raise ValueError('varint bound')
    def patched(prev):
        if prev is None:raise ValueError('missing repeat state')
        count=var()
        if count>len(prev):raise ValueError('patch count')
        u=bytearray(prev);last=-1
        for _ in range(count):
            k,v=take(2)
            if not last<k<len(u):raise ValueError('patch index')
            u[k]=v;last=k
        return bytes(u)
    def tiled(unit,n):
        return (unit*((n+len(unit)-1)//len(unit)))[:n]
    if take(len(MAGIC))!=MAGIC:raise ValueError('magic')
    total=var()
    if len(expected)!=32 or take(32)!=expected:raise ValueError('source digest')
    out=bytearray();prev=None
    while len(out)<total:
        mode=take(1)[0];n=var()
        if not 0<n<=total-len(out):raise ValueError('length')
        if mode==0:part=take(n)
        elif mode==1:
            p=var()
            if not 0<p<=min(MAX_PERIOD,n):raise ValueError('period')
            prev=take(p);part=tiled(prev,n)
        elif mode==2:
            prev=patched(prev)
            if len(prev)>n:raise ValueError('period larger than run')
            part=tiled(prev,n)
        elif mode==3:
            m=var()
            if not 0<m<n:raise ValueError('token bound')
            part=general._expand_frame(take(m),n)
        elif mode==4:
            sub=take(1)[0]
            if sub==0:
                p=var()
                if not 0<p<=min(MAX_PERIOD,n):raise ValueError('period')
                prev=take(p)
            elif sub==1:prev=patched(prev)
            else:raise ValueError('exception base')
            if len(prev)>n:raise ValueError('period larger than run')
            part=bytearray(tiled(prev,n))
            count=var()
            if not 0<count<=n:raise ValueError('exception count')
            last=-1
            for _ in range(count):
                k=last+1+var();v=take(1)[0]
                if k>=n:raise ValueError('exception index')
                # Canonical: an exception must actually contradict the relationship.
                if part[k]==v:raise ValueError('redundant exception')
                part[k]=v;last=k
            part=bytes(part)
        else:raise ValueError('mode')
        if len(part)!=n:raise ValueError('output length')
        out.extend(part)
    if s.read(1) or hashlib.sha256(out).digest()!=expected:raise ValueError('integrity')
    return bytes(out)
