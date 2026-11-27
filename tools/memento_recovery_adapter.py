"""Memento-Skills v0.4.0 recovery in the original Plenum engineering executor.

Only classification and feedback; never imports upstream skill dispatch or
executes upstream recovery suggestions. No network, provider or new authority.
"""
import hashlib
import json
from vendor.memento_recovery.loop_detector import LoopDetector
from vendor.memento_recovery.error_recovery import StatefulErrorPatternDetector

class NativeRecovery:
    def __init__(self):
        self.detector = LoopDetector(max_observation_chain=5,window_size=6)
        self.actions=[]
        self.errors=[]
        self.last_effect=0
        self.last_hint=0

    def observe(self, action, result, edits, turn):
        effect = edits > self.last_effect
        self.last_effect = edits
        raw=action.get("command","")
        try:
            d=json.loads(raw)
            op=d.get("op") if isinstance(d,dict) else None
        except (ValueError,TypeError,RecursionError):
            op=None
        op=op if op in ("view","replace","submit") else "invalid"
        self.detector.record(op,"effect" if effect else "observation",turn,
                             created_artifacts=int(effect))
        if effect:
            self.actions.clear()
            self.errors.clear()
        fingerprint=hashlib.sha256(str(raw).encode("utf-8","replace")).hexdigest()
        self.actions.append({"tool":op,"arguments":{"sha256":fingerprint}})
        self.actions=self.actions[-5:]
        if result.get("returncode") != 0:
            out=str(result.get("output",""))[:6000]
            self.errors.append({"error":out,"tool":op,"turn":turn})
            self.errors=self.errors[-5:]
        loop=self.detector.detect()
        errors=StatefulErrorPatternDetector.analyze(self.errors,self.actions)
        # Deliberately translate only known diagnostic categories. Upstream
        # hints suggesting arbitrary tools, installs or permission changes
        # never enter the model context.
        categories=[]
        if loop and not effect:
            categories.append(loop["type"])
        categories.extend(x["pattern"] for x in errors)
        if not categories or turn-self.last_hint<2 or (op=="submit" and result.get("returncode")==0):
            return result, []
        self.last_hint=turn
        hint=("Recovery: change approach. Inspect only the relevant source fragment if necessary; "
              "make a different exact replacement, then use the automatic regression feedback. "
              "Do not repeat a failed action or modify tests.")
        return {**result,"output":str(result.get("output",""))+"\n"+hint}, sorted(set(categories))
