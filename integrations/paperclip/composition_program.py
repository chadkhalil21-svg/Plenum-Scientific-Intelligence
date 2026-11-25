"""Bounded exact expression interpreter. No eval, imports from inputs, or network."""
import ast
import json
import sys
from fractions import Fraction

def calculate(expressions, values, outputs):
    env={k:Fraction(v) for k,v in values.items()}
    result={}
    for name in outputs:
        source=expressions[name]
        if type(source) is not str or not 1<=len(source)<=160:
            raise ValueError("Expression length")
        tree=ast.parse(source,mode="eval")
        if sum(1 for _ in ast.walk(tree))>65:
            raise ValueError("Expression complexity")
        used=set()
        def walk(node):
            if isinstance(node,ast.Name) and node.id in env:
                used.add(node.id)
                value=env[node.id]
            elif isinstance(node,ast.Constant) and type(node.value) is int and abs(node.value)<=1000000:
                value=Fraction(node.value)
            elif isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub):
                value=-walk(node.operand)
            elif isinstance(node,ast.BinOp):
                a,b=walk(node.left),walk(node.right)
                if isinstance(node.op,ast.Add):value=a+b
                elif isinstance(node.op,ast.Sub):value=a-b
                elif isinstance(node.op,ast.Mult):value=a*b
                elif isinstance(node.op,ast.Div):value=a/b
                elif isinstance(node.op,ast.FloorDiv):value=Fraction(a//b)
                else:raise ValueError("Operator outside authorized grammar")
            else:raise ValueError("Expression outside authorized grammar")
            if max(abs(value.numerator),value.denominator)>10**18:raise ValueError("Quantity bound")
            return value
        value=walk(tree.body)
        if not used:raise ValueError("Output must reference scoped input or prior result")
        env[name]=value
        result[name]={"numerator":value.numerator,"denominator":value.denominator}
    return result

def analyze(data):
    return {"results":calculate(data["expressions"],data["values"],data["outputs"]),
            "holdout":calculate(data["expressions"],data["holdout"],data["outputs"])}

if __name__=="__main__":
    if sys.argv[1:]!=["collections"]:raise ValueError("Only reviewed interpreter")
    print(json.dumps(analyze(json.load(sys.stdin)),sort_keys=True))
