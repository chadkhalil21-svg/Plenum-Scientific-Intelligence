"""Check exact upstream metadata exclusion and no application-data exclusion."""
import sqlite3,tempfile
from pathlib import Path
from contextlib import closing
from replica import logical
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/"fixture.sqlite"
    with closing(sqlite3.connect(p)) as c:
        c.execute("create table workflow (id integer primary key, receipt text)")
        c.execute("insert into workflow values (1,'acknowledged')");c.commit()
        before=logical(p)
        c.execute("CREATE TABLE IF NOT EXISTS _litestream_seq (id INTEGER PRIMARY KEY, seq INTEGER);")
        c.execute("CREATE TABLE IF NOT EXISTS _litestream_lock (id INTEGER);")
        c.execute("insert into _litestream_seq values (1,1)");c.commit()
        assert logical(p)==before
        c.execute("update workflow set receipt='changed'");c.commit()
        assert logical(p)!=before
        c.execute("create table _litestream_unexpected (id integer)");c.commit()
        try:logical(p)
        except ValueError:pass
        else:raise AssertionError("Unreviewed metadata excluded")
print("PASS: exact Litestream bookkeeping schema only; changed application row detected; unknown metadata rejected")
