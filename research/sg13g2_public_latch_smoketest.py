#!/usr/bin/env python3
"""Public, generic SG13G2 textbook SR latch benchmark; no private circuit, data or claims."""
import pathlib, subprocess, math, json
root=pathlib.Path(__file__).resolve().parent
deck="""Generic textbook CMOS SR latch (public).
.lib cornerMOSlv.lib mos_tt
VDD vdd 0 1.2
VSET set 0 PWL(0 0 1.0n 0 1.005n 1.2 1.6n 1.2 1.605n 0 6n 0)
VRST rst 0 PWL(0 0 3.0n 0 3.005n 1.2 3.6n 1.2 3.605n 0 6n 0)
XQN q qb 0 0 sg13_lv_nmos w=1.0u l=130n ng=1 m=1
XQP q qb vdd vdd sg13_lv_pmos w=2.0u l=130n ng=1 m=1
XQBN qb q 0 0 sg13_lv_nmos w=1.0u l=130n ng=1 m=1
XQBP qb q vdd vdd sg13_lv_pmos w=2.0u l=130n ng=1 m=1
XR q rst 0 0 sg13_lv_nmos w=1.2u l=130n ng=1 m=1
XS qb set 0 0 sg13_lv_nmos w=1.2u l=130n ng=1 m=1
CQ q 0 2f
CQB qb 0 2f
.ic v(q)=0 v(qb)=1.2
.control
set wr_singlescale
set wr_vecnames
tran 1p 6n 0 1p uic
wrdata baseline-waveform.txt v(q) v(qb) v(set) v(rst)
quit
.endc
.end
"""
deckpath=root/"baseline.spice";deckpath.write_text(deck)
p=subprocess.run(["ngspice","-b","-o","baseline.log",str(deckpath)],cwd=root,
                 capture_output=True,text=True,timeout=200)
print("ngspice_exit",p.returncode);print("stdout_tail",p.stdout[-1200:]);
if (root/"baseline.log").exists(): print("simulator_log_tail",(root/"baseline.log").read_text(errors="replace")[-2200:])
if p.returncode:raise SystemExit(p.returncode)
data=[]
for line in (root/"baseline-waveform.txt").read_text().splitlines():
  try:
    vals=[float(v) for v in line.split()]
    if len(vals)>=3: data.append(vals)
  except ValueError:pass
if len(data)<100:raise RuntimeError("Insufficient transient waveform samples")
def sample(t):
  return min(data,key=lambda r:abs(r[0]-t))
s=sample(2.5e-9);r=sample(4.5e-9)
assert math.isfinite(s[1]) and math.isfinite(s[2]) and math.isfinite(r[1]) and math.isfinite(r[2])
print("RESULT",json.dumps({"kind":"GENERIC_PUBLIC_IHP_SG13G2_PDK_LATCH_ONLY",
 "samples":len(data),"set_t_sec":s[0],"set_q":s[1],"set_qb":s[2],
 "reset_t_sec":r[0],"reset_q":r[1],"reset_qb":r[2],
 "set_pass":s[1]>.7 and s[2]<.5,
 "reset_pass":r[1]<.5 and r[2]>.7,
 "private_proprietary_circuit_executed":False},sort_keys=True))
assert s[1]>.7 and s[2]<.5,"Generic SR set failed"
assert r[1]<.5 and r[2]>.7,"Generic SR reset failed"
print("ACCEPTED: PUBLIC GENERIC PDK LATCH SMOKE TEST; NOT PRIVATE NEUMANN RECEIVER")
