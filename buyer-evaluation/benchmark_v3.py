import hashlib,gzip,json,random,time,sys,platform
from pathlib import Path
import grammar_v3 as v3,grammar_v2 as v2
N=v3.MAX
def irregular(seed):
    rng=random.Random(seed);out=bytearray(rng.randbytes(137));k=0
    while len(out)<N:
        p=rng.choice([3,7,19,37,61,127,128])
        unit=rng.randbytes(p)
        length=rng.randrange(3*p,9000)
        out.extend((unit*((length+p-1)//p))[:length])
        out.extend(rng.randbytes(rng.randrange(17,9000)));k+=1
    return bytes(out[:N])
def changing(seed):
    rng=random.Random(seed);out=bytearray(rng.randbytes(53));unit=bytearray(rng.randbytes(37))
    for i in range(170):
        unit[i%37]=i%256;n=rng.randrange(300,7000)
        out.extend((bytes(unit)*((n+36)//37))[:n])
        out.extend(rng.randbytes(rng.randrange(1,3000)))
    return bytes(out[:N])
def noisy(seed):
    rng=random.Random(seed);base=bytearray((b'abc1234!'*131072))
    for j in range(0,N,1021):base[j]=rng.randrange(256)
    return bytes(base)
def run():
    cases=[(f'mixed-{b}-{s}',v2.fixture(b,s)) for b in (512,4096,65536) for s in (20261127,20261128,20261129)]
    cases += [('shifted-137',b'x'*137+v2.fixture(4096,20261130)[:-137]),('shifted-1',b'X'+v2.fixture(512,20261130)[:-1]),('shifted-251',random.Random(9).randbytes(251)+v2.fixture(65536,20261130)[:-251])]
    cases += [(f'irregular-{s}',irregular(s)) for s in (20261131,20261132,20261133)]
    cases += [('changing-motif',changing(543)),('sparse-defects',noisy(54)),('random-1MiB',random.Random(20261130).randbytes(N)),('repeat-1MiB',(b'not-a-csv-record!\x00'*N)[:N]),('source-code',b'\n'.join(Path(p).read_bytes() for p in ['trial.py','crcodec/codec.py','crcodec/general.py'])),('odd-length',random.Random(42).randbytes(65537)),('empty',b''),('short',b'abc')]
    rows=[];negative=0
    for name,d in cases:
        sha=hashlib.sha256(d).digest()
        t=time.perf_counter();z=gzip.compress(d,compresslevel=6,mtime=0);gzms=(time.perf_counter()-t)*1000
        assert gzip.decompress(z)==d
        t=time.perf_counter();old,_=v2.encode(d);oldms=(time.perf_counter()-t)*1000;assert v2.decode(old,sha)==d
        t=time.perf_counter();w,m=v3.encode(d);enc=(time.perf_counter()-t)*1000
        t=time.perf_counter();rest=v3.decode(w,sha);dec=(time.perf_counter()-t)*1000
        assert rest==d
        for bad,expected in ((w[:-1],sha),(w+b'X',sha),(w[:10]+bytes([w[10]^1])+w[11:],sha),(w,bytes([sha[0]^1])+sha[1:])):
            try:v3.decode(bad,expected)
            except Exception:negative+=1
            else:raise AssertionError('negative accepted '+name)
        row=dict(case=name,sourceBytes=len(d),sourceSHA256=sha.hex(),gzipBytes=len(z),v2Bytes=len(old),v3Bytes=len(w),encodedSHA256=hashlib.sha256(w).hexdigest(),exact=True,gzipEncodeMs=gzms,v2EncodeMs=oldms,v3EncodeMs=enc,v3DecodeMs=dec,**m)
        rows.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ('sourceSHA256','encodedSHA256','runSample')}),flush=True)
    report=dict(schema='crt-content-boundary-v3',python=sys.version,platform=platform.platform(),sourceLimit=N,roundTrips=len(rows),negativeControls=negative,commercialRuntimeEvaluated=False,timingScope='single in-memory run, encoder search included, fixed order; no disk or transport',rows=rows)
    Path('/tmp/v3-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(rows),negative)
if __name__=='__main__':run()
