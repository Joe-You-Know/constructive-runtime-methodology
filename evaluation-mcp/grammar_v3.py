"""Content-defined constructive runs, experimental CRTG3; Python 3.11+.
No fixed data frames, no seed or external dictionary. Not a production codec.
Requires crcodec from the published CRT research trial.
"""
import hashlib,io,time
from crcodec.codec import uvar,read_uvar
from crcodec import general

MAGIC=b'CRTG3\x00'
MAX=1048576
MAX_PERIOD=128
ANCHOR=8
MIN_RUN=24

def extent(d,i,p):
    """Longest exact prefix with period p, extending by byte comparisons."""
    end=len(d)-i-p
    matched=ANCHOR
    step=max(p,ANCHOR)
    while matched<end:
        k=min(step,end-matched)
        a=i+matched
        if d[a:a+k]==d[a+p:a+p+k]:
            matched+=k;step*=2
        else:
            lo,hi=0,k
            while lo+1<hi:
                m=(lo+hi)//2
                if d[a:a+m]==d[a+p:a+p+m]:lo=m
                else:hi=m
            matched+=lo
            break
    return p+matched

def discover(d,i):
    """Find repeated anchor at arbitrary byte position, verify actual period."""
    n=len(d)
    if n-i<MIN_RUN:return None
    prefix=d[i:i+ANCHOR]
    limit=min(n,i+MAX_PERIOD+ANCHOR)
    j=d.find(prefix,i+1,limit)
    best=None;gain=0
    while j>=0:
        p=j-i
        length=extent(d,i,p)
        if length>=max(MIN_RUN,2*p):
            cost=1+len(uvar(length))+len(uvar(p))+p
            g=length-cost
            if g>gain:
                best=(length,d[i:i+p]);gain=g
            if i+length==n:break
            # A long short-period run already supplies a profitable construction.
            # Heuristic: do not enumerate every multiple of that period.
            if length>=8*p and length>=256:break
        j=d.find(prefix,j+1,limit)
    return best

def literal(d):
    if not d:return b'',None
    h=uvar(len(d));raw=b'\x00'+h+d
    t=general._construct_frame(d)
    tok=b'\x03'+h+uvar(len(t))+t
    return (tok,'token') if len(tok)<len(raw) else (raw,'raw')

def repeat(n,unit,prev):
    h=uvar(n)
    cmd=b'\x01'+h+uvar(len(unit))+unit;mode='repeat'
    if prev is not None and len(prev)==len(unit):
        edits=[(i,v) for i,v in enumerate(unit) if v!=prev[i]]
        patch=b'\x02'+h+uvar(len(edits))+bytes(x for e in edits for x in e)
        if len(patch)<len(cmd):cmd,mode=patch,'patch'
    return cmd,mode

def encode(d):
    if len(d)>MAX:raise ValueError('size bound')
    header=MAGIC+uvar(len(d))+hashlib.sha256(d).digest()
    out=bytearray(header);i=start=0;prev=None;counts={};runs=[]
    def add(cmd,mode):
        if mode:
            out.extend(cmd);counts[mode]=counts.get(mode,0)+1
    while i+MIN_RUN<=len(d):
        r=discover(d,i)
        if r is None:i+=1;continue
        n,unit=r;cmd,mode=repeat(n,unit,prev)
        if len(cmd)+2>=n:i+=1;continue
        add(*literal(d[start:i]))
        add(cmd,mode)
        runs.append((i,n,len(unit),mode))
        prev=unit;i+=n;start=i
    add(*literal(d[start:]))
    fallback,mode=literal(d)
    if len(header)+len(fallback)<len(out):
        out=bytearray(header+fallback);counts={mode:1} if mode else {};runs=[]
    return bytes(out),dict(modes=counts,periodicRuns=len(runs),runSample=runs[:12])

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
    if take(len(MAGIC))!=MAGIC:raise ValueError('magic')
    total=var()
    if len(expected)!=32 or take(32)!=expected:raise ValueError('source digest')
    out=bytearray();prev=None
    while len(out)<total:
        mode=take(1)[0];n=var()
        if not 0<n<=total-len(out):raise ValueError('length')
        if mode==0:part=take(n)
        elif mode in (1,2):
            if mode==1:
                p=var()
                if not 0<p<=min(MAX_PERIOD,n):raise ValueError('period')
                prev=take(p)
            else:
                if prev is None or len(prev)>n:raise ValueError('missing/invalid repeat state')
                count=var()
                if count>len(prev):raise ValueError('patch count')
                u=bytearray(prev);last=-1
                for _ in range(count):
                    i,v=take(2)
                    if not last<i<len(u):raise ValueError('patch index')
                    u[i]=v;last=i
                prev=bytes(u)
            part=(prev*((n+len(prev)-1)//len(prev)))[:n]
        elif mode==3:
            m=var()
            if not 0<m<n:raise ValueError('token bound')
            part=general._expand_frame(take(m),n)
        else:raise ValueError('mode')
        if len(part)!=n:raise ValueError('output length')
        out.extend(part)
    if s.read(1) or hashlib.sha256(out).digest()!=expected:raise ValueError('integrity')
    return bytes(out)
