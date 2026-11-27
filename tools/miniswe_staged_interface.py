"""Opt-in agent-computer interface for the original isolated mini-SWE executor.

Inspired by SWE-agent's structured editing and independent evaluation. No new
model, service, agent, shell authority or historical inference replay.
"""
import ast
import hashlib
import json
import re
import shlex
from pathlib import Path

MAX_SOURCE = 12000
MAX_FRAGMENT = 6000
EDIT_SCRIPT = """import ast,json,sys
from pathlib import Path
p=Path(sys.argv[1])
d=json.loads(sys.argv[2])
if not p.is_file() or p.is_symlink(): raise ValueError("invalid source")
s=p.read_text()
if len(s.encode())>12000 or s.count(d["old"])!=1: raise ValueError("old fragment must match once")
n=s.replace(d["old"],d["new"],1)
if n==s or len(n.encode())>12000: raise ValueError("invalid edit size or unchanged")
ast.parse(n)
p.write_text(n)
print("Exact source replacement applied")
"""

class StagedInterface:
    """Upstream still plans and calls tools; only its action vocabulary changes."""
    def __init__(self, env, source, test, original, receipt):
        if not re.fullmatch(r"src/plenum_ai/[a-z][a-z0-9_]{1,64}\.py",source):
            raise ValueError("invalid source")
        if not re.fullmatch(r"test_[a-z0-9_]+\.py",test):
            raise ValueError("invalid test")
        if not 0<len(original)<=MAX_SOURCE:
            raise ValueError("source exceeds staged interface bound")
        self.env,self.source,self.test,self.receipt=env,source,test,Path(receipt)
        self.edits=0
        self.views=0
        self.passed=False
        self.actions=0
        self.original_sha=hashlib.sha256(original).hexdigest()

    def __getattr__(self,name):
        return getattr(self.env,name)

    def _record(self,kind,rc):
        with self.receipt.open("a",encoding="utf-8") as f:
            f.write(json.dumps({"ordinal":self.actions,"action":kind,
                "returncode":rc,"edits":self.edits,"regression_passed":self.passed})+"\n")

    def _reject(self,why):
        self._record("rejected",1)
        return {"returncode":1,"output":why,"exception_info":""}

    def execute(self,action,**kwargs):
        self.actions+=1
        if self.actions>12:
            return self._reject("Action budget exhausted.")
        raw=action.get("command")
        if not isinstance(raw,str) or len(raw)>24000:
            return self._reject("Send one bounded JSON action, not shell.")
        try:
            d=json.loads(raw)
        except (ValueError,RecursionError):
            return self._reject('Use JSON: {"op":"replace","old":"exact old text","new":"new text"}.')
        if not isinstance(d,dict):
            return self._reject("Use an action object.")
        op=d.get("op")
        if op=="view" and set(d)=={"op","start","end"}:
            a,b=d["start"],d["end"]
            if self.views>=2 or type(a) is not int or type(b) is not int or not 1<=a<=b<=1000 or b-a>80:
                return self._reject("View allowance exhausted or invalid. Use the supplied source and replace.")
            self.views+=1
            result=self.env.execute({"command":f"sed -n '{a},{b}p' {shlex.quote(self.source)}"})
        elif op=="replace" and set(d)=={"op","old","new"}:
            old,new=d["old"],d["new"]
            if not isinstance(old,str) or not isinstance(new,str) or not 0<len(old)<=MAX_FRAGMENT or len(new)>MAX_FRAGMENT or old==new:
                return self._reject("Replacement must be bounded and change a unique fragment.")
            command="python -B -c "+shlex.quote(EDIT_SCRIPT)+" "+shlex.quote(self.source)+" "+shlex.quote(json.dumps({"old":old,"new":new}))
            result=self.env.execute({"command":command})
            if result["returncode"]==0:
                self.edits+=1
                self.views=0
                self.passed=False
                checked=self.env.execute({"command":"python -B -m unittest discover -s tests -p "+self.test})
                self.passed=checked["returncode"]==0
                result={"returncode":checked["returncode"],"output":result["output"]+"\nAutomatic focused regression:\n"+checked["output"],"exception_info":checked.get("exception_info","")}
        elif op=="submit" and set(d)=={"op"}:
            if not self.edits or not self.passed:
                return self._reject("A successful changed-source regression is required before submission.")
            self._record("submit",0)
            return self.env.execute({"command":"echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"})
        else:
            return self._reject("Only view, exact replace and submit are allowed. Every successful edit runs regression automatically.")
        self._record(op,result["returncode"])
        return result

def staged_task(task,original):
    return (task+"\nThe original editable source is supplied below. Your bash tool's command argument now accepts ONLY "
        "a JSON string encoding one action: {\\\"op\\\":\\\"replace\\\",\\\"old\\\":\\\"exact unique source fragment\\\",\\\"new\\\":\\\"replacement\\\"}, "
        "{\\\"op\\\":\\\"view\\\",\\\"start\\\":1,\\\"end\\\":30}, or {\\\"op\\\":\\\"submit\\\"}. "
        "Use replace promptly; every successful replacement automatically runs existing focused regressions and returns feedback. "
        "At most two views between edits. Submit only after passing regression. Independent hidden acceptance still applies.\n\n"
        "Original source:\n"+original.decode("utf-8"))
