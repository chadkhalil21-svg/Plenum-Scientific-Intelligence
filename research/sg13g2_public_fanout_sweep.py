#!/usr/bin/env python3
"""PUBLIC textbook fanout/isolation experiment on open IHP SG13G2 model.
No proprietary Plenum/Neumann circuit, component sizes, geometry, stimuli or timing.
Only classic cross-coupled CMOS latch and textbook two-inverter output buffer.
"""
import json, pathlib, subprocess, math
root=pathlib.Path(__file__).resolve().parent
def deck(corner,temp,fanout):
  lines=[
    "PUBLIC generic CMOS latch buffer/fanout benchmark",
    f".lib cornerMOSlv.lib {corner}",f".temp {temp}",
    "VDD vdd 0 1.2",
    "VSET set 0 PWL(0 0 1.000n 0 1.005n 1.2 1.600n 1.2 1.605n 0 6n 0)",
    "VRST rst 0 PWL(0 0 4.000n 0 4.005n 1.2 4.600n 1.2 4.605n 0 6n 0)",
    "* Direct textbook latch with MOS-gate fanout",
    "XDn q_direct qd_bar 0 0 sg13_lv_nmos w=1.0u l=130n ng=1 m=1",
    "XDp q_direct qd_bar vdd vdd sg13_lv_pmos w=2.0u l=130n ng=1 m=1",
    "XDBn qd_bar q_direct 0 0 sg13_lv_nmos w=1.0u l=130n ng=1 m=1",
    "XDBp qd_bar q_direct vdd vdd sg13_lv_pmos w=2.0u l=130n ng=1 m=1",
    "XDSet qd_bar set 0 0 sg13_lv_nmos w=1.2u l=130n ng=1 m=1",
    "XDRst q_direct rst 0 0 sg13_lv_nmos w=1.2u l=130n ng=1 m=1",
    "CD q_direct 0 2f","CDB qd_bar 0 2f",
    "* Isolated textbook latch and two CMOS inverter output buffer",
    "XCn q_core qc_bar 0 0 sg13_lv_nmos w=1.0u l=130n ng=1 m=1",
    "XCp q_core qc_bar vdd vdd sg13_lv_pmos w=2.0u l=130n ng=1 m=1",
    "XCBn qc_bar q_core 0 0 sg13_lv_nmos w=1.0u l=130n ng=1 m=1",
    "XCBp qc_bar q_core vdd vdd sg13_lv_pmos w=2.0u l=130n ng=1 m=1",
    "XCSet qc_bar set 0 0 sg13_lv_nmos w=1.2u l=130n ng=1 m=1",
    "XCRst q_core rst 0 0 sg13_lv_nmos w=1.2u l=130n ng=1 m=1",
    "CC q_core 0 2f","CCB qc_bar 0 2f",
    "XB1n mid q_core 0 0 sg13_lv_nmos w=1.0u l=130n ng=1 m=1",
    "XB1p mid q_core vdd vdd sg13_lv_pmos w=2.0u l=130n ng=1 m=1",
    "XB2n q_out mid 0 0 sg13_lv_nmos w=6.0u l=130n ng=1 m=1",
    "XB2p q_out mid vdd vdd sg13_lv_pmos w=12.0u l=130n ng=1 m=1",
    "CM mid 0 2f","CO q_out 0 2f",
  ]
  for k in range(fanout):
    for pre,node in (("D","q_direct"),("B","q_out")):
      out=f"lo_{pre}_{k}"
      lines.extend([
        f"XLn_{pre}_{k} {out} {node} 0 0 sg13_lv_nmos w=0.8u l=130n ng=1 m=1",
        f"XLp_{pre}_{k} {out} {node} vdd vdd sg13_lv_pmos w=1.6u l=130n ng=1 m=1",
        f"CL_{pre}_{k} {out} 0 1f"])
  lines.extend([
    ".ic v(q_direct)=0 v(qd_bar)=1.2 v(q_core)=0 v(qc_bar)=1.2 v(mid)=1.2 v(q_out)=0",
    ".control","set wr_singlescale","set wr_vecnames",
    "tran 1p 6n 0 1p uic",
    "wrdata sweep-wave.txt v(q_direct) v(q_core) v(q_out)",
    "quit",".endc",".end"])
  return "\n".join(lines)+"\n"
def sample_cross(data,col,threshold,after,increasing):
  prev=data[0]
  for row in data[1:]:
    if row[0]>=after:
      if increasing and prev[col]<threshold<=row[col]:return 1e12*row[0]
      if not increasing and prev[col]>threshold>=row[col]:return 1e12*row[0]
    prev=row
  return None
results=[]
for corner,temp in [("mos_tt",27),("mos_ss",125),("mos_ff",-40)]:
  for fanout in [2,8,24,48]:
    deckpath=root/"sweep.spice";deckpath.write_text(deck(corner,temp,fanout))
    p=subprocess.run(["ngspice","-b","-o","sweep.log",str(deckpath)],
                     cwd=root,capture_output=True,text=True,timeout=150)
    if p.returncode:
      print((root/"sweep.log").read_text(errors="replace")[-3500:])
      raise RuntimeError(f"ngspice failed {corner}, fanout{fanout}, code{p.returncode}")
    data=[]
    for line in (root/"sweep-wave.txt").read_text().splitlines():
      try:
        row=[float(x) for x in line.split()]
        if len(row)>=4:data.append(row)
      except ValueError:pass
    if len(data)<100:raise RuntimeError("not enough native samples")
    times=[sample_cross(data,i,.8,1.005e-9,True) for i in [1,2,3]]
    reset=[sample_cross(data,i,.2,4.005e-9,False) for i in [1,2,3]]
    if any(t is None for t in times+reset):
      raise RuntimeError(f"native incorrect set/reset, {corner}, fanout{fanout}, times{times}, reset{reset}")
    selected=[min(data,key=lambda r:abs(r[0]-t)) for t in [2.5e-9,5e-9]]
    if not all(s[1]>.8 and s[2]>.8 and s[3]>.8 for s in selected[:1]):
      raise RuntimeError("final high must pass")
    if not all(s[1]<.2 and s[2]<.2 and s[3]<.2 for s in selected[1:]):
      raise RuntimeError("final low must pass")
    r={"corner":corner,"temp_C":temp,"fanout_CMOS_inverters":fanout,"native_samples":len(data),
       "direct_output_set_ps":round(times[0],3),"isolated_core_set_ps":round(times[1],3),
       "buffered_output_set_ps":round(times[2],3),
       "direct_output_reset_ps":round(reset[0],3),"isolated_core_reset_ps":round(reset[1],3),
       "buffered_output_reset_ps":round(reset[2],3),
       "output_buffer_minus_direct_set_ps":round(times[2]-times[0],3),
       "internal_isolated_core_minus_direct_set_ps":round(times[1]-times[0],3),
       "pass":True}
    results.append(r)
    print("CORNER_RESULT",json.dumps(r,sort_keys=True))
print("FINAL_RESULT",json.dumps({"experiment":"GENERIC_PUBLIC_IHP_SG13G2_FANOUT_NATIVE_PHYSICS",
"private_neumann_source_used":False,"native_device_model":True,"sampled_runs":len(results),
"all_cases_pass":True,"comparisons":results},sort_keys=True))
