"""Reviewed bounded objective computation. No network, user code or arbitrary paths."""
import json,re,sys
from fractions import Fraction
from collections import Counter

TOOLS=("sqlite","collections","stream")
OPS=("mean","median","range","word_counts","shared_terms","term_frequency","population_variance","least_squares_slope","max_step_change")

def tokens(text):
    return re.findall(r"[a-z0-9]+",text.lower())

def counts_stream(items):
    out={}
    for item in items:out[item]=out.get(item,0)+1
    return out

def analyze(data,tool):
    if tool not in TOOLS:raise ValueError("Unsupported reviewed tool")
    docs=[tokens(x) for x in data.get("documents",[])]
    samples=data.get("samples",[])
    ops=data["operations"]
    if tool=="sqlite":
        import sqlite3
        db=sqlite3.connect(":memory:")
        try:
            db.execute("CREATE TABLE tokens (document INTEGER, token TEXT)")
            db.executemany("INSERT INTO tokens VALUES (?,?)",[(i,t) for i,items in enumerate(docs) for t in items])
            db.execute("CREATE TABLE samples (value INTEGER)")
            db.executemany("INSERT INTO samples VALUES (?)",[(v,) for v in samples])
            freq=[dict(db.execute("SELECT token,count(*) FROM tokens WHERE document=? GROUP BY token",(i,))) for i in range(len(docs))]
            ordered=[x[0] for x in db.execute("SELECT value FROM samples ORDER BY value")]
            total=db.execute("SELECT sum(value) FROM samples").fetchone()[0]
        finally:db.close()
    elif tool=="collections":
        freq=[dict(Counter(x)) for x in docs]
        ordered=sorted(samples);total=sum(samples)
    else:
        freq=[counts_stream(x) for x in docs]
        ordered=[];total=0
        for value in samples:
            i=0
            while i<len(ordered) and ordered[i]<=value:i+=1
            ordered.insert(i,value);total+=value
    out={}
    for op in ops:
        n=len(ordered)
        if op=="word_counts":out[op]=[sum(x.values()) for x in freq]
        elif op=="shared_terms":out[op]=sorted(set(freq[0]).intersection(*[set(x) for x in freq[1:]]))
        elif op=="term_frequency":out[op]=[dict(sorted(x.items())) for x in freq]
        else:
            if op=="mean":value=Fraction(total,n)
            elif op=="median":value=Fraction(ordered[(n-1)//2]+ordered[n//2],2)
            elif op=="range":value=Fraction(ordered[-1]-ordered[0])
            elif op=="population_variance":value=Fraction(n*sum(x*x for x in ordered)-total*total,n*n)
            elif op=="least_squares_slope":
                sx=n*(n-1)//2; sxx=n*(n-1)*(2*n-1)//6
                value=Fraction(n*sum(i*y for i,y in enumerate(samples))-sx*total,n*sxx-sx*sx)
            elif op=="max_step_change":value=Fraction(max(abs(y-x) for x,y in zip(samples,samples[1:])))
            else:raise ValueError("Unknown acceptance operation")
            out[op]={"numerator":value.numerator,"denominator":value.denominator}
    return {"results":out}
if __name__=="__main__":print(json.dumps(analyze(json.load(sys.stdin),sys.argv[1]),sort_keys=True))
