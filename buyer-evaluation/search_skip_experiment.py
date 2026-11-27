"""Search-cost experiment: CRTG4 encoder with adaptive skipping after failed discovery.
After `k` consecutive failed positions the next probe advances by min(2**k_level, MAX_SKIP).
The wire format and decoder are unchanged (output decodes with grammar_v4.decode);
only which runs the encoder finds can change. Python 3.11+."""
import gzip,hashlib,json,time
from pathlib import Path
import grammar_v4 as v4
import benchmark_v4 as b4

def encode_skip(d,max_skip):
    v3=v4.v3
    header=v4.MAGIC+v4.uvar(len(d))+hashlib.sha256(d).digest()
    out=bytearray(header);i=start=0;prev=None;fails=0
    while i+v4.MIN_RUN<=len(d):
        r=v3.discover(d,i)
        if r is None:
            fails+=1;i+=min(max_skip,1<<min(fails//8,8));continue
        n,unit=r;n,exc=v4.extend(d,i,unit,n)
        cmd,mode=v4.run_cmd(n,unit,prev,exc)
        if len(cmd)+2>=n:fails+=1;i+=1;continue
        lit,lm=v3.literal(d[start:i])
        if lm:out+=lit
        out+=cmd;prev=unit;i+=n;start=i;fails=0
    lit,lm=v3.literal(d[start:])
    if lm:out+=lit
    fb,fm=v3.literal(d)
    if len(header)+len(fb)<len(out):out=bytearray(header+fb)
    return bytes(out)

def main():
    rows=[]
    cases=b4.primary()+b4.extra()
    for max_skip in (1,4,16):
        tot=0;ms=0;worse=[]
        for name,d in cases:
            sha=hashlib.sha256(d).digest()
            t=time.perf_counter();w=encode_skip(d,max_skip);e=(time.perf_counter()-t)*1000
            assert v4.decode(w,sha)==d,(name,max_skip)
            tot+=len(w);ms+=e
            rows.append(dict(maxSkip=max_skip,case=name,bytes=len(w),encodeMs=round(e,1)))
        print(f'maxSkip={max_skip:>2}: total {tot:,} B across {len(cases)} cases, encode total {ms:,.0f} ms')
    base={r['case']:r for r in rows if r['maxSkip']==1}
    for r in rows:
        if r['maxSkip']>1 and r['bytes']!=base[r['case']]['bytes']:
            print(f"  skip {r['maxSkip']:>2} {r['case']:24} {base[r['case']]['bytes']:>9,} -> {r['bytes']:>9,} B; {base[r['case']]['encodeMs']:>7} -> {r['encodeMs']:>7} ms")
    slow=[(r['case'],base[r['case']]['encodeMs'],r['encodeMs']) for r in rows if r['maxSkip']==16 and base[r['case']]['encodeMs']>300]
    for c,a,b in slow:print(f'  time {c:24} {a:>7} -> {b:>7} ms')
    Path('search_skip_experiment_20261127.json').write_text(json.dumps(rows,indent=2)+'\n')

if __name__=='__main__':main()
