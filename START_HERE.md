# EduPredict 3.0 — Final Start Guide

## Recommended Windows setup

Use **Python 3.14** for this project. The bundled Joblib/scikit-learn model artifacts are pinned to **scikit-learn 1.8.0** and are used with Python 3.14. The project is configured and tested for Python 3.14.

### One-click setup

1. Extract the ZIP completely.
2. Double-click `SETUP_WINDOWS.bat`.
3. The script automatically removes a stale `.venv` and creates a clean Python 3.14 environment.
4. Wait for dependency installation, model training, and the project audit to finish.
5. Double-click `RUN_WINDOWS.bat`.
6. Open `http://127.0.0.1:5000`.

### Manual setup

```cmd
py -3.14 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python model\train_model.py
python tools\audit_project.py
python app.py
```

## Demo accounts

- Teacher: `teacher` / `teacher123`
- Student: `student` / `student123`

## Main features

- Student and teacher authentication
- SQLite live/persistent database
- Automatic import of 1,500 dataset students
- AI performance prediction
- At-risk early warning
- Learning-profile clustering
- Anomaly detection
- Explainable model-sensitivity analysis
- Personalized recommendations and study plan
- Teacher interventions
- Performance trends and ML analytics
- Model comparison, ROC and feature-importance views
- CSV export and JSON APIs
- CSRF protection and security headers
- **EduPredict AI Assistant** integrated with prediction results

## Important academic disclosure

The bundled dataset contains 1,500 **synthetic** student records. The model demonstrates an end-to-end AI decision-support pipeline. Predictions should not be treated as final academic judgments or causal claims.
