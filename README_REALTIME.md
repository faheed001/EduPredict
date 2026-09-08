# EduPredict - Real-Time Student Performance System

## New features
- SQLite persistent database (`data/edupredict.db`) for live records.
- Student and teacher authentication with hashed passwords.
- Student dashboard and performance update page.
- Teacher dashboard with latest prediction and risk monitoring for every student.
- Every saved performance record immediately runs the trained ensemble ML model.
- Prediction history is stored for progress tracking.
- JSON APIs: `/api/predict`, authenticated `/api/student/update`, and authenticated teacher `/api/students`.

## Demo accounts
- Teacher: `teacher` / `teacher123`
- Student: `student` / `student123`

Change the demo passwords and `EDUPREDICT_SECRET` before production use.

## Run
```bash
pip install -r requirements.txt
python app.py
```
Open `http://localhost:5000` and use Login.

## Architecture
Browser -> Flask -> SQLite live data -> ML prediction pipeline -> prediction history -> student/teacher dashboards.

The model is not retrained on every update. It uses the existing trained model to score the newest data immediately. Model retraining can be scheduled later using accumulated institution data.
