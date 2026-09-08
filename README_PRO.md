# EduPredict Pro

A more complete Student Performance Prediction and Early Intervention system built on the supplied ML project.

## Added in Pro version
- SQLite live database with migration-safe startup
- Student self-registration and teacher-created student accounts
- Role-based student/teacher dashboards
- CSRF protection for browser POST forms
- Input validation and safe checkbox handling (`extracurricular_activities` defaults to 0)
- Ensemble prediction: Random Forest + Gradient Boosting
- Risk classification, learner profiling and anomaly detection
- Explainable counterfactual feature impacts
- Personalized recommendations and study plan
- Prediction history and trend charts
- Teacher intervention notes with Open / In Progress / Resolved status
- Student profile management
- Teacher search/filter and CSV export
- JSON APIs for prediction, live student data, trends and health checks
- Better responsive UI and error pages

## Demo accounts
Teacher: `teacher` / `teacher123`
Student: `student` / `student123`

## Run on Windows
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py app.py
```
Open `http://127.0.0.1:5000`.

The SQLite database is created at `data/edupredict.db` automatically. The first startup also creates the demo accounts.

## API examples
Authenticated session required.
- `GET /api/health`
- `POST /api/predict`
- `POST /api/student/update` (student)
- `GET /api/students` (teacher)
- `GET /api/student/<id>/trend` (teacher)

## Notes
The model is trained from the supplied dataset and is intended for demonstration/academic project use. Predictions should support, not replace, teacher judgment.
