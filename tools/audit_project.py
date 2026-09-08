import ast, json, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in [ROOT/'app.py',ROOT/'model/train_model.py',ROOT/'data/generate_dataset.py']:
    ast.parse(p.read_text(encoding='utf-8'))
try:
    from jinja2 import Environment, FileSystemLoader
    env=Environment(loader=FileSystemLoader(str(ROOT/'templates')))
    for p in (ROOT/'templates').glob('*.html'): env.get_template(p.name)
except ImportError: pass
m=json.loads((ROOT/'model/metrics.json').read_text(encoding='utf-8'))
assert 0<m['classification']['roc_auc']<=1
assert 0<m['classification']['operating_threshold']<1
assert 2<=m['clustering']['clusters']<=6
assert m['validation_size']>0 and m['test_size']>0
# Extract schema literal and execute in an isolated SQLite database.
tree=ast.parse((ROOT/'app.py').read_text(encoding='utf-8')); script=None
for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='executescript' and n.args and isinstance(n.args[0],ast.Constant): script=n.args[0].value; break
assert script
c=sqlite3.connect(':memory:'); c.executescript(script)
required={'users','students','performance_records','predictions','interventions','audit_log','system_meta'}
actual={r[0] for r in c.execute("select name from sqlite_master where type='table'")}
assert required<=actual
assert not c.execute('PRAGMA foreign_key_check').fetchall()
print('EduPredict 3.0 audit: PASS')
print('Dataset:',m['dataset_size'],'Train/Val/Test:',m['train_size'],m['validation_size'],m['test_size'])
print('Regression MAE/R2:',m['regression']['mae'],m['regression']['r2_score'])
print('Classification AUC/F1/Recall:',m['classification']['roc_auc'],m['classification']['f1_score'],m['classification']['recall'])
print('Risk threshold:',m['classification']['operating_threshold'])
print('Selected K/silhouette:',m['clustering']['clusters'],m['clustering']['silhouette_score'])
