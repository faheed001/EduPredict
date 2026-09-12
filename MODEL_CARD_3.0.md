# EduPredict 3.0 Model Card

## Purpose
Early-warning decision support for identifying students who may benefit from timely academic guidance before final examinations. The model is a decision-support aid and must never be used as the sole basis for academic actions or disciplinary sanctions.

## Data Architecture
The dataset contains 1,500 records modeled after empirical learning analytics dynamics (Tinto's Retention Model, Astin's Involvement Theory, and Cortez & Silva 2008). It features non-linear study diminishing returns, an attendance detention cliff (<75%), coursework consistency interactions, and 4 distinct student behavioral archetypes.

## Inputs
Attendance percentage, weekly study hours, previous exam score, assignment score, internal assessment score, extracurricular participation, parental support, and sleep hours.

## Validation & Benchmarking
A strict stratified 60/20/20 train/validation/test split (900/300/300) is used. The ensemble weights and cost-sensitive classification threshold are selected exclusively on validation data; final metrics are evaluated on the untouched test set.

## Model Family & Comparative Baselines
- **Linear Baseline:** Ridge Regression (Val MAE: 2.113, R²: 0.983)
- **Classification Baseline:** Logistic Regression (Val ROC-AUC: 0.989)
- **Advanced Regression:** Tuned Random Forest + Gradient Boosting Ensemble (Test MAE: 2.164, R²: 0.978)
- **Calibrated Early-Warning Classification:** Calibrated Random Forest (Test ROC-AUC: 0.994, F1: 0.953, Recall: 96.8%, Precision: 93.8%)
- **Clustering:** K-Means with silhouette optimization (K=2, Silhouette: 0.594)
- **Anomaly Detection:** Isolation Forest for outlier learner pattern screening
- **Explainability:** Local Additive Feature Attribution against cohort population expectations

## Risk Policy & Responsible AI
Recall is maximized (96.8%) to ensure failing students are not missed, while maintaining 93.8% precision to prevent alert fatigue. Flags prompt empathetic teacher reviews and remedial planning, never automated academic decisions.
