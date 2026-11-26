"""Generic dimensional constraints, not domain-specific equations or hidden answers."""
import ast
import re
from collections import Counter
NAME=re.compile(r"[a-z][a-z0-9_]{0,23}")

def validate(c):
    dimensions=c["dimensions"];integers=c["integer_outputs"];names=set(c["values"])|set(c["outputs"])
    if not isinstance(dimensions,dict) or set(dimensions)!=names or not isinstance(integers,list) or any(not isinstance(k,str) or k not in c["outputs"] for k in integers) or len(set(integers))!=len(integers):
        raise ValueError("Exact declared dimension schema")
    axes=set()
    for d in dimensions.values():
        if not isinstance(d,dict) or len(d)>8 or any(not isinstance(k,str) or not NAME.fullmatch(k) or type(v) is not int or not -4<=v<=4 or v==0 for k,v in d.items()):
            raise ValueError("Invalid dimension vector")
        axes.update(d)
    if len(axes)>8:raise ValueError("Dimension axis bound")

def combine(a,b,sign):
    out=dict(a)
    for k,v in b.items():out[k]=out.get(k,0)+sign*v
    return {k:v for k,v in out.items() if v}

def candidate_expressions(c):
    """Enumerate grammar-derived two-operand choices without reading input values."""
    validate(c);d=c["dimensions"];available=sorted(c["values"]);out={}
    for target in c["outputs"]:
        candidates=set()
        for left in available:
            for right in available:
                a,b=d[left],d[right];wanted=d[target]
                if a==b==wanted:
                    if left<=right:candidates.add(left+"+"+right)
                    candidates.add(left+"-"+right)
                if combine(a,b,1)==wanted and left<=right:candidates.add(left+"*"+right)
                if combine(a,b,-1)==wanted:
                    candidates.add(left+"/"+right)
                    if target in c["integer_outputs"]:
                        candidates.add("ceil("+left+"/"+right+")")
                        candidates.add("floor("+left+"/"+right+")")
        if not candidates or len(candidates)>96:raise ValueError("No bounded dimensioned two-operand plan")
        out[target]=sorted(candidates);available.append(target)
    return out

def verify_expressions(c,expressions):
    """Independent symbolic dimensional walk, no enumeration or hidden answer use."""
    validate(c)
    if not isinstance(expressions,dict) or set(expressions)!=set(c["outputs"]):raise ValueError("Output contract")
    d=c["dimensions"];env={k:d[k] for k in c["values"]}
    for target in c["outputs"]:
        expr=expressions[target]
        if not isinstance(expr,str) or not 1<=len(expr)<=160:raise ValueError("Expression alphabet")
        tree=ast.parse(expr,mode="eval")
        if sum(1 for _ in ast.walk(tree))>65:raise ValueError("Expression node limit")
        def walk(node):
            if isinstance(node,ast.Name) and node.id in env:return env[node.id]
            if isinstance(node,ast.Constant) and type(node.value) is int and abs(node.value)<=1000000:return {}
            if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub):return walk(node.operand)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ("ceil","floor") and len(node.args)==1 and not node.keywords:
                if target not in c["integer_outputs"]:raise ValueError("Rounding continuous output forbidden")
                return walk(node.args[0])
            if isinstance(node,ast.BinOp):
                a,b=walk(node.left),walk(node.right)
                if isinstance(node.op,(ast.Add,ast.Sub)):
                    if a!=b:raise ValueError("Dimension mismatch")
                    return a
                if isinstance(node.op,ast.Mult):sign=1
                elif isinstance(node.op,ast.Div):sign=-1
                elif isinstance(node.op,ast.FloorDiv):
                    if target not in c["integer_outputs"]:raise ValueError("Rounding continuous output forbidden")
                    sign=-1
                else:raise ValueError("Forbidden dimension operator")
                keys=set(a)|set(b)
                result={k:a.get(k,0)+sign*b.get(k,0) for k in keys}
                return {k:v for k,v in result.items() if v}
            raise ValueError("Forbidden dimension expression")
        if walk(tree.body)!=d[target]:raise ValueError("Dimension mismatch")
        env[target]=d[target]
