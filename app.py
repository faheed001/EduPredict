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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACT_PATH = os.path.join(BASE_DIR, 'model', 'artifacts.joblib')
METRICS_PATH = os.path.join(BASE_DIR, 'model', 'metrics.json')
DATA_PATH = os.path.join(BASE_DIR, 'data', 'student_performance_dataset.csv')
DB_PATH = os.path.join(BASE_DIR, 'data', 'edupredict.db')

app = Flask(__name__)
app.secret_key = os.environ.get('EDUPREDICT_SECRET') or 'demo-secret-change-me'
# Production deployments must set EDUPREDICT_SECRET; the fallback exists only for local academic demos.
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

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
df = pd.read_csv(DATA_PATH)
PARENTAL_SUPPORT_LABELS = {0: 'Low', 1: 'Medium', 2: 'High'}

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
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
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
    response.headers.setdefault('Content-Security-Policy', "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data:; connect-src 'self'; font-src 'self' https://cdn.jsdelivr.net; frame-ancestors 'self'")
    if request.is_secure:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response


def build_feature_vector(payload):
    return np.array([float(payload[c]) for c in FEATURE_COLUMNS], dtype=float).reshape(1, -1)


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
    impacts = []
    for feat in FEATURE_COLUMNS:
        changed = dict(payload)
        changed[feat] = float(df[feat].median())
        alt = predict_score(scaler.transform(build_feature_vector(changed)))
        impacts.append({'feature': feat, 'impact': round(base_score - alt, 2)})
    return sorted(impacts, key=lambda x: abs(x['impact']), reverse=True)


def run_prediction(payload):
    payload = validate_payload(payload)
    X = build_feature_vector(payload); Xs = scaler.transform(X)
    score = round(max(0, min(100, predict_score(Xs))), 1)
    risk = float(classifier.predict_proba(Xs)[0][1])
    at_risk = bool(risk >= RISK_THRESHOLD)
    category = 'High' if score >= 75 else ('Medium' if score >= 50 else 'Low')
    profile_id = int(kmeans.predict(cluster_scaler.transform(X))[0])
    profile = profile_names.get(profile_id, 'General Learner')
    anomaly = int(anomaly_detector.predict(cluster_scaler.transform(X))[0]) == -1

    weak = []
    for item in FEATURE_IMPORTANCE:
        feat = item[0]
        if feat != 'extracurricular_activities' and float(payload[feat]) < float(df[feat].median()):
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

    source = pd.read_csv(DATA_PATH)
    if source.empty:
        return 0

    con = get_db()
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
        name = f"Dataset Student {sid_num:04d}"
        email = f"student{sid_num:04d}@example.com"

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

    q = message.lower()
    con = get_db()
    student = None
    latest = None
    if session.get('role') == 'student':
        student = con.execute('SELECT * FROM students WHERE user_id=?', (session['user_id'],)).fetchone()
    if student:
        latest = con.execute('SELECT * FROM predictions WHERE student_id=? ORDER BY id DESC LIMIT 1', (student['id'],)).fetchone()
    con.close()

    def has(*terms):
        return any(term in q for term in terms)

    # 1) EduPredict system/features and workflow
    if has('what is edupredict', 'what does edupredict', 'about edupredict', 'about this system', 'this system'):
        answer = ('EduPredict is an AI-based student performance support system. It combines student academic data, '
                  'machine-learning prediction, risk classification, learning profiles, anomaly detection, explanations, '
                  'personalized recommendations, study planning, dashboards, prediction history, and teacher interventions. '
                  'Its purpose is to help students and teachers identify learning needs early and make informed decisions.')
    elif has('features', 'feature', 'modules', 'module', 'what can this system do', 'what are the functions'):
        answer = ('EduPredict features include: student and teacher authentication; student profile and academic-data management; '
                  'AI performance prediction; at-risk probability and risk classification; prediction history; personalized '
                  'recommendations; study-plan generation; learning-profile clustering; anomaly detection; explainable feature '
                  'impacts; student and teacher dashboards; student search and filtering; teacher intervention notes; analytics; '
                  'CSV export; JSON APIs; and this EduPredict Assistant.')
    elif has('workflow', 'how does the system work', 'how does edupredict work', 'prediction process', 'prediction pipeline'):
        answer = ('The main workflow is: 1) the student enters or updates academic indicators, 2) the application validates the '
                  'input, 3) the trained ML models process the features, 4) the system predicts a performance score, 5) a risk '
                  'classifier estimates at-risk probability, 6) explainability highlights important factors, 7) recommendations '
                  'and a study plan are generated, and 8) the result is stored so students and teachers can review progress over time.')
    elif has('student dashboard', 'student features', 'student can do', 'student module'):
        answer = ('The Student Dashboard lets a student view their profile, academic records, latest prediction, risk status, '
                  'recommendations, study plan, prediction history, and teacher interventions. Students can update relevant '
                  'academic information and run a new prediction when supported by the system.')
    elif has('teacher dashboard', 'teacher features', 'teacher can do', 'teacher module'):
        answer = ('The Teacher Dashboard helps teachers monitor students, review predicted performance and risk, inspect trends '
                  'and explanations, search or filter students, and record intervention notes. This supports early intervention '
                  'rather than replacing teacher judgment.')
    elif has('database', 'sqlite', 'data storage', 'stored data'):
        answer = ('EduPredict uses SQLite for persistent application data such as users, student profiles, performance records, '
                  'predictions, interventions, and audit information. The ML model artifacts are stored separately and loaded by the Flask application.')
    elif has('login', 'registration', 'register', 'authentication'):
        answer = ('The system provides role-based authentication for students and teachers. Passwords are stored as secure hashes, '
                  'sessions identify the logged-in user, and protected routes restrict features according to the user role.')
    elif has('prediction history', 'history'):
        answer = ('Prediction History stores previous prediction results so performance can be reviewed over time. It helps users '
                  'compare outcomes, identify changes, and discuss progress with teachers.')
    elif has('recommendation', 'recommendations'):
        if latest and latest['details_json']:
            details = json.loads(latest['details_json'])
            recs = details.get('recommendations', [])
            answer = 'Your latest recommendations are: ' + ' '.join(recs[:5]) if recs else ('The recommendation module converts important performance signals into practical actions, '
                      'such as improving attendance, study consistency, assignments, or weak academic areas.')
        else:
            answer = ('The recommendation module converts important performance signals into practical actions, such as improving '
                      'attendance, study consistency, assignments, or weak academic areas.')
    elif has('study plan', 'study planning', 'study planner'):
        if latest and latest['details_json']:
            details = json.loads(latest['details_json'])
            plan = details.get('study_plan', [])
            answer = 'Your latest suggested study plan is: ' + ' '.join(plan[:5]) if plan else ('The study planner suggests consistent study blocks, revision, assignment completion, '
                      'focus on weak topics, and weekly progress review.')
        else:
            answer = ('The study planner suggests consistent study blocks, revision, assignment completion, focus on weak topics, '
                      'and weekly progress review.')
    elif has('risk level', 'risk status', 'at risk', 'risk probability', 'risk detection', 'early warning'):
        if latest:
            answer = f"Your latest risk probability is {latest['risk_probability']}%. The system currently marks you {'at risk' if latest['at_risk'] else 'not at risk'}. This is an early-warning decision-support signal, not a final judgment."
        else:
            answer = ('Risk detection estimates the probability that a student may be in an at-risk category. It is intended to '
                      'support early intervention. No current student prediction is available in your account yet.')
    elif has('predicted score', 'my score', 'prediction score', 'predicted performance'):
        if latest:
            answer = f"Your latest predicted score is {latest['predicted_score']:.1f}/100, classified as {latest['performance_category']} performance."
        else:
            answer = 'No prediction is available yet. Run an AI prediction first.'

    # 2) ML concepts used by EduPredict
    elif has('random forest'):
        answer = ('Random Forest is an ensemble of decision trees. Each tree learns from a different sample and feature subset, '
                  'then their outputs are combined. EduPredict uses Random Forest as one of its prediction models because it can '
                  'capture nonlinear relationships and is relatively robust on tabular student data.')
    elif has('gradient boosting', 'gradient boost'):
        answer = ('Gradient Boosting builds models sequentially. Each new tree focuses on reducing the errors made by the previous '
                  'trees. It is useful for structured/tabular data and is one of the regression models evaluated in EduPredict.')
    elif has('ensemble', 'model combination'):
        answer = ('An ensemble combines predictions from more than one model. In EduPredict, validation results are used to select '
                  'the contribution of the available regression models, aiming to improve generalization compared with relying on a single model.')
    elif has('regression') and has('classification'):
        answer = ('Regression predicts a continuous value, such as a performance score out of 100. Classification predicts a '
                  'category, such as at-risk versus not-at-risk. EduPredict uses regression for score prediction and classification '
                  'for early-warning risk assessment.')
    elif has('regression'):
        answer = ('Regression is a supervised-learning task for predicting a numeric value. In EduPredict, the regression component '
                  'predicts a student performance score.')
    elif has('classification'):
        answer = ('Classification is a supervised-learning task for predicting a category. In EduPredict, classification is used '
                  'to support the at-risk versus not-at-risk decision and risk probability.')
    elif has('k-means', 'k means', 'learning profile', 'clustering'):
        answer = ('K-Means is an unsupervised clustering algorithm. It groups students with similar patterns in selected academic '
                  'features. EduPredict uses clustering to create learning profiles that can support more targeted guidance.')
    elif has('anomaly', 'isolation forest', 'outlier'):
        answer = ('Anomaly detection identifies records whose patterns differ substantially from typical student data. EduPredict '
                  'uses this type of analysis to flag unusual academic patterns for review. An anomaly is a signal to investigate, '
                  'not proof that something is wrong.')
    elif has('feature importance', 'important features', 'feature impact', 'explainability', 'why prediction'):
        answer = ('Feature importance or feature impact explains which input variables contribute most to a model output. In '
                  'EduPredict, this helps users understand the main factors associated with a prediction instead of receiving only a score.')
    elif has('overfitting'):
        answer = ('Overfitting happens when a model learns the training data too closely and performs worse on unseen data. '
                  'Train/validation/test splits and evaluation on unseen test data help detect and reduce this problem.')
    elif has('train test', 'training data', 'validation set', 'data split'):
        answer = ('A training set is used to learn model patterns, a validation set is used to compare or tune model choices, and '
                  'a test set is kept for final evaluation on unseen data. This separation helps produce a more honest estimate of model performance.')
    elif has('mae', 'mean absolute error'):
        answer = ('MAE, or Mean Absolute Error, is the average absolute difference between predicted and actual numeric values. '
                  'Lower MAE is better; an MAE of 4.4 would mean predictions are about 4.4 score points away from actual values on average, subject to the evaluation dataset.')
    elif has('r2', 'r²', 'r squared'):
        answer = ('R² measures how much of the variation in the target is explained by a regression model. Values closer to 1 generally indicate better fit, while the metric should always be interpreted on unseen evaluation data.')
    elif has('precision', 'recall', 'f1', 'f1 score', 'roc-auc', 'auc'):
        answer = ('For risk classification, precision measures how many predicted at-risk students were actually at risk; recall measures '
                  'how many actual at-risk students were detected; F1 balances precision and recall; ROC-AUC summarizes ranking '
                  'performance across classification thresholds. For early warning, recall can be especially important because missed at-risk students matter.')

    # 3) Basic/intermediate educational and technical questions
    elif has('what is ai', 'what is artificial intelligence'):
        answer = 'Artificial Intelligence (AI) is the field of building systems that can perform tasks that normally require human-like intelligence, such as learning from data, recognizing patterns, reasoning, and making predictions.'
    elif has('what is machine learning', 'what is ml'):
        answer = 'Machine Learning (ML) is a branch of AI in which algorithms learn patterns from data and use those patterns to make predictions or decisions on new data.'
    elif has('what is python', 'python language'):
        answer = 'Python is a high-level programming language widely used for web development, automation, data analysis, and machine learning. EduPredict uses Python with Flask, pandas, NumPy, and scikit-learn.'
    elif has('what is flask'):
        answer = 'Flask is a lightweight Python web framework. EduPredict uses Flask to provide web pages, authentication, API endpoints, and the connection between the user interface, database, and ML model.'
    elif has('what is sql', 'what is sqlite'):
        answer = 'SQL is a language used to create, read, update, and manage data in relational databases. SQLite is a lightweight relational database engine that stores the database in a file and is used by EduPredict for persistent application data.'
    elif has('what is database', 'database meaning'):
        answer = 'A database is an organized system for storing and retrieving information. EduPredict uses a database to persist users, student information, academic records, predictions, and intervention records.'
    elif has('what is attendance'):
        answer = 'Attendance is the proportion or record of classes a student attends. In EduPredict, attendance is an input feature that can contribute to the prediction, but the model should not be interpreted as proving that attendance alone causes an outcome.'
    elif has('what is gpa'):
        answer = 'GPA, or Grade Point Average, is a numerical summary of academic performance based on grades or grade points. The exact calculation depends on the institution.'
    elif has('what is api', 'api meaning'):
        answer = 'An API, or Application Programming Interface, is a way for software components to communicate. EduPredict provides JSON API endpoints for application features such as prediction and the EduPredict Assistant.'
    elif has('what is json'):
        answer = 'JSON, or JavaScript Object Notation, is a lightweight text format commonly used to exchange structured data between a web client and a server.'
    elif has('what is csv'):
        answer = 'CSV, or Comma-Separated Values, is a simple tabular file format. EduPredict uses CSV data for the student-performance dataset and supports data export in relevant analytics workflows.'
    elif has('what is cybersecurity', 'security'):
        answer = ('Cybersecurity is the practice of protecting applications, systems, and data from unauthorized access or misuse. '
                  'EduPredict includes measures such as password hashing, session-based access control, CSRF protection, and security headers, but a production deployment would still require further security review.')
    elif has('what is web application', 'web app'):
        answer = 'A web application is software accessed through a web browser. EduPredict is a Flask web application with HTML/CSS/JavaScript on the front end and Python, SQLite, and machine-learning components on the back end.'
    elif has('hello', 'hi', 'hey'):
        answer = ('Hello! I am the EduPredict Assistant. I can explain the system features and workflow, answer basic and intermediate '
                  'AI/ML/programming questions, and—when available—explain your own prediction, risk, recommendations, and study plan.')
    else:
        answer = ('I can explain EduPredict features, system workflow, student/teacher dashboards, prediction, risk detection, '
                  'recommendations, study planning, database and security, or technical concepts such as AI, ML, Random Forest, '
                  'Gradient Boosting, K-Means, MAE, R², precision, recall, F1, and ROC-AUC. Try asking “What features does EduPredict have?”')

    audit('assistant_query', message)
    return jsonify({'answer': answer})


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
    """Return baseline and one-factor what-if score changes without saving data."""
    try:
        payload = validate_payload(request.get_json(force=True) or {})
        baseline = run_prediction(payload)
        scenarios = []
        changes = {
            'attendance_percentage': 5,
            'study_hours_per_week': 5,
            'previous_exam_score': 5,
            'assignment_score': 5,
            'internal_assessment_score': 5,
        }
        for feature, delta in changes.items():
            changed = dict(payload)
            lo, hi = RANGES[feature]
            changed[feature] = min(hi, max(lo, changed[feature] + delta))
            result = run_prediction(changed)
            scenarios.append({
                'feature': feature,
                'change': round(changed[feature] - payload[feature], 1),
                'baseline_score': baseline['predicted_score'],
                'scenario_score': result['predicted_score'],
                'score_change': round(result['predicted_score'] - baseline['predicted_score'], 1),
                'risk_probability': result['risk_probability'],
                'at_risk': result['at_risk'],
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


@app.route('/dashboard')
def dashboard():
    with open(METRICS_PATH) as f: metrics=json.load(f)
    category_counts=df.performance_category.value_counts().to_dict()
    parental_avg=df.groupby('parental_support').final_exam_score.mean().round(1).to_dict(); parental_avg={PARENTAL_SUPPORT_LABELS[k]:v for k,v in parental_avg.items()}
    bins=pd.cut(df.attendance_percentage,bins=[40,60,70,80,90,100]); ap=df.groupby(bins,observed=True).final_exam_score.mean().round(1)
    return render_template('dashboard.html',metrics=metrics,category_counts=category_counts,parental_avg=parental_avg,attendance_labels=[str(i) for i in ap.index],attendance_values=ap.values.tolist(),feature_importance=metrics['feature_importance'])


@app.errorhandler(404)
def not_found(e): return render_template('error.html', code=404, message='Page not found.'), 404

@app.errorhandler(500)
def server_error(e): return render_template('error.html', code=500, message='Unexpected server error.'), 500


if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1', host='0.0.0.0', port=int(os.environ.get('PORT','5000')))
