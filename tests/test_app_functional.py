import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Keep tests isolated from a developer's environment.
os.environ.setdefault('EDUPREDICT_SECRET', 'test-secret-for-edupredict')
os.environ.setdefault('FLASK_DEBUG', '0')

import app


def login(client, username, password):
    with client.session_transaction() as sess:
        sess['csrf_token'] = 'test-csrf'
    return client.post('/login', data={
        'username': username,
        'password': password,
        '_csrf': 'test-csrf',
    }, follow_redirects=False)


def test_public_health_and_security_headers():
    client = app.app.test_client()
    response = client.get('/api/health')
    assert response.status_code == 200
    body = response.get_json()
    assert body['status'] == 'ok'
    assert body['model_loaded'] is True
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'
    assert 'default-src' in response.headers['Content-Security-Policy']


def test_role_protection_and_prediction_flow():
    client = app.app.test_client()
    denied = client.get('/teacher/dashboard')
    assert denied.status_code == 302
    assert '/login' in denied.location

    logged_in = login(client, 'student', 'student123')
    assert logged_in.status_code == 302

    with client.session_transaction() as sess:
        token = sess['csrf_token']

    response = client.post('/api/predict', json={
        'attendance_percentage': 90,
        'study_hours_per_week': 15,
        'previous_exam_score': 75,
        'assignment_score': 80,
        'internal_assessment_score': 78,
        'extracurricular_activities': 1,
        'parental_support': 2,
        'sleep_hours': 8,
    }, headers={'X-CSRF-Token': token})
    assert response.status_code == 200
    result = response.get_json()
    assert 0 <= result['predicted_score'] <= 100
    assert 0 <= result['risk_probability'] <= 100
    assert isinstance(result['recommendations'], list)
    assert len(result['feature_impacts']) <= 5


def test_student_api_requires_csrf():
    client = app.app.test_client()
    login(client, 'student', 'student123')
    response = client.post('/api/student/update', json={
        'attendance_percentage': 90,
        'study_hours_per_week': 12,
        'previous_exam_score': 70,
        'assignment_score': 70,
        'internal_assessment_score': 70,
        'extracurricular_activities': 0,
        'parental_support': 1,
        'sleep_hours': 8,
    })
    assert response.status_code == 400


def test_what_if_api_simulation():
    client = app.app.test_client()
    login(client, 'student', 'student123')
    with client.session_transaction() as sess:
        token = sess['csrf_token']

    payload = {
        'attendance_percentage': 82,
        'study_hours_per_week': 14,
        'previous_exam_score': 68,
        'assignment_score': 72,
        'internal_assessment_score': 70,
        'extracurricular_activities': 1,
        'parental_support': 1,
        'sleep_hours': 7.5,
    }
    response = client.post('/api/what-if', json=payload, headers={'X-CSRF-Token': token})
    assert response.status_code == 200
    data = response.get_json()
    assert 'baseline' in data
    assert 'scenarios' in data
    assert 0 <= data['baseline']['predicted_score'] <= 100
    assert len(data['scenarios']) == 5
    for sc in data['scenarios']:
        assert 'feature' in sc
        assert 'score_change' in sc
        assert 'scenario_score' in sc


def test_assistant_api_student_and_teacher():
    client = app.app.test_client()

    # 1. Missing CSRF token is rejected with 400
    res_no_csrf = client.post('/api/assistant', json={'message': 'hello'})
    assert res_no_csrf.status_code == 400

    # 2. Unauthenticated request with CSRF redirects to login (302)
    with client.session_transaction() as sess:
        sess['csrf_token'] = 'test-csrf'
    res_unauth = client.post('/api/assistant', json={'message': 'hello'}, headers={'X-CSRF-Token': 'test-csrf'})
    assert res_unauth.status_code == 302
    assert '/login' in res_unauth.location

    # 2. Student query
    login(client, 'student', 'student123')
    with client.session_transaction() as sess:
        token = sess['csrf_token']

    res_student = client.post('/api/assistant', json={
        'message': 'What is my predicted score?'
    }, headers={'X-CSRF-Token': token})
    assert res_student.status_code == 200
    data_student = res_student.get_json()
    assert 'answer' in data_student
    assert 'suggestions' in data_student
    assert len(data_student['suggestions']) > 0
    assert data_student['role'] == 'student'

    # Theory query
    res_theory = client.post('/api/assistant', json={
        'message': 'Why use an ensemble over linear baseline?'
    }, headers={'X-CSRF-Token': token})
    assert res_theory.status_code == 200
    data_theory = res_theory.get_json()
    assert 'Ridge' in data_theory['answer']
    assert 'MAE' in data_theory['answer']

    # 3. Teacher query
    client.get('/logout')
    login(client, 'teacher', 'teacher123')
    with client.session_transaction() as sess:
        t_token = sess['csrf_token']

    res_teacher = client.post('/api/assistant', json={
        'message': 'Cohort risk overview'
    }, headers={'X-CSRF-Token': t_token})
    assert res_teacher.status_code == 200
    data_teacher = res_teacher.get_json()
    assert 'Cohort Executive Briefing' in data_teacher['answer']
    assert 'Active Students' in data_teacher['answer']
    assert data_teacher['role'] == 'teacher'


