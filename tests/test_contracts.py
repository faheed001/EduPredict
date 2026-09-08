import json, pathlib, sqlite3, ast

ROOT=pathlib.Path(__file__).resolve().parents[1]
def test_python_syntax():
    for p in [ROOT/"app.py", ROOT/"model/train_model.py", ROOT/"data/generate_dataset.py"]: ast.parse(p.read_text(encoding="utf-8"))
def test_metrics_contract():
    m=json.loads((ROOT/"model/metrics.json").read_text(encoding="utf-8"))
    assert 0 < m["classification"]["roc_auc"] <= 1
    assert 0 < m["classification"]["operating_threshold"] < 1
    assert 2 <= m["clustering"]["clusters"] <= 6
    assert m["validation_size"] > 0 and m["test_size"] > 0
def test_schema_contract():
    tree=ast.parse((ROOT/"app.py").read_text(encoding="utf-8")); script=None
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr=="executescript" and n.args and isinstance(n.args[0], ast.Constant): script=n.args[0].value; break
    assert script
    c=sqlite3.connect(":memory:"); c.executescript(script)
    names={r[0] for r in c.execute("select name from sqlite_master where type='table'")}
    assert {"users","students","performance_records","predictions","interventions","audit_log","system_meta"} <= names
