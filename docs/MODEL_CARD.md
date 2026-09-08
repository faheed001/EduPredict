# EduPredict 3.0 — Model Card

## Intended use
EduPredict is an academic decision-support prototype for demonstrating how machine learning can estimate student performance and flag students for possible additional support.

## Data
- 1,500 records.
- Synthetic dataset generated for academic demonstration/testing.
- Train/validation/test split: 900/300/300 (60/20/20).

## Input features
The current model uses these features:

- `attendance_percentage`
- `study_hours_per_week`
- `previous_exam_score`
- `assignment_score`
- `internal_assessment_score`
- `extracurricular_activities`
- `parental_support`
- `sleep_hours`

## Models
- Random Forest regression.
- Gradient Boosting regression.
- Validation-weighted regression ensemble.
- Random Forest classification for early warning.
- K-Means learning-profile clustering.
- Isolation Forest anomaly detection.

## Reported test results
- Regression MAE: 4.415.
- Regression R²: 0.657.
- At-risk accuracy: 0.903.
- At-risk precision: 0.471.
- At-risk recall: 0.593.
- At-risk F1: 0.525.
- At-risk ROC-AUC: 0.907.
- Clustering: K=2, silhouette score 0.134.

## Model comparison
- Random Forest: MAE 4.581, R² 0.662.
- Gradient Boosting: MAE 4.192, R² 0.716.
- Ensemble: MAE 4.191, R² 0.716, with validation-selected RF weight 0.08 and GB weight 0.92.

## Limitations
These metrics are based on synthetic data and do not establish real-world educational effectiveness. The risk classifier has a relatively modest minority-class F1 score. Clustering separation is also limited. Outputs are not causal conclusions and should not be used as the sole basis for academic decisions.

## Responsible use
Use predictions as decision-support signals. Educators should review context, communicate with students appropriately, and avoid treating a model score as a fixed judgment of ability.
