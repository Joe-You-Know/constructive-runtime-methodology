"""CRTG4 benchmark: the 23 CRTG3 workloads plus new sparse-defect sweeps,
randomized round trips and negative controls. Python 3.11+.
Run from a directory holding the CRT research trial (trial.py, crcodec/)."""
import hashlib,gzip,json,random,time,sys,platform
from pathlib import Path
import grammar_v2 as v2,grammar_v3 as v3,grammar_v4 as v4
import benchmark_v3 as b3
N=v4.MAX

def defects(seed,every,unit=b'abc1234!'):
    rng=random.Random(seed);base=bytearray((unit*(N//len(unit)+1))[:N])
    for j in range(0,N,every):base[j]=rng.randrange(256)
    return bytes(base)

def bursts(seed,every,width):
    rng=random.Random(seed);base=bytearray((b'abc1234!'*(N//8))[:N])
    for j in range(0,N,every):base[j:j+width]=rng.randbytes(len(base[j:j+width]))
    return bytes(base)

def log_lines(seed):
    rng=random.Random(seed);out=bytearray();k=0
    while len(out)<N:
        out+=f"2026-11-27T12:00:{k%60:02d}Z INFO worker={rng.randrange(8)} job={k:08d} status=ok\n".encode();k+=1
    return bytes(out[:N])

def primary():
    cases=[(f'mixed-{b}-{s}',v2.fixture(b,s)) for b in (512,4096,65536) for s in (20261127,20261128,20261129)]
    cases+=[('shifted-137',b'x'*137+v2.fixture(4096,20261130)[:-137]),('shifted-1',b'X'+v2.fixture(512,20261130)[:-1]),('shifted-251',random.Random(9).randbytes(251)+v2.fixture(65536,20261130)[:-251])]
    cases+=[(f'irregular-{s}',b3.irregular(s)) for s in (20261131,20261132,20261133)]
    cases+=[('changing-motif',b3.changing(543)),('sparse-defects',b3.noisy(54)),('random-1MiB',random.Random(20261130).randbytes(N)),('repeat-1MiB',(b'not-a-csv-record!\x00'*N)[:N]),('source-code',b'\n'.join(Path(p).read_bytes() for p in ['trial.py','crcodec/codec.py','crcodec/general.py'])),('odd-length',random.Random(42).randbytes(65537)),('empty',b''),('short',b'abc')]
    return cases

def extra():
    # New workloads chosen to probe where exceptions help and where they should stop.
    cases=[(f'defects-every-{e}',defects(60+e,e)) for e in (16,64,256,4096)]
    cases+=[('defects-period-37',defects(77,1021,bytes(range(37)))),('bursts-16-every-4096',bursts(78,4096,16)),('bursts-256-every-4096',bursts(79,4096,256)),('log-lines',log_lines(80))]
    return cases

def measure(name,d,rows,neg):
    sha=hashlib.sha256(d).digest()
    t=time.perf_counter();z=gzip.compress(d,compresslevel=6,mtime=0);gz=(time.perf_counter()-t)*1000
    assert gzip.decompress(z)==d
    t=time.perf_counter();w3,_=v3.encode(d);e3=(time.perf_counter()-t)*1000;assert v3.decode(w3,sha)==d
    t=time.perf_counter();w,m=v4.encode(d);enc=(time.perf_counter()-t)*1000
    t=time.perf_counter();rest=v4.decode(w,sha);dec=(time.perf_counter()-t)*1000
    assert rest==d,name
    for bad,expected in ((w[:-1],sha),(w+b'X',sha),(w[:10]+bytes([w[10]^1])+w[11:],sha),(w,bytes([sha[0]^1])+sha[1:])):
        try:v4.decode(bad,expected)
        except Exception:neg[0]+=1
        else:raise AssertionError('negative accepted '+name)
    row=dict(case=name,sourceBytes=len(d),sourceSHA256=sha.hex(),gzipBytes=len(z),v3Bytes=len(w3),v4Bytes=len(w),encodedSHA256=hashlib.sha256(w).hexdigest(),exact=True,gzipEncodeMs=gz,v3EncodeMs=e3,v4EncodeMs=enc,v4DecodeMs=dec,**m)
    rows.append(row)
    print(f"{name:24} gzip={len(z):>9,} v3={len(w3):>9,} v4={len(w):>9,} exc={m['exceptions']:>6} enc={enc:7.0f}ms dec={dec:5.1f}ms",flush=True)

def randomized(count=250,size=65536):
    """Random mixtures of periodic regions, sparse/burst defects, noise and odd periods."""
    ok=0
    for seed in range(count):
        rng=random.Random(10_000+seed);out=bytearray()
        while len(out)<size:
            kind=rng.random();p=rng.choice([1,2,3,7,8,19,37,61,127,128,129,200])
            unit=rng.randbytes(p);n=rng.randrange(1,6000)
            reg=bytearray((unit*(n//p+1))[:n])
            if kind<0.5:
                for _ in range(rng.randrange(0,40)):
                    if reg:reg[rng.randrange(len(reg))]=rng.randrange(256)
            elif kind<0.6 and reg:
                j=rng.randrange(len(reg));reg[j:j+rng.randrange(1,64)]=rng.randbytes(len(reg[j:j+64]))
            out+=reg;out+=rng.randbytes(rng.randrange(0,500))
        d=bytes(out[:rng.randrange(size//2,size+1)]);sha=hashlib.sha256(d).digest()
        w,_=v4.encode(d)
        assert v4.decode(w,sha)==d,f'random seed {seed}'
        ok+=1
    return ok

def run():
    rows=[];extra_rows=[];neg=[0]
    print('-- primary (CRTG3 workloads)');[measure(n,d,rows,neg) for n,d in primary()]
    print('-- new workloads');[measure(n,d,extra_rows,neg) for n,d in extra()]
    t=time.perf_counter();rnd=randomized();rt=(time.perf_counter()-t)*1000
    print(f'-- randomized round trips: {rnd}/250 exact ({rt:.0f} ms)')
    report=dict(schema='crt-exceptions-v4',python=sys.version,platform=platform.platform(),sourceLimit=N,stop=v4.STOP,
        primaryRoundTrips=len(rows),extraRoundTrips=len(extra_rows),randomizedRoundTrips=rnd,negativeControls=neg[0],
        commercialRuntimeEvaluated=False,timingScope='single in-memory run, encoder search included, fixed order; no disk or transport',
        rows=rows,extraRows=extra_rows)
    Path('grammar_v4_report_20261127.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(rows),len(extra_rows),rnd,neg[0])
if __name__=='__main__':run()
