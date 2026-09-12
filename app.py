"""EduPredict Pro - Student Performance Management System.
A more complete demo with live SQLite data, role-based auth, AI prediction,
explainability, early-warning interventions, analytics, exports and APIs.
"""
import os, json, csv, io, sqlite3, secrets
from functools import wraps
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, Response
from werkzeug.security import generate_password_hash, check_password_hash
from assistant_engine import process_assistant_query

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_PATH = os.path.join(BASE_DIR, 'model', 'artifacts.joblib')
METRICS_PATH = os.path.join(BASE_DIR, 'model', 'metrics.json')
DATA_PATH = os.path.join(BASE_DIR, 'data', 'student_performance_dataset.csv')
DB_PATH = os.path.join(BASE_DIR, 'data', 'edupredict.db')

app = Flask(__name__)
SECRET_FILE = os.path.join(BASE_DIR, '.secret_key')


def get_secret_key():
    env_secret = os.environ.get('EDUPREDICT_SECRET')
    if env_secret:
        return env_secret
    if os.path.exists(SECRET_FILE):
        try:
            with open(SECRET_FILE, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception:
            pass
    new_key = secrets.token_hex(32)
    try:
        with open(SECRET_FILE, 'w', encoding='utf-8') as f:
            f.write(new_key)
    except Exception:
        pass
    return new_key


app.secret_key = get_secret_key()
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

artifacts = joblib.load(ARTIFACT_PATH)
rf_regressor = artifacts['rf_regressor']
gb_regressor = artifacts['gb_regressor']
classifier = artifacts['classifier']
scaler = artifacts['scaler']
cluster_scaler = artifacts['cluster_scaler']
kmeans = artifacts['kmeans']
profile_names = {int(k): v for k, v in artifacts['profile_names'].items()}
anomaly_detector = artifacts['anomaly_detector']
FEATURE_COLUMNS = list(artifacts['feature_columns'])
FEATURE_IMPORTANCE = artifacts['feature_importance']
MODEL_METRICS = json.load(open(METRICS_PATH, encoding='utf-8')) if os.path.exists(METRICS_PATH) else {}
RISK_THRESHOLD = float(artifacts.get('risk_threshold', 0.40))
RF_ENSEMBLE_WEIGHT = float(artifacts.get('ensemble_rf_weight', 0.55))
GB_ENSEMBLE_WEIGHT = float(artifacts.get('ensemble_gb_weight', 1.0 - RF_ENSEMBLE_WEIGHT))

# Inference latency optimization: single-thread decision tree traversal avoids Windows thread pool overhead.
rf_regressor.n_jobs = 1
if hasattr(classifier, 'calibrated_classifiers_'):
    for cc in classifier.calibrated_classifiers_:
        if hasattr(cc, 'estimator'):
            cc.estimator.n_jobs = 1

df = pd.read_csv(DATA_PATH)
PARENTAL_SUPPORT_LABELS = {0: 'Low', 1: 'Medium', 2: 'High'}

# Precompute cohort statistics for sub-millisecond local feature attribution.
COHORT_MEANS = {feat: float(df[feat].mean()) for feat in FEATURE_COLUMNS}
COHORT_MEANS_ARR = np.array([COHORT_MEANS[c] for c in FEATURE_COLUMNS], dtype=np.float64)
COHORT_MEDIANS = {feat: float(df[feat].median()) for feat in FEATURE_COLUMNS}
_DASHBOARD_CACHE = None


RANGES = {
    'attendance_percentage': (0, 100),
    'study_hours_per_week': (0, 80),
    'previous_exam_score': (0, 100),
    'assignment_score': (0, 100),
    'internal_assessment_score': (0, 100),
    'extracurricular_activities': (0, 1),
    'parental_support': (0, 2),
    'sleep_hours': (0, 14),
}
RECOMMENDATIONS = {
    'attendance_percentage': 'Raise attendance toward 85%+ with reminders and catch-up sessions.',
    'study_hours_per_week': 'Use a weekly timetable and increase focused study in small, consistent blocks.',
    'previous_exam_score': 'Review weak topics from the previous exam and attend remedial sessions.',
    'assignment_score': 'Use assignment feedback to correct recurring mistakes before the next submission.',
    'internal_assessment_score': 'Practice internal-assessment questions and revise high-weight topics.',
    'sleep_hours': 'Keep a consistent sleep routine and avoid sacrificing sleep for last-minute study.',
    'parental_support': 'Create a simple parent/mentor progress check-in each week.',
    'extracurricular_activities': 'Keep extracurricular activities balanced with academic study time.'
}


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def get_db():
    con = sqlite3.connect(DB_PATH, timeout=30.0)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA synchronous=NORMAL')
    con.execute('PRAGMA busy_timeout=15000')
    return con


def init_db():
    con = get_db(); cur = con.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL CHECK(role IN ('student','teacher')),
      full_name TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS students(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER UNIQUE,
      student_code TEXT UNIQUE NOT NULL,
      full_name TEXT NOT NULL,
      email TEXT,
      course TEXT,
      year TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS performance_records(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      student_id INTEGER NOT NULL,
      attendance_percentage REAL NOT NULL,
      study_hours_per_week REAL NOT NULL,
      previous_exam_score REAL NOT NULL,
      assignment_score REAL NOT NULL,
      internal_assessment_score REAL NOT NULL,
      extracurricular_activities INTEGER NOT NULL,
      parental_support INTEGER NOT NULL,
      sleep_hours REAL NOT NULL,
      recorded_at TEXT NOT NULL,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS predictions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      student_id INTEGER NOT NULL,
      record_id INTEGER,
      predicted_score REAL,
      risk_probability REAL,
      at_risk INTEGER,
      performance_category TEXT,
      learning_profile TEXT,
      unusual_pattern INTEGER DEFAULT 0,
      details_json TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS interventions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      student_id INTEGER NOT NULL,
      teacher_id INTEGER NOT NULL,
      note TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open','In Progress','Resolved')),
      created_at TEXT NOT NULL,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
      FOREIGN KEY(teacher_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS system_meta(
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS audit_log(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      action TEXT NOT NULL,
      details TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    CREATE INDEX IF NOT EXISTS idx_records_student ON performance_records(student_id, id DESC);
    CREATE INDEX IF NOT EXISTS idx_predictions_student ON predictions(student_id, id DESC);
    CREATE INDEX IF NOT EXISTS idx_interventions_student ON interventions(student_id, id DESC);
    ''')
    # Lightweight migration for databases created by the earlier project.
    cols = {r['name'] for r in cur.execute('PRAGMA table_info(predictions)').fetchall()}
    if 'unusual_pattern' not in cols: cur.execute('ALTER TABLE predictions ADD COLUMN unusual_pattern INTEGER DEFAULT 0')
    if 'details_json' not in cols: cur.execute('ALTER TABLE predictions ADD COLUMN details_json TEXT')
    cur.execute("INSERT INTO system_meta(key,value,updated_at) VALUES('schema_version','3.0',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at", (now_iso(),))
    if cur.execute("SELECT COUNT(*) FROM users WHERE role='teacher'").fetchone()[0] == 0:
        cur.execute('INSERT INTO users(username,password_hash,role,full_name,created_at) VALUES(?,?,?,?,?)',
                    ('teacher', generate_password_hash('teacher123'), 'teacher', 'Demo Teacher', now_iso()))
    if cur.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0] == 0:
        cur.execute('INSERT INTO users(username,password_hash,role,full_name,created_at) VALUES(?,?,?,?,?)',
                    ('student', generate_password_hash('student123'), 'student', 'Demo Student', now_iso()))
        uid = cur.lastrowid
        cur.execute('INSERT INTO students(user_id,student_code,full_name,email,course,year,created_at) VALUES(?,?,?,?,?,?,?)',
                    (uid, 'STU001', 'Demo Student', 'student@example.com', 'Computer Science', '3', now_iso()))
    con.commit(); con.close()

init_db()


def audit(action, details=''):
    con = get_db()
    con.execute('INSERT INTO audit_log(user_id,action,details,created_at) VALUES(?,?,?,?)',
                (session.get('user_id'), action, details[:500], now_iso()))
    con.commit(); con.close()


def login_required(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get('user_id'):
                return redirect(url_for('login', next=request.path))
            if role and session.get('role') != role:
                flash('You do not have permission to access that page.', 'error')
                return redirect(url_for('home'))
            return fn(*args, **kwargs)
        return wrapper
    return deco


def csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(24)
    return session['csrf_token']


@app.context_processor
def inject_globals():
    return {'csrf_token': csrf_token()}


@app.before_request
def protect_posts():
    if request.method == 'POST':
        token = request.form.get('_csrf') or request.headers.get('X-CSRF-Token')
        if not token or token != session.get('csrf_token'):
            # JSON prediction is intentionally protected only when logged-in session exists.
            if request.path == '/api/predict' and not session.get('user_id'):
                return jsonify({'error': 'Authentication required for this API.'}), 401
            return 'CSRF validation failed. Refresh the page and try again.', 400


@app.after_request
def add_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; img-src 'self' data:; connect-src 'self'; font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; frame-ancestors 'self'")
    if request.is_secure:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response


def build_feature_vector(payload):
    return pd.DataFrame([[float(payload[c]) for c in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)


def validate_payload(payload):
    clean = {}
    for c in FEATURE_COLUMNS:
        raw = payload.get(c, 0 if c == 'extracurricular_activities' else None)
        if raw is None or raw == '':
            raise ValueError(f'Missing value: {c}')
        try: value = float(raw)
        except (TypeError, ValueError): raise ValueError(f'Invalid value: {c}')
        lo, hi = RANGES[c]
        if not lo <= value <= hi: raise ValueError(f'{c} must be between {lo} and {hi}.')
        if c in ('extracurricular_activities', 'parental_support'): value = int(round(value))
        clean[c] = value
    return clean


def predict_score(X_scaled):
    return float(RF_ENSEMBLE_WEIGHT * rf_regressor.predict(X_scaled)[0] + GB_ENSEMBLE_WEIGHT * gb_regressor.predict(X_scaled)[0])


def explain_prediction(payload, base_score):
    r"""
    Local Additive Feature Attribution (Marginal Contribution Decomposition).
    Vectorized batch calculation for sub-millisecond execution:
    phi_i = f(x) - f(x \ {i} U {E[X_i]}).
    """
    vec_base = np.array([float(payload[c]) for c in FEATURE_COLUMNS], dtype=np.float64)
    batch = np.tile(vec_base, (len(FEATURE_COLUMNS), 1))
    for i in range(len(FEATURE_COLUMNS)):
        batch[i, i] = COHORT_MEANS_ARR[i]

    df_batch = pd.DataFrame(batch, columns=FEATURE_COLUMNS)
    Xs = scaler.transform(df_batch)
    alt_scores = np.clip(
        RF_ENSEMBLE_WEIGHT * rf_regressor.predict(Xs) + GB_ENSEMBLE_WEIGHT * gb_regressor.predict(Xs),
        0, 100
    )
    impacts = [
        {'feature': feat, 'impact': round(base_score - float(alt_scores[i]), 2)}
        for i, feat in enumerate(FEATURE_COLUMNS)
    ]
    return sorted(impacts, key=lambda x: abs(x['impact']), reverse=True)


def run_prediction(payload):
    payload = validate_payload(payload)
    X = build_feature_vector(payload); Xs = scaler.transform(X)
    score = round(max(0.0, min(100.0, predict_score(Xs))), 1)
    risk = float(classifier.predict_proba(Xs)[0][1])
    at_risk = bool(risk >= RISK_THRESHOLD)
    category = 'High' if score >= 75 else ('Medium' if score >= 50 else 'Low')
    X_clust = cluster_scaler.transform(X)
    profile_id = int(kmeans.predict(X_clust)[0])
    profile = profile_names.get(profile_id, 'General Learner')
    anomaly = int(anomaly_detector.predict(X_clust)[0]) == -1

    weak = []
    for item in FEATURE_IMPORTANCE:
        feat = item[0]
        if feat != 'extracurricular_activities' and float(payload[feat]) < COHORT_MEDIANS[feat]:
            weak.append(feat)
        if len(weak) >= 3: break
    rec = [RECOMMENDATIONS[f] for f in weak]
    if at_risk:
        rec.insert(0, 'Schedule a teacher/mentor review this week because the model flags elevated academic risk.')
    if not rec: rec = ['Maintain current habits and set a measurable target for the next assessment.']
    plan = [
        'Daily: 45–60 minutes of distraction-free revision.',
        'Weekly: complete one timed practice test and review every error.',
        'Before exams: focus first on the two weakest areas identified by the teacher.'
    ]
    if payload['attendance_percentage'] < 75: plan[0] = 'Daily: attend scheduled classes and complete a 30-minute catch-up block.'
    if payload['study_hours_per_week'] < 10: plan[1] = 'Weekly: build study time gradually toward 10–15 focused hours.'
    return {
        'predicted_score': score, 'performance_category': category, 'at_risk': at_risk,
        'risk_probability': round(risk * 100, 1), 'recommendations': rec,
        'learning_profile': profile, 'profile_id': profile_id, 'unusual_pattern': anomaly,
        'feature_impacts': explain_prediction(payload, score)[:5], 'study_plan': plan,
        'model_note': f'Ensemble: Random Forest ({RF_ENSEMBLE_WEIGHT:.2f}) + Gradient Boosting ({GB_ENSEMBLE_WEIGHT:.2f}); calibrated risk classifier with validation-selected threshold {RISK_THRESHOLD:.3f}; learner profiling and anomaly detection are additional signals.'
    }


def record_from_form(form):
    return validate_payload({c: form.get(c, 0 if c == 'extracurricular_activities' else None) for c in FEATURE_COLUMNS})


def save_record(student_id, payload):
    payload = validate_payload(payload)
    con = get_db(); cur = con.cursor(); stamp = now_iso()
    vals = [student_id] + [payload[c] for c in FEATURE_COLUMNS] + [stamp]
    cur.execute('''INSERT INTO performance_records(
      student_id,attendance_percentage,study_hours_per_week,previous_exam_score,
      assignment_score,internal_assessment_score,extracurricular_activities,
      parental_support,sleep_hours,recorded_at) VALUES(?,?,?,?,?,?,?,?,?,?)''', vals)
    rid = cur.lastrowid
    result = run_prediction(payload)
    cur.execute('''INSERT INTO predictions(
      student_id,record_id,predicted_score,risk_probability,at_risk,
      performance_category,learning_profile,unusual_pattern,details_json,created_at)
      VALUES(?,?,?,?,?,?,?,?,?,?)''',
      (student_id, rid, result['predicted_score'], result['risk_probability'], int(result['at_risk']),
       result['performance_category'], result['learning_profile'], int(result['unusual_pattern']), json.dumps(result), stamp))
    con.commit(); con.close()
    return rid, result


def import_dataset_students():
    """Import the bundled 1,500-row CSV into the live SQLite tables once."""
    if not os.path.exists(DATA_PATH):
        return 0

    con = get_db()
    count = con.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    if count >= 1500:
        con.close()
        return 0

    source = pd.read_csv(DATA_PATH)
    if source.empty:
        con.close()
        return 0

    cur = con.cursor()

    # Reuse the built-in demo student for the first dataset row so the
    # dashboard contains exactly the 1,500 CSV students, not 1,501 rows.
    demo = cur.execute(
        "SELECT id FROM students WHERE student_code='STU001' AND full_name='Demo Student' LIMIT 1"
    ).fetchone()

    feature_matrix = source[FEATURE_COLUMNS].astype(float).to_numpy()
    scaled = scaler.transform(feature_matrix)
    predicted = np.clip(
        RF_ENSEMBLE_WEIGHT * rf_regressor.predict(scaled) + GB_ENSEMBLE_WEIGHT * gb_regressor.predict(scaled), 0, 100
    )
    predicted = np.round(predicted, 1)
    risk_prob = classifier.predict_proba(scaled)[:, 1] * 100
    at_risk = (risk_prob >= RISK_THRESHOLD * 100).astype(int)
    categories = np.where(predicted >= 75, 'High',
                          np.where(predicted >= 50, 'Medium', 'Low'))
    profiles = kmeans.predict(cluster_scaler.transform(feature_matrix))
    profile_labels = [profile_names.get(int(p), 'General Learner') for p in profiles]
    unusual = (anomaly_detector.predict(cluster_scaler.transform(feature_matrix)) == -1).astype(int)

    inserted = 0
    stamp = now_iso()

    for i, row in source.iterrows():
        sid_num = int(row['student_id'])
        code = f"STU{sid_num:04d}"
        name = str(row['student_name']).strip() if 'student_name' in row and pd.notna(row['student_name']) else f"Dataset Student {sid_num:04d}"
        clean_email_name = name.lower().replace("'", "").replace(" ", ".")
        email = f"{clean_email_name}@campus.edu"

        existing = cur.execute(
            "SELECT id FROM students WHERE student_code=?", (code,)
        ).fetchone()

        if existing:
            student_db_id = existing['id']
        elif sid_num == 1 and demo:
            # Preserve the demo login while turning its student record into row 1.
            student_db_id = demo['id']
            cur.execute(
                """UPDATE students
                   SET student_code=?, full_name=?, email=?, course=?, year=?, created_at=?
                   WHERE id=?""",
                (code, name, email, 'Information Technology', '3', stamp, student_db_id)
            )
        else:
            cur.execute(
                """INSERT INTO students(user_id,student_code,full_name,email,course,year,created_at)
                   VALUES(NULL,?,?,?,?,?,?)""",
                (code, name, email, 'Information Technology', '3', stamp)
            )
            student_db_id = cur.lastrowid

        # Avoid duplicate records if the app is restarted.
        has_record = cur.execute(
            "SELECT id FROM performance_records WHERE student_id=? LIMIT 1",
            (student_db_id,)
        ).fetchone()
        if has_record:
            continue

        vals = [student_db_id] + [float(row[c]) for c in FEATURE_COLUMNS] + [stamp]
        cur.execute(
            """INSERT INTO performance_records(
               student_id,attendance_percentage,study_hours_per_week,previous_exam_score,
               assignment_score,internal_assessment_score,extracurricular_activities,
               parental_support,sleep_hours,recorded_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            vals
        )
        record_id = cur.lastrowid

        details = {
            'source': 'student_performance_dataset.csv',
            'student_id': sid_num,
            'final_exam_score': float(row['final_exam_score']),
            'dataset_performance_category': str(row['performance_category']),
            'dataset_at_risk': int(row['at_risk']),
            'predicted_score': float(predicted[i]),
            'risk_probability': round(float(risk_prob[i]), 1),
            'performance_category': str(categories[i]),
            'learning_profile': profile_labels[i],
            'unusual_pattern': bool(unusual[i])
        }
        cur.execute(
            """INSERT INTO predictions(
               student_id,record_id,predicted_score,risk_probability,at_risk,
               performance_category,learning_profile,unusual_pattern,details_json,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (student_db_id, record_id, float(predicted[i]), round(float(risk_prob[i]), 1),
             int(at_risk[i]), str(categories[i]), profile_labels[i], int(unusual[i]),
             json.dumps(details), stamp)
        )
        inserted += 1

    con.commit()
    con.close()
    return inserted


# Automatically load the bundled 1,500-student dataset into SQLite.
import_dataset_students()

def latest_student_rows(con):
    return con.execute('''SELECT s.*, p.predicted_score,p.risk_probability,p.at_risk,p.performance_category,
      p.learning_profile,p.unusual_pattern,p.created_at AS prediction_time
      FROM students s LEFT JOIN predictions p ON p.id=(SELECT MAX(id) FROM predictions WHERE student_id=s.id)
      ORDER BY s.full_name''').fetchall()


@app.route('/')
def home():
    if session.get('user_id'):
        return redirect(url_for('student_dashboard' if session.get('role') == 'student' else 'teacher_dashboard'))
    return render_template('index.html', stats={
        'total_students': len(df), 'avg_score': round(df.final_exam_score.mean(), 1),
        'at_risk_count': int(df.at_risk.sum()), 'at_risk_pct': round(df.at_risk.mean() * 100, 1)
    })


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        con = get_db(); user = con.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone(); con.close()
        if user and check_password_hash(user['password_hash'], request.form.get('password', '')):
            session.clear(); session.update(user_id=user['id'], role=user['role'], full_name=user['full_name'])
            csrf_token(); audit('login', f'role={user["role"]}')
            return redirect(request.args.get('next') or url_for('home'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower(); password = request.form.get('password', '')
        name = request.form.get('full_name', '').strip(); code = request.form.get('student_code', '').strip().upper()
        if len(password) < 6: flash('Password must be at least 6 characters.', 'error'); return render_template('register.html')
        if not username or not name or not code: flash('Please fill all required fields.', 'error'); return render_template('register.html')
        con = get_db()
        try:
            cur = con.cursor()
            cur.execute('INSERT INTO users(username,password_hash,role,full_name,created_at) VALUES(?,?,?,?,?)',
                        (username, generate_password_hash(password), 'student', name, now_iso()))
            uid = cur.lastrowid
            cur.execute('INSERT INTO students(user_id,student_code,full_name,email,course,year,created_at) VALUES(?,?,?,?,?,?,?)',
                        (uid, code, name, request.form.get('email','').strip(), request.form.get('course','').strip(), request.form.get('year','').strip(), now_iso()))
            con.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            con.rollback(); flash('Username or student code already exists.', 'error')
        finally: con.close()
    return render_template('register.html')


@app.route('/assistant')
@login_required()
def assistant():
    return render_template('assistant.html')


@app.route('/api/assistant', methods=['POST'])
@login_required()
def api_assistant():
    data = request.get_json(silent=True) or {}
    message = str(data.get('message', '')).strip()[:500]
    if not message:
        return jsonify({'error': 'Please enter a question.'}), 400

    con = get_db()
    try:
        res = process_assistant_query(
            message=message,
            user_id=session.get('user_id'),
            role=session.get('role'),
            username=session.get('username'),
            con=con
        )
    finally:
        con.close()

    audit('assistant_query', message)
    return jsonify(res)


@app.route('/logout')
def logout():
    if session.get('user_id'): audit('logout')
    session.clear(); return redirect(url_for('login'))


@app.route('/student/dashboard')
@login_required('student')
def student_dashboard():
    con = get_db(); s = con.execute('SELECT * FROM students WHERE user_id=?', (session['user_id'],)).fetchone()
    records = con.execute('SELECT * FROM performance_records WHERE student_id=? ORDER BY id DESC LIMIT 20', (s['id'],)).fetchall() if s else []
    preds = con.execute('SELECT * FROM predictions WHERE student_id=? ORDER BY id DESC LIMIT 20', (s['id'],)).fetchall() if s else []
    interventions = con.execute('''SELECT i.*,u.full_name AS teacher_name FROM interventions i JOIN users u ON u.id=i.teacher_id WHERE i.student_id=? ORDER BY i.id DESC LIMIT 10''', (s['id'],)).fetchall() if s else []
    con.close()
    return render_template('student_dashboard.html', student=s, records=records, predictions=preds, interventions=interventions)


@app.route('/student/profile', methods=['GET', 'POST'])
@login_required('student')
def student_profile():
    con = get_db(); s = con.execute('SELECT * FROM students WHERE user_id=?', (session['user_id'],)).fetchone()
    if request.method == 'POST':
        name = request.form.get('full_name','').strip(); email=request.form.get('email','').strip(); course=request.form.get('course','').strip(); year=request.form.get('year','').strip()
        if not name: flash('Name is required.', 'error')
        else:
            con.execute('UPDATE students SET full_name=?,email=?,course=?,year=? WHERE id=?', (name,email,course,year,s['id']))
            con.execute('UPDATE users SET full_name=? WHERE id=?', (name,session['user_id'])); con.commit(); session['full_name']=name; audit('profile_update', f'student_id={s["id"]}'); flash('Profile updated.', 'success'); return redirect(url_for('student_profile'))
    s = con.execute('SELECT * FROM students WHERE id=?', (s['id'],)).fetchone(); con.close()
    return render_template('student_profile.html', student=s)


@app.route('/student/update', methods=['GET', 'POST'])
@login_required('student')
def student_update():
    con=get_db(); s=con.execute('SELECT * FROM students WHERE user_id=?',(session['user_id'],)).fetchone(); con.close()
    if request.method=='POST':
        try:
            payload=record_from_form(request.form); rid,result=save_record(s['id'],payload); audit('performance_update', f'student_id={s["id"]},record_id={rid}')
            flash(f'Performance updated. New AI prediction: {result["predicted_score"]}/100.', 'success'); return redirect(url_for('student_dashboard'))
        except Exception as e: flash(str(e), 'error')
    return render_template('student_update.html', student=s, form_data=None, parental_labels=PARENTAL_SUPPORT_LABELS)


@app.route('/teacher/dashboard')
@login_required('teacher')
def teacher_dashboard():
    con=get_db(); students=latest_student_rows(con)
    stats=con.execute('''SELECT COUNT(*) total, COALESCE(AVG(predicted_score),0) avg, COALESCE(SUM(at_risk),0) risk,
      COALESCE(SUM(unusual_pattern),0) unusual FROM predictions WHERE id IN (SELECT MAX(id) FROM predictions GROUP BY student_id)''').fetchone()
    trend=con.execute('''SELECT substr(created_at,1,10) day, ROUND(AVG(predicted_score),1) avg_score, COUNT(*) count
      FROM predictions GROUP BY substr(created_at,1,10) ORDER BY day DESC LIMIT 14''').fetchall()
    con.close()
    return render_template('teacher_dashboard.html', students=students, stats=stats, trend=list(reversed(trend)))


@app.route('/teacher/student/<int:student_id>')
@login_required('teacher')
def teacher_student(student_id):
    con=get_db(); s=con.execute('SELECT * FROM students WHERE id=?',(student_id,)).fetchone()
    records=con.execute('SELECT * FROM performance_records WHERE student_id=? ORDER BY id DESC LIMIT 30',(student_id,)).fetchall()
    preds=con.execute('SELECT * FROM predictions WHERE student_id=? ORDER BY id DESC LIMIT 30',(student_id,)).fetchall()
    notes=con.execute('''SELECT i.*,u.full_name AS teacher_name FROM interventions i JOIN users u ON u.id=i.teacher_id WHERE i.student_id=? ORDER BY i.id DESC LIMIT 20''',(student_id,)).fetchall()
    con.close()
    if not s: return 'Student not found',404
    return render_template('teacher_student.html', student=s, records=records, predictions=preds, notes=notes)


@app.route('/teacher/student/<int:student_id>/intervention', methods=['POST'])
@login_required('teacher')
def add_intervention(student_id):
    note=request.form.get('note','').strip(); status=request.form.get('status','Open')
    if not note: flash('Intervention note cannot be empty.', 'error')
    elif status not in ('Open','In Progress','Resolved'): flash('Invalid status.', 'error')
    else:
        con=get_db(); exists=con.execute('SELECT id FROM students WHERE id=?',(student_id,)).fetchone()
        if exists:
            con.execute('INSERT INTO interventions(student_id,teacher_id,note,status,created_at) VALUES(?,?,?,?,?)',(student_id,session['user_id'],note,status,now_iso())); con.commit(); audit('intervention_added',f'student_id={student_id}'); flash('Intervention saved.', 'success')
        con.close()
    return redirect(url_for('teacher_student', student_id=student_id))


@app.route('/teacher/add-student', methods=['GET','POST'])
@login_required('teacher')
def add_student():
    if request.method=='POST':
        username=request.form.get('username','').strip().lower(); password=request.form.get('password',''); name=request.form.get('full_name','').strip(); code=request.form.get('student_code','').strip().upper()
        if len(password)<6 or not username or not name or not code: flash('Username, name, code and a 6+ character password are required.','error'); return render_template('add_student.html')
        con=get_db()
        try:
            cur=con.cursor(); cur.execute('INSERT INTO users(username,password_hash,role,full_name,created_at) VALUES(?,?,?,?,?)',(username,generate_password_hash(password),'student',name,now_iso())); uid=cur.lastrowid
            cur.execute('INSERT INTO students(user_id,student_code,full_name,email,course,year,created_at) VALUES(?,?,?,?,?,?,?)',(uid,code, name, request.form.get('email','').strip(), request.form.get('course','').strip(), request.form.get('year','').strip(), now_iso())); con.commit(); audit('student_created',f'username={username},code={code}'); flash('Student account created.','success'); return redirect(url_for('teacher_dashboard'))
        except sqlite3.IntegrityError: con.rollback(); flash('Username or student code already exists.','error')
        finally: con.close()
    return render_template('add_student.html')


@app.route('/teacher/export.csv')
@login_required('teacher')
def export_csv():
    con=get_db(); rows=con.execute('''SELECT s.student_code,s.full_name,s.course,s.year,p.predicted_score,p.risk_probability,p.performance_category,p.learning_profile,p.created_at
      FROM students s LEFT JOIN predictions p ON p.id=(SELECT MAX(id) FROM predictions WHERE student_id=s.id) ORDER BY s.full_name''').fetchall(); con.close()
    out=io.StringIO(); writer=csv.writer(out); writer.writerow(['Student Code','Name','Course','Year','Predicted Score','Risk %','Category','Learning Profile','Last Prediction'])
    for r in rows: writer.writerow(list(r))
    audit('export_csv', f'rows={len(rows)}')
    return Response(out.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=edupredict_students.csv'})


@app.route('/api/predict', methods=['POST'])
@login_required()
def api_predict():
    try: return jsonify(run_prediction(request.get_json(force=True) or {}))
    except Exception as e: return jsonify({'error':str(e)}),400


@app.route('/api/what-if', methods=['POST'])
@login_required()
def api_what_if():
    """Return baseline and one-factor what-if score changes using vectorized batch inference."""
    try:
        payload = validate_payload(request.get_json(force=True) or {})
        baseline = run_prediction(payload)

        scenario_features = [
            'attendance_percentage',
            'study_hours_per_week',
            'previous_exam_score',
            'assignment_score',
            'internal_assessment_score',
        ]

        vec_base = np.array([float(payload[c]) for c in FEATURE_COLUMNS], dtype=np.float64)
        scenarios_matrix = np.tile(vec_base, (len(scenario_features), 1))

        deltas = []
        for i, feat in enumerate(scenario_features):
            col_idx = FEATURE_COLUMNS.index(feat)
            lo, hi = RANGES[feat]
            new_val = min(hi, max(lo, vec_base[col_idx] + 5.0))
            scenarios_matrix[i, col_idx] = new_val
            deltas.append(round(new_val - vec_base[col_idx], 1))

        df_scenarios = pd.DataFrame(scenarios_matrix, columns=FEATURE_COLUMNS)
        Xs_scenarios = scaler.transform(df_scenarios)

        sc_rf = rf_regressor.predict(Xs_scenarios)
        sc_gb = gb_regressor.predict(Xs_scenarios)
        sc_scores = np.round(np.clip(RF_ENSEMBLE_WEIGHT * sc_rf + GB_ENSEMBLE_WEIGHT * sc_gb, 0, 100), 1)
        sc_risks = classifier.predict_proba(Xs_scenarios)[:, 1]

        scenarios = []
        for i, feat in enumerate(scenario_features):
            sc_score = float(sc_scores[i])
            sc_risk = round(float(sc_risks[i] * 100), 1)
            scenarios.append({
                'feature': feat,
                'change': deltas[i],
                'baseline_score': baseline['predicted_score'],
                'scenario_score': sc_score,
                'score_change': round(sc_score - baseline['predicted_score'], 1),
                'risk_probability': sc_risk,
                'at_risk': bool(sc_risks[i] >= RISK_THRESHOLD),
            })

        return jsonify({'baseline': baseline, 'scenarios': scenarios})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/student/update', methods=['POST'])
@login_required('student')
def api_student_update():
    try:
        con=get_db(); s=con.execute('SELECT id FROM students WHERE user_id=?',(session['user_id'],)).fetchone(); con.close()
        rid,result=save_record(s['id'],request.get_json(force=True) or {}); audit('api_performance_update',f'record_id={rid}'); return jsonify({'record_id':rid,**result})
    except Exception as e: return jsonify({'error':str(e)}),400


@app.route('/api/students')
@login_required('teacher')
def api_students():
    con=get_db(); rows=latest_student_rows(con); con.close(); return jsonify([dict(r) for r in rows])


@app.route('/api/student/<int:student_id>/trend')
@login_required('teacher')
def api_student_trend(student_id):
    con=get_db(); rows=con.execute('''SELECT created_at,predicted_score,risk_probability FROM predictions WHERE student_id=? ORDER BY id ASC LIMIT 50''',(student_id,)).fetchall(); con.close(); return jsonify([dict(r) for r in rows])


@app.route('/api/health')
def api_health():
    return jsonify({'status':'ok','model_loaded':bool(artifacts),'database':os.path.exists(DB_PATH),'features':FEATURE_COLUMNS,'risk_threshold':RISK_THRESHOLD})


@app.route('/predict', methods=['GET','POST'])
@login_required()
def predict():
    result=form_data=None
    if request.method=='POST':
        try: form_data=record_from_form(request.form); result=run_prediction(form_data)
        except Exception as e: flash(str(e),'error')
    return render_template('predict.html',result=result,form_data=form_data,parental_labels=PARENTAL_SUPPORT_LABELS)


def get_dashboard_cache():
    global _DASHBOARD_CACHE
    if _DASHBOARD_CACHE is None:
        metrics = json.load(open(METRICS_PATH, encoding='utf-8')) if os.path.exists(METRICS_PATH) else {}
        category_counts = df.performance_category.value_counts().to_dict()
        parental_avg = df.groupby('parental_support').final_exam_score.mean().round(1).to_dict()
        parental_avg = {PARENTAL_SUPPORT_LABELS[k]: v for k, v in parental_avg.items()}
        bins = pd.cut(df.attendance_percentage, bins=[40, 60, 70, 80, 90, 100])
        ap = df.groupby(bins, observed=True).final_exam_score.mean().round(1)
        _DASHBOARD_CACHE = {
            'metrics': metrics,
            'category_counts': category_counts,
            'parental_avg': parental_avg,
            'attendance_labels': [str(i) for i in ap.index],
            'attendance_values': ap.values.tolist(),
            'feature_importance': metrics.get('feature_importance', [])
        }
    return _DASHBOARD_CACHE


@app.route('/dashboard')
def dashboard():
    data = get_dashboard_cache()
    return render_template('dashboard.html', **data)



@app.errorhandler(404)
def not_found(e): return render_template('error.html', code=404, message='Page not found.'), 404

@app.errorhandler(500)
def server_error(e): return render_template('error.html', code=500, message='Unexpected server error.'), 500


if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1', host='0.0.0.0', port=int(os.environ.get('PORT','5000')))
