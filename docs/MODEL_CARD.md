# EduPredict 3.0 — Model Card

## Intended Use
EduPredict is an institutional early-warning decision-support system designed to forecast continuous exam performance and detect academic vulnerability before final evaluations.

## Data & Empirical Grounding
- **1,500 records** generated from empirical educational dynamics literature (Tinto's Retention Model, Astin's Involvement Theory, Cortez & Silva 2008).
- Features non-linear diminishing returns to study ($\ln(1+\text{hours})$), attendance threshold penalties ($<75\%$), and coursework consistency interactions.
- **Protocol:** Stratified 60/20/20 train/validation/test split (900 / 300 / 300 records).

## Input Features
1. `attendance_percentage` (40.0 - 100.0)
2. `study_hours_per_week` (0.0 - 40.0)
3. `previous_exam_score` (0.0 - 100.0)
4. `assignment_score` (0.0 - 100.0)
5. `internal_assessment_score` (0.0 - 100.0)
6. `extracurricular_activities` (0 or 1)
7. `parental_support` (0: Low, 1: Medium, 2: High)
8. `sleep_hours` (4.0 - 10.0)

## Multi-Model Benchmarking Suite
| Model | Task | Val / Test Metric | Role |
|---|---|---|---|
| **Ridge Regression** | Regression Baseline | Val MAE: 2.113, R²: 0.983 | Linear Benchmark |
| **Logistic Regression** | Classification Baseline | Val ROC-AUC: 0.989 | Linear Benchmark |
| **Random Forest Regressor** | Non-linear Regression | Val MAE: 1.896, R²: 0.983 | Tree Ensemble Component |
| **Gradient Boosting Regressor** | Non-linear Regression | Val MAE: 1.888, R²: 0.983 | Boosting Component |
| **Validation-Weighted Ensemble** | Regression Final | Test MAE: 2.164, R²: 0.978 | Production Regressor (RF 0.15, GB 0.85) |
| **Calibrated Random Forest** | Risk Classification | Test ROC-AUC: 0.994, F1: 0.953 | Production Early Warning (Recall 96.8%, Prec 93.8%) |
| **K-Means Clustering** | Learner Profiling | Silhouette Score: 0.594 (K=2) | Statistically Validated Archetypes |
| **Isolation Forest** | Outlier Detection | Contamination: 5% | Pattern Anomaly Detector |

## Explainability Engine
Local Additive Feature Attribution decomposes how each feature moves an individual student's score relative to the cohort population expectation $\mathbb{E}[X]$.

## Responsible AI Safeguards
EduPredict is explicitly architected as human-in-the-loop decision support. Predictions must never trigger automatic penalties or academic actions without human review.
