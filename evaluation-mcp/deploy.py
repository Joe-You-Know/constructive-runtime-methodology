"""Deploy reviewed public evaluation source only to the separate CPU Basic Space."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
from huggingface_hub import HfApi, CommitOperationAdd

ROOT=Path(__file__).resolve().parent
FILES=("app.py","grammar_v3.py","grammar_v4.py","trial.zip.b64","benchmark-summary.json","requirements.txt","README.md","test_evaluation.py")
p=argparse.ArgumentParser()
p.add_argument("--expected-sha",required=True)
a=p.parse_args()
subprocess.run([sys.executable,"-m","unittest","-v","test_evaluation"],cwd=ROOT,check=True)
api=HfApi()
repo="joe-you-know/crt-evaluation-mcp"
info=api.repo_info(repo_id=repo,repo_type="space")
if info.sha != a.expected_sha or info.private:
    raise SystemExit("Expected public Space revision mismatch; not deployed")
runtime=api.get_space_runtime(repo_id=repo)
if runtime.hardware not in (None,"cpu-basic") or runtime.requested_hardware not in (None,"cpu-basic"):
    raise SystemExit("Hardware not CPU Basic; no deployment")
result=api.create_commit(repo_id=repo,repo_type="space",parent_commit=info.sha,
    operations=[CommitOperationAdd(path_in_repo=f,path_or_fileobj=str(ROOT/f)) for f in FILES],
    commit_message="Deploy public CRTG4 evaluation MCP (no commerce credentials)")
print("Deployed revision:",result.oid)
