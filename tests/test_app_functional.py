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
