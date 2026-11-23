#!/usr/bin/env python3
"""Public generic SG13G2 short-pulse CMOS latch test. No private circuit or secret timing."""
import json, pathlib, subprocess, importlib.util, math
p=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("sg13",p/"sg13g2_public_fanout_sweep.py")
m=importlib.util.module_from_spec(spec)
# Import by extracting only the deck function; source file also launches standalone PVT jobs.
import ast
source=(p/"sg13g2_public_fanout_sweep.py").read_text()
parsed=ast.parse(source)
fn=next(x for x in parsed.body if isinstance(x,ast.FunctionDef) and x.name=="deck")
ns={}
exec(compile(ast.Module(body=[fn],type_ignores=[]),"<public-latch-deck>",'exec'),ns)
deck=ns["deck"]
results=[]
for corner,temp in [("mos_tt",27),("mos_ss",125),("mos_ff",-40)]:
 for fanout in [8,24,48]:
  for pulse_ps in [20,60,120,240]:
   s=deck(corner,temp,fanout)
   # generic standard wave form, shifted only in rise/fall duration
   assert "1.600n 1.2 1.605n 0" in s
   s=s.replace("1.600n 1.2 1.605n 0",f"{(1.005+pulse_ps/1000):.3f}n 1.2 {(1.010+pulse_ps/1000):.3f}n 0")
   (p/"pulse.spice").write_text(s)
   run=subprocess.run(["ngspice","-b","-o","pulse.log","pulse.spice"],cwd=p,capture_output=True,text=True,timeout=100)
   if run.returncode:
    raise RuntimeError(f"{corner} fanout{fanout} pulse{pulse_ps} NGSPICE failed "+(p/"pulse.log").read_text(errors="replace")[-1000:])
   rows=[]
   for line in (p/"sweep-wave.txt").read_text().splitlines():
    try:
     v=[float(x) for x in line.split()]
     if len(v)>=4:rows.append(v)
    except ValueError:pass
   if not rows:raise RuntimeError("Native transient empty")
   sample=min(rows,key=lambda x:abs(x[0]-2.5e-9))
   reset=min(rows,key=lambda x:abs(x[0]-5.0e-9))
   x={"corner":corner,"temp_C":temp,"fanout":fanout,"pulse_ps":pulse_ps,
      "direct_set":float(sample[1]),"core_set":float(sample[2]),"buffered_set":float(sample[3]),
      "direct_reset":float(reset[1]),"core_reset":float(reset[2]),"buffered_reset":float(reset[3]),
      "direct_set_valid":bool(sample[1]>.8),"buffered_set_valid":bool(sample[3]>.8),
      "direct_reset_valid":bool(reset[1]<.2),"buffered_reset_valid":bool(reset[3]<.2)}
   results.append(x)
   print("PULSE_CASE",json.dumps(x,sort_keys=True))
summary={"experiment":"PUBLIC IHP SG13G2 short-pulse direct-vs-buffered CMOS latch; NONPROPRIETARY",
         "number_native_transients":len(results),"all_results":results,
         "direct_both_pass":sum(r["direct_set_valid"] and r["direct_reset_valid"] for r in results),
         "buffered_both_pass":sum(r["buffered_set_valid"] and r["buffered_reset_valid"] for r in results),
         "private_design_run":False,"formal_neumann_gate_closed":False}
print("PULSE_FINAL",json.dumps(summary,sort_keys=True))
