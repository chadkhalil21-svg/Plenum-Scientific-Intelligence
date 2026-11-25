"""Synthetic public fixture. No private credentials, no real commercial spend."""
import json,sys,os
from pathlib import Path
from uuid import UUID
from harness import validate_input,execute,verify,exclusive,digest
from synthesis_smoke import scope,fixture_selection
from synthesis_contract import accept_choice,independent

CASES={"review":("a60d5f45-5570-4e04-9955-09d199ef9f8d",100),"defer":("a62d5f45-5570-4e04-9955-09d199ef9f8d",50)}
def main():
    phase,case,folder=sys.argv[1:]
    if case not in CASES:raise ValueError("Unknown qualification fixture")
    thread,budget=CASES[case]
    s=scope();data=accept_choice(s,fixture_selection(s));result=independent(data)
    ctx=validate_input(data,result,budget,75)
    root=Path(folder)
    if phase in ("run","pause"):root.mkdir(mode=0o700,parents=True,exist_ok=False)
    if phase=="verify":
        row=verify(root,ctx,thread,case)
        if case=="review" and not row["acknowledged_checkpoint_resume"]:raise ValueError("Missing deliberate recovery proof")
        print(json.dumps(row,sort_keys=True))
    else:execute(root,ctx,thread,phase)
if __name__=="__main__":main()
