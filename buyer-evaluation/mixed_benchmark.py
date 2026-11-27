import hashlib, json, random, tempfile, statistics, platform, sys, gzip, time, struct
from pathlib import Path
from crcodec import general,codec
from trial import run
SIZE=1024*1024
SEEDS=[20261127,20261128,20261129]
BLOCKS=[512,4096,65536]
REPS=3
def fixture(block,seed):
    rng=random.Random(seed)
    parts=[]
    for i in range(SIZE//block):
        if i%2:parts.append(rng.randbytes(block))
        else:
            # Counter varies by structured block; identical 25-byte records within each block.
            record=f"alpha,blue,{i//2:010d},17\n".encode()
            parts.append((record*((block+len(record)-1)//len(record)))[:block])
    return b''.join(parts)
def main():
    rows=[]
    for b in BLOCKS:
        for seed in SEEDS:
            d=fixture(b,seed);assert len(d)==SIZE
            runs=[]
            for rep in range(REPS):
                with tempfile.TemporaryDirectory() as td:
                    r=run(d,Path(td))
                    runs.append(r['results'])
            for i,entry in enumerate(runs[0]):
                if entry.get('applicable') is False:
                    rows.append(dict(blockBytes=b,seed=seed,codec=entry['codec'],applicable=False,reason=entry['reason']))
                    continue
                vals=[rr[i] for rr in runs]
                assert all(x['roundTripExact'] and x['decodedSha256']==hashlib.sha256(d).hexdigest() for x in vals)
                assert len({x['encodedBytes'] for x in vals})==1
                rows.append(dict(blockBytes=b,seed=seed,codec=entry['codec'],sourceBytes=len(d),sourceSha256=hashlib.sha256(d).hexdigest(),encodedBytes=entry['encodedBytes'],encodedSha256=entry['encodedSha256'],exact=True,encodeMsMedian=statistics.median(x['encodeMs'] for x in vals),decodeMsMedian=statistics.median(x['decodeMs'] for x in vals),encodeMsAll=[x['encodeMs'] for x in vals],decodeMsAll=[x['decodeMs'] for x in vals]))
    report={'schema':'crt-mixed-workload-v1','trialSHA256':'192740a5b119e02bf3b1fc991124c90564857dc7a3e0095eac3a79eab2ba7905','python':sys.version,'platform':platform.platform(),'repetitions':REPS,'sourceBytes':SIZE,'seeds':SEEDS,'blockSizes':BLOCKS,'timingScope':'published trial: local writes and fsync, fixed codec order, not transport; excludes generation','commercialRuntimeEvaluated':False,'rows':rows}
    Path('/tmp/mixed-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main()
