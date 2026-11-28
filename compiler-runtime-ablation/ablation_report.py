#!/usr/bin/env python3
"""CRT151 monitoring-only ablation report.

Runs crt151_monitor_ablation.exe over the same rooted revisions as CRT1411, verifies
every output executable natively, and reports paired per-revision differences:
  monitored - pinned : cost of the monitoring step alone (same pins, same identity path)
  rehash    - pinned : cost of per-build compiler rehash
  rehash - monitored : replication of the published CRT1411 comparison
Each difference is also split by which arm of the pair ran first, so an order
(cache/thermal drift) effect is visible instead of averaged away."""
import argparse,hashlib,json,statistics,subprocess,sys
from pathlib import Path

def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def stats(v):
 if not v:return None
 q=statistics.quantiles(v,n=4) if len(v)>=4 else [min(v),statistics.median(v),max(v)]
 return {'n':len(v),'median_ms':statistics.median(v),'q1_ms':q[0],'q3_ms':q[2],'mean_ms':statistics.fmean(v),'positive':sum(x>0 for x in v)}

def main():
 p=argparse.ArgumentParser()
 for k in ('driver','manifest','verifier-object','compiler','gate','policy','work','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args();m=json.loads(Path(a.manifest).read_text());work=Path(a.work).resolve();work.mkdir(parents=True,exist_ok=True)
 cmd=[str(Path(a.driver).resolve()),'--base-raw',m['base_raw'],'--base-state',m['base_state'],
  '--trusted-raw-sha',m['base_raw_sha'],'--trusted-source-sha',m['base_source_sha'],'--trusted-base-root',m['base_root'],
  '--steps',m['steps_tsv'],'--cache',str(work/'cache'),'--verifier-obj',str(Path(a.verifier_object).resolve()),
  '--compiler',str(Path(a.compiler).resolve()),'--trusted-compiler-sha',digest(a.compiler),
  '--execution-gate',str(Path(a.gate).resolve()),'--trusted-gate-sha',digest(a.gate),
  '--execution-policy',str(Path(a.policy).resolve()),'--trusted-policy-sha',digest(a.policy)]
 rows=[];done=None;setup=None;first_rejection=None;event_count=0
 events_path=Path(a.output).with_name('execution_monitor_events.jsonl');events_path.parent.mkdir(parents=True,exist_ok=True)
 expected=len(m['steps'])*6
 with events_path.open('w',encoding='utf-8') as log, subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1) as proc:
  for line in proc.stdout:
   if line.startswith('{'):
    try:event=json.loads(line)
    except json.JSONDecodeError:event={'kind':'unparsed','raw':line.rstrip('\r\n')}
    log.write(json.dumps(event,ensure_ascii=False)+'\n');event_count+=1
    if first_rejection is None and (str(event.get('decision','')).startswith('reject_') or (event.get('kind')=='verdict' and not event.get('accepted',True)) or event.get('kind')=='fatal'):first_rejection=event
    continue
   if line.startswith('CRT151_ROW '):
    rows.append(json.loads(line.partition(' ')[2]))
    if len(rows)%36==0:print('CRT151_PROGRESS',len(rows),'/',expected,flush=True)
   elif line.startswith('CRT151_SETUP '):setup=json.loads(line.partition(' ')[2])
   elif line.startswith('CRT151_DONE '):done=json.loads(line.partition(' ')[2])
   elif line.startswith('CRT151_'):print(line.strip(),flush=True)
  error=proc.stderr.read();rc=proc.wait()
 cells={}
 for r in rows:cells.setdefault((r['step'],r['mode']),{})[r['strategy']]=r
 complete=bool(rc==0 and done and len(rows)==expected and all(len(v)==3 for v in cells.values()))
 checks=0
 if complete:
  for r in rows:
   q=subprocess.run([r['output'],r['raw']],capture_output=True,text=True,timeout=60)
   if q.returncode:raise RuntimeError('native executable rejected: '+r['output']+' '+q.stderr[-200:])
   z=json.loads(q.stdout.strip().splitlines()[-1])
   if z.get('match') is not True or z.get('verified_native_calls')!=34816:raise RuntimeError('independent source check mismatch '+r['output'])
   checks+=1
 contrasts={'monitored_minus_pinned':('monitored','pinned'),'rehash_minus_pinned':('rehash','pinned'),'rehash_minus_monitored':('rehash','monitored')}
 summary={}
 for mode in ('whole','fragment'):
  summary[mode]={}
  for name,(x,y) in contrasts.items():
   for field in ('build_wall_ms','compile_ms','link_ms','identity_ms'):
    allv=[];xfirst=[];yfirst=[]
    for (st,md),v in sorted(cells.items()):
     if md!=mode or len(v)!=3:continue
     d=v[x][field]-v[y][field];allv.append(d)
     (xfirst if v[x]['position']<v[y]['position'] else yfirst).append(d)
    summary[mode].setdefault(name,{})[field]={'all':stats(allv),x+'_ran_first':stats(xfirst),y+'_ran_first':stats(yfirst)}
  summary[mode]['arm_medians_ms']={arm:{f:statistics.median([v[arm][f] for (st,md),v in cells.items() if md==mode and len(v)==3]) for f in ('build_wall_ms','compile_ms','link_ms','identity_ms')} for arm in ('rehash','pinned','monitored')} if complete else None
 report={'status':'complete' if complete else 'failed','schema':'crt151.monitor-ablation.v1','setup':setup,
  'design':{'arms':{'rehash':'per-build compiler-executable rehash, no monitor','pinned':'session file pins (compiler + every policy entry + gate + policy), no rehash, no monitor','monitored':'same pins plus debug-event execution gate with staged read-locked source'},
   'isolated_factor':'monitored - pinned differs only in the monitoring step (gated launch + staged source)',
   'order':'six permutations of the three arms rotated by revision; each pairwise order occurs equally often','revisions':len(m['steps']),'modes':['whole','fragment']},
  'paired_contrasts':summary,'native_execution_checks':checks,
  'peak_memory_note':'launched_peak_kib is PeakWorkingSetSize of the directly launched process: the compiler/linker for rehash and pinned, but the gate process for monitored. It is therefore NOT a comparable peak-memory measurement across arms.',
  'raw_rows':rows,'monitor_events_path':str(events_path),'monitor_events_count':event_count,'first_monitor_rejection':first_rejection,'security_acceptance_met':False}
 if not complete:report['error']={'returncode':rc,'stderr_tail':(error or '')[-2000:],'observed_rows':len(rows),'first_monitor_rejection':first_rejection}
 out=Path(a.output);out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 brief={md:{k:(summary[md][k]['build_wall_ms']['all'] or {}).get('median_ms') for k in contrasts} for md in summary}
 print('CRT151_SUMMARY',json.dumps({'status':report['status'],'median_wall_diffs_ms':brief,'native_checks':checks}))
 return 0 if complete else 1
if __name__=='__main__':sys.exit(main())
