"""Where do CRTG4's remaining losses come from? Measurement only, no codec change.
Estimates the cost of candidate constructive relationships on the two worst cases.
Run beside the trial and benchmark files. Python 3.11+."""
import gzip,hashlib,json,time
from pathlib import Path
from crcodec.codec import uvar
import grammar_v4 as v4
import benchmark_v4 as b4

def vlen(x):return len(uvar(x))

def source_case():
    return b'\n'.join(Path(p).read_bytes() for p in ['trial.py','crcodec/codec.py','crcodec/general.py'])

def line_relations(d):
    """Relationship A: a line equal to an earlier line (by index).
    Relationship B: a line equal to the previous line with k byte exceptions (same length)."""
    lines=d.split(b'\n');seen={};exact=exact_bytes=0;near=0;near_cost=0;lit_bytes=0
    prev=None
    for idx,l in enumerate(lines):
        if l in seen and len(l)>=4:exact+=1;exact_bytes+=len(l)
        elif prev is not None and len(prev)==len(l) and l:
            diffs=[k for k in range(len(l)) if l[k]!=prev[k]]
            if len(diffs)*2+2<len(l):near+=1;near_cost+=2+2*len(diffs)
            else:lit_bytes+=len(l)
        else:lit_bytes+=len(l)
        seen.setdefault(l,idx);prev=l
    return dict(lines=len(lines),exactRepeatLines=exact,exactRepeatBytes=exact_bytes,
                nearPrevLines=near,nearPrevCost=near_cost,remainingLiteralBytes=lit_bytes)

def field_relations(d):
    """Relationship C: per-line fields that are previous value + constant step (counters)."""
    lines=d.split(b'\n')[:-1]
    def fields(l):return l.replace(b'=',b' ').replace(b':',b' ').split(b' ')
    prev=None;stepped=same=other=0;steps={}
    for l in lines:
        f=fields(l)
        if prev and len(prev)==len(f):
            for k,(a,b) in enumerate(zip(prev,f)):
                if a==b:same+=1;continue
                if a.isdigit() and b.isdigit() and len(a)==len(b):
                    s=int(b)-int(a);steps.setdefault(k,{}).setdefault(s,0);steps[k][s]+=1
                    stepped+=1
                else:other+=1
        prev=f
    common={k:max(v.items(),key=lambda kv:kv[1]) for k,v in steps.items()}
    return dict(lines=len(lines),unchangedFields=same,numericChangedFields=stepped,otherChangedFields=other,
                dominantStepPerField={str(k):dict(step=s,count=c) for k,(s,c) in common.items()})

def main():
    out={}
    for name,d in (('source-code',source_case()),('log-lines',b4.log_lines(80))):
        z=len(gzip.compress(d,6,mtime=0))
        t=time.perf_counter();w,m=v4.encode(d);enc=(time.perf_counter()-t)*1000
        lit=sum(1 for _ in [0])
        row=dict(sourceBytes=len(d),gzip6=z,crtg4=len(w),crtg4Modes=m['modes'],crtg4Runs=m['periodicRuns'],encodeMs=round(enc),
                 lineRelations=line_relations(d))
        if name=='log-lines':row['fieldRelations']=field_relations(d)
        out[name]=row
    # Search-cost probe: how many discover() calls fail on log-lines?
    d=b4.log_lines(80);calls=fails=0;i=0
    t=time.perf_counter()
    while i+v4.MIN_RUN<=len(d) and calls<20000:
        calls+=1;r=v4.v3.discover(d,i)
        if r is None:fails+=1;i+=1
        else:i+=r[0]
    out['log-lines']['searchProbe']=dict(discoverCalls=calls,failed=fails,ms=round((time.perf_counter()-t)*1000),
        note='first 20,000 positions only; every failed call scans up to 128+8 bytes for an anchor')
    print(json.dumps(out,indent=2))
    Path('loss_analysis_v4_20261127.json').write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__':main()
