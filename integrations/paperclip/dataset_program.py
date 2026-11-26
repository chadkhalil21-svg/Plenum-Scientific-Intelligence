"""Reviewed generic exact integer sample analysis. No network, eval or domain fixture."""
import json
import sys
from fractions import Fraction

def analyze(data):
    values=data["values"]
    operations=data["operations"]
    if not 2<=len(values)<=65 or any(type(x) is not int or abs(x)>10**9 for x in values):raise ValueError("Invalid samples")
    if not operations or len(set(operations))!=len(operations) or set(operations)-{"mean","median","range"}:raise ValueError("Invalid operations")
    ordered=sorted(values)
    n=len(values)
    results={}
    for op in operations:
        if op=="mean":v=Fraction(sum(values),n)
        elif op=="median":v=Fraction(ordered[(n-1)//2]+ordered[n//2],2)
        else:v=Fraction(ordered[-1]-ordered[0])
        results[op]={"numerator":v.numerator,"denominator":v.denominator}
    return {"count":n,"results":results}
if __name__=="__main__":print(json.dumps(analyze(json.load(sys.stdin)),sort_keys=True))
