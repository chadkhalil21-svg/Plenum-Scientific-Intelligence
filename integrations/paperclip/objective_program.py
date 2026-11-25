"""Reviewed bounded objective computation. No network, user code or arbitrary paths."""
import json,re,sys
from fractions import Fraction
from collections import Counter

TOOLS=("sqlite","collections","stream")
OPS=("mean","median","range","word_counts","shared_terms","term_frequency","population_variance","least_squares_slope","max_step_change")


# Terminal operations are selected by the local model. Reviewed dependencies
# are expanded into a closed DAG. No user code, shell or network.
PIPELINES={
    "experiment":{"control_mean":(),"treatment_mean":(),"absolute_reduction":("control_mean","treatment_mean"),
                  "relative_reduction":("absolute_reduction","control_mean")},
    "design":{"total_load":(),"reserve_capacity":("total_load",),
              "reserve_fraction":("reserve_capacity",),"utilization_fraction":("total_load",)},
    "business":{"unit_contribution":(),"total_contribution":("unit_contribution",),
                "break_even_units":("unit_contribution",),"operating_profit":("total_contribution",)}
}
PIPELINE_OPS=tuple(op for graph in PIPELINES.values() for op in graph)

def pipeline_order(domain,operations):
    graph=PIPELINES[domain]
    if not isinstance(operations,list) or not operations or any(type(op) is not str or op not in graph for op in operations) or len(set(operations))!=len(operations):
        raise ValueError("Invalid terminal operations")
    ordered=[]
    def visit(op):
        if op in ordered:return
        for dep in graph[op]:visit(dep)
        ordered.append(op)
    for op in sorted(operations):visit(op)
    return ordered

def rational(v):
    return {"numerator":v.numerator,"denominator":v.denominator}

def aggregate(values,tool):
    if tool=="sqlite":
        import sqlite3
        with sqlite3.connect(":memory:") as db:
            db.execute("CREATE TABLE readings (value INTEGER)")
            db.executemany("INSERT INTO readings VALUES (?)",[(x,) for x in values])
            return db.execute("SELECT sum(value) FROM readings").fetchone()[0]
    if tool=="collections":return sum(k*n for k,n in Counter(values).items())
    total=0
    for v in values:total+=v
    return total

def analyze_pipeline(data,tool):
    domains=set(data)&set(PIPELINES)
    if len(domains)!=1:raise ValueError("Exactly one pipeline domain")
    domain=next(iter(domains));raw=data[domain];ops=data["operations"]
    if set(data)!={domain,"operations"}:raise ValueError("Unexpected pipeline input")
    values={};trace=[]
    for op in pipeline_order(domain,ops):
        if op=="control_mean":v=Fraction(aggregate(raw["control"],tool),len(raw["control"]))
        elif op=="treatment_mean":v=Fraction(aggregate(raw["treatment"],tool),len(raw["treatment"]))
        elif op=="absolute_reduction":v=values["control_mean"]-values["treatment_mean"]
        elif op=="relative_reduction":v=values["absolute_reduction"]/values["control_mean"]
        elif op=="total_load":v=Fraction(aggregate(raw["loads"],tool))
        elif op=="reserve_capacity":v=Fraction(raw["capacity"])-values["total_load"]
        elif op=="reserve_fraction":v=values["reserve_capacity"]/raw["capacity"]
        elif op=="utilization_fraction":v=values["total_load"]/raw["capacity"]
        elif op=="unit_contribution":v=Fraction(raw["price"]-raw["variable_cost"])
        elif op=="total_contribution":v=values["unit_contribution"]*raw["units"]
        elif op=="break_even_units":
            q=Fraction(raw["fixed_cost"])/values["unit_contribution"]
            v=Fraction(-(-q.numerator//q.denominator))
        elif op=="operating_profit":v=values["total_contribution"]-raw["fixed_cost"]
        else:raise ValueError("Unknown pipeline node")
        values[op]=v
        trace.append({"operation":op,"depends_on":list(PIPELINES[domain][op]),"value":rational(v)})
    return {"results":{op:rational(values[op]) for op in ops},"pipeline":{"domain":domain,"steps":trace}}


def tokens(text):
    return re.findall(r"[a-z0-9]+",text.lower())

def counts_stream(items):
    out={}
    for item in items:out[item]=out.get(item,0)+1
    return out

def analyze(data,tool):
    if tool not in TOOLS:raise ValueError("Unsupported reviewed tool")
    if set(data)&set(PIPELINES):return analyze_pipeline(data,tool)
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
