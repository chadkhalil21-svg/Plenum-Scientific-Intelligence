"""Load the verified prior native mission receipts into a disposable PG fixture.
No actual Paperclip PostgreSQL database or private data is exported.
"""
import json,sys
from pathlib import Path
from receipts import read_accepted,encoded,digest
def main():
    action,archive=sys.argv[1:]
    rows=read_accepted(Path(archive))
    values=[(k,r["company"],r["mission"],r["qualification_sha256"],r["scope_sha256"],5,11) for k,r in sorted(rows.items())]
    if action=="sql":
        print("CREATE TABLE acceptance(case_name text PRIMARY KEY, company uuid NOT NULL, mission uuid NOT NULL, qualification_sha256 text NOT NULL, scope_sha256 text NOT NULL, divisions integer CHECK(divisions=5), products integer CHECK(products=11));")
        for v in values:
            # All strings have already passed canonical strict allowlists.
            print("INSERT INTO acceptance VALUES ("+",".join("'"+x+"'" if isinstance(x,str) else str(x) for x in v)+");")
    elif action=="expected":
        for v in values:print("|".join(map(str,v)))
    else:raise ValueError("Unknown action")
if __name__=="__main__":main()
