// CRT151: monitoring-only ablation of the CRT1411 paired experiment.
// Three builders share ONE Session (identical authenticated revisions):
//   rehash    : per-build compiler-executable rehash, no monitor   (CRT1411 baseline)
//   pinned    : session file pins, no per-build rehash, no monitor (NEW ablation arm)
//   monitored : the SAME file pins plus the debug-event execution gate (CRT1411 monitored)
// pinned and monitored pin the identical file set (compiler + every policy entry +
// gate + policy file), so per build they differ ONLY in the monitoring step
// (gated launch plus staged, read-locked source). Arm order rotates through all six
// permutations by revision, so each pair of arms runs in both orders equally often.
#define CRT148_NO_MAIN
#include "crt148_select.cpp"
#include <array>
#include <fstream>
#include <iostream>
#include <sstream>
#include <iomanip>
#include <vector>
namespace {
struct Step {std::string receipt,root,raw,first;U groups=0,trial=0;};
std::vector<Step> read_plan151(const std::string&p){
 std::ifstream in(p);if(!in)throw std::runtime_error("missing step plan");
 std::vector<Step>out;std::string line;
 while(std::getline(in,line)){if(line.empty())continue;std::istringstream ss(line);std::vector<std::string>v;std::string part;
  while(std::getline(ss,part,'\t'))v.push_back(part);
  if(v.size()!=6)throw std::runtime_error("bad plan row");
  Step s; s.receipt=v[0];s.root=v[1];s.raw=v[2];s.first=v[5];s.groups=std::stoull(v[3]);s.trial=std::stoull(v[4]);out.push_back(s);
 }return out;
}
// Same pin set the monitored builder takes from the policy, plus gate and policy file.
std::vector<std::pair<std::string,Digest>> policy_pins(const std::string&policy,const Digest&policy_sha,const std::string&gate,const Digest&gate_sha){
 if(hash_file(policy)!=policy_sha)throw std::runtime_error("allowlist anchor mismatch");
 std::ifstream input(policy);if(!input)throw std::runtime_error("missing scoped policy");
 std::vector<std::pair<std::string,Digest>> out;std::string line;
 while(std::getline(input,line)){
  if(line.empty())continue;
  auto a=line.find('\t'),b=(a==std::string::npos?std::string::npos:line.find('\t',a+1));
  if(a==std::string::npos||b==std::string::npos)throw std::runtime_error("allowlist must contain ID, path, SHA256");
  auto sha=line.substr(b+1);if(sha.size()!=64)throw std::runtime_error("malformed policy digest");
  out.push_back({line.substr(a+1,b-a-1),unhex(sha)});
 }
 if(out.empty())throw std::runtime_error("empty monitored allowlist");
 out.push_back({gate,gate_sha});out.push_back({policy,policy_sha});
 return out;
}
void emit151(const Step&s,U step,const std::string&strategy,const std::string&mode,U position,const std::string&order,const std::string&out,const Result&r,double wall,double patch){
 std::cout<<std::fixed<<std::setprecision(5)
  <<"CRT151_ROW {\"step\":"<<step<<",\"trial\":"<<s.trial<<",\"groups\":"<<s.groups
  <<",\"strategy\":"<<json_string(strategy)<<",\"mode\":"<<json_string(mode)
  <<",\"position\":"<<position<<",\"order\":"<<json_string(order)
  <<",\"identity_ms\":"<<r.compiler_identity_ms<<",\"compile_ms\":"<<r.compilation_ms
  <<",\"cache_check_ms\":"<<r.cache_validation_ms<<",\"link_ms\":"<<r.link_ms
  <<",\"build_wall_ms\":"<<wall<<",\"proof_patch_ms\":"<<patch
  <<",\"launched_peak_kib\":"<<r.max_compiler_peak<<",\"link_launched_peak_kib\":"<<r.link_peak
  <<",\"compiled\":"<<r.compiled<<",\"reused\":"<<r.reused
  <<",\"output\":"<<json_string(out)<<",\"raw\":"<<json_string(s.raw)
  <<",\"root\":"<<json_string(s.root)<<"}"<<std::endl;
}
}
int main(int argc,char**argv){try{
 auto raw=field("--base-raw",argc,argv),state=field("--base-state",argc,argv),plan=field("--steps",argc,argv);
 auto tr=field("--trusted-raw-sha",argc,argv),ts=field("--trusted-source-sha",argc,argv),root=field("--trusted-base-root",argc,argv);
 auto compiler=field("--compiler",argc,argv,"clang++"),dir=field("--cache",argc,argv),verifier=field("--verifier-obj",argc,argv);
 auto sha=field("--trusted-compiler-sha",argc,argv),gate=field("--execution-gate",argc,argv),gate_sha=field("--trusted-gate-sha",argc,argv);
 auto policy=field("--execution-policy",argc,argv),policy_sha=field("--trusted-policy-sha",argc,argv);
 if(raw.empty()||state.empty()||plan.empty()||tr.empty()||ts.empty()||root.empty()||dir.empty()||verifier.empty()||sha.empty()||gate.empty()||gate_sha.empty()||policy.empty()||policy_sha.empty())throw std::runtime_error("missing rooted source or toolchain anchors");
 Session session(raw,state,unhex(tr),unhex(ts),unhex(root));
 Builder rehash(session,compiler,(std::filesystem::path(dir)/"rehash").string(),64,verifier);
 Builder pinned(session,compiler,(std::filesystem::path(dir)/"pinned").string(),64,verifier);
 Builder monitored(session,compiler,(std::filesystem::path(dir)/"monitored").string(),64,verifier);
 if(rehash.compiler_digest!=unhex(sha)||pinned.compiler_digest!=unhex(sha)||monitored.compiler_digest!=unhex(sha))throw std::runtime_error("compiler identity anchor mismatch");
 pinned.start_experimental_pin(policy_pins(policy,unhex(policy_sha),gate,unhex(gate_sha)));
 monitored.start_monitored_execution(gate,unhex(gate_sha),policy,unhex(policy_sha),{});
 auto arm=[&](const std::string&w)->Builder&{return w=="rehash"?rehash:(w=="pinned"?pinned:monitored);};
 auto begin=Clock::now();
 for(const std::string w:{"rehash","pinned","monitored"}){
  Builder&b=arm(w);active_execution_gate.enabled=(w=="monitored");
  auto r=b.build({},(std::filesystem::path(dir)/(w+"_base.exe")).string());
  auto x=b.build_whole((std::filesystem::path(dir)/(w+"_base_whole.exe")).string());b.calibrate(r,x);
 }
 std::cout<<"CRT151_SETUP {\"calibration_wall_ms\":"<<milli(begin,Clock::now())<<"}"<<std::endl;
 const std::array<std::array<const char*,3>,6> orders{{
  {"rehash","pinned","monitored"},{"pinned","monitored","rehash"},{"monitored","rehash","pinned"},
  {"rehash","monitored","pinned"},{"monitored","pinned","rehash"},{"pinned","rehash","monitored"}}};
 auto steps=read_plan151(plan);U step=0;
 for(auto&s:steps){
  const auto indices=changed_indices(s.receipt);
  auto at=Clock::now();U changed=session.apply(s.receipt,unhex(s.root));double patch=milli(at,Clock::now());
  if(changed!=s.groups||indices.size()!=s.groups)throw std::runtime_error("rooted change-count mismatch");
  for(const std::string w:{"rehash","pinned","monitored"})
   if(arm(w).predict(indices,"auto").cache_miss_groups!=s.groups)throw std::runtime_error("unexpected cache population");
  const auto&ord=orders[step%6];
  const std::string order=std::string(ord[0])+">"+ord[1]+">"+ord[2];
  for(auto&mode:{s.first,(s.first=="whole"?std::string("fragment"):std::string("whole"))}){
   U position=0;
   for(const char* c:ord){
    const std::string which(c);Builder&b=arm(which);
    active_execution_gate.enabled=(which=="monitored");
    auto out=(std::filesystem::path(dir)/("crt151_"+std::to_string(step)+"_"+mode+"_"+which+".exe")).string();
    const auto tick=Clock::now();auto r=(mode=="whole"?b.build_whole(out):b.build(indices,out));double wall=milli(tick,Clock::now());
    if(mode=="fragment"&&(r.compiled!=s.groups||r.reused!=b.groups.size()-s.groups))throw std::runtime_error("invalid cache-reuse accounting");
    emit151(s,step,which,mode,position++,order,out,r,wall,patch);
   }
  }
  step++;
 }
 active_execution_gate.enabled=false;
 std::cout<<"CRT151_DONE {\"revisions\":"<<step<<",\"builds\":"<<step*6<<",\"final_root\":\""<<hex(session.current)<<"\"}"<<std::endl;
 return 0;
}catch(const std::exception&e){std::cerr<<"CRT151_REJECTED "<<e.what()<<std::endl;return 1;}}
