# EduPredict

**AI-Based Student Performance Prediction & Early Warning System**

EduPredict is a Flask-based educational analytics prototype that combines machine learning, student/teacher workflows, persistent SQLite storage, performance prediction, early-warning risk classification, learning profiles, anomaly detection, personalized recommendations, analytics, and an integrated **EduPredict Assistant**.

> **Academic / Responsible-Use Notice:** The included 1,500-record dataset is synthetic and is provided for academic demonstration and software testing. Model predictions are decision-support signals and should not be treated as definitive judgments of student ability or used as the sole basis for academic decisions.

## Features

- Student and teacher registration/login.
- Student profile and performance management.
- ML-based performance prediction.
- At-risk early-warning classification.
- Prediction history and student trends.
- Personalized recommendations and study plans.
- Feature importance / explainability.
- Learning-profile clustering with K-Means.
- Anomaly detection with Isolation Forest.
- Teacher dashboard, student search and intervention tracking.
- Analytics dashboard with model evidence.
- CSV export and JSON APIs.
- What-if prediction endpoint.
- Integrated **EduPredict Assistant** for system explanations, basic/intermediate educational and technical questions, and student-specific guidance.
- Security headers, CSRF protection and role-based access control.
- Automated tests and project audit tooling.

## Technology stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, Flask |
| Frontend | HTML, CSS, JavaScript |
| Charts | Chart.js |
| Database | SQLite |
| Data | Pandas, NumPy |
| ML | scikit-learn 1.8.0 |
| Model persistence | Joblib |
| Authentication | Werkzeug password hashing + Flask sessions |

## Machine-learning pipeline

```text
Student data
   -> validation
   -> trained ML models
   -> predicted performance
   -> risk probability/category
   -> feature impacts
   -> recommendations
   -> dashboard/history/intervention
```

Models include Random Forest regression, Gradient Boosting regression, a validation-weighted regression ensemble, Random Forest risk classification, K-Means learning profiles, and Isolation Forest anomaly detection.

## Dataset and evaluation

The dataset contains **1,500 synthetic records** with a 60/20/20 train/validation/test split (900/300/300).

| Metric | Test result |
|---|---:|
| Regression MAE | 4.415 |
| Regression R² | 0.657 |
| At-risk accuracy | 0.903 |
| At-risk precision | 0.471 |
| At-risk recall | 0.593 |
| At-risk F1 | 0.525 |
| At-risk ROC-AUC | 0.907 |
| K-Means clusters | 2 |
| Silhouette score | 0.134 |

Model comparison and limitations are documented in [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md).

## Installation on Windows

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python model\train_model.py
python tools\audit_project.py
python app.py
```

Open **http://127.0.0.1:5000**.

## Tests

```powershell
python -m pytest -q
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Model Card](docs/MODEL_CARD.md)
- [Data Dictionary](docs/DATA_DICTIONARY.md)
- [User Guide](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Viva Questions](docs/VIVA_QUESTIONS.md)
- [GitHub Setup](docs/GITHUB_SETUP.md)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Repository topics

`python` `flask` `machine-learning` `scikit-learn` `student-performance` `education` `educational-technology` `data-science` `artificial-intelligence` `sqlite` `predictive-analytics`

## License

MIT License. See [`LICENSE`](LICENSE).
