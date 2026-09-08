# EduPredict 3.0 — 95+ Presentation Plan

## 1. Opening (30 seconds)
**Problem:** Colleges often identify struggling students only after examination results. EduPredict provides an early-warning and decision-support workflow using attendance, study habits, previous scores, assignments, internal assessment, sleep, parental support and extracurricular activity.

**One-line contribution:** A role-based student platform that combines performance prediction, risk scoring, learner profiling, anomaly detection, explainability, recommendations and teacher interventions in one workflow.

## 2. Live Demo Order
1. Open home page and point out the 1,500-record synthetic dataset disclosure.
2. Student login.
3. Show student dashboard and current prediction.
4. Enter/update performance data.
5. Show predicted score, performance category and risk probability.
6. Show feature impacts and recommendations/study plan.
7. Teacher login.
8. Show the 1,500-student list.
9. Filter mentally/visually for at-risk students and open one profile.
10. Add a teacher intervention note and status.
11. Open analytics and explain the validation/test design.
12. Show model comparison, ROC-AUC, confusion matrix and feature importance.

## 3. Three Numbers to Memorize
- Dataset: **1,500 synthetic student records**
- Regression test result: **MAE 4.415, R² 0.657**
- Risk model test result: **ROC-AUC 0.907, F1 0.525, recall 0.593**

## 4. Model Method
- 60/20/20 train/validation/test split.
- Regression: Random Forest + Gradient Boosting, with ensemble weight selected on validation data.
- Classification: calibrated Random Forest with operating threshold selected on validation data.
- Clustering: KMeans, K selected from 2–6 using silhouette score.
- Anomaly detection: Isolation Forest.

## 5. Judge-Safe Answers
**Why synthetic data?**
The bundled dataset is explicitly synthetic and is used to demonstrate the complete technical pipeline. Real institutional data would require permission, privacy controls and external validation.

**Why is F1 lower than accuracy?**
The at-risk class is much smaller than the non-risk class, so accuracy can hide minority-class errors. We therefore report precision, recall, F1 and ROC-AUC rather than accuracy alone.

**Can the system decide that a student will fail?**
No. It is a teacher decision-support system. The prediction is a probabilistic signal, not a final academic judgment.

**Is feature impact causal?**
No. It is a model-sensitivity/counterfactual explanation showing how the prediction changes when one input is replaced by a reference value.

**Why is the clustering silhouette score modest?**
The input variables overlap continuously rather than forming perfectly separated groups. The clustering is therefore exploratory and is not used as a high-stakes decision by itself.

## 6. What Not to Claim
- Do not claim real-world accuracy from synthetic data.
- Do not call feature impact a causal effect.
- Do not say the AI automatically diagnoses or decides a student's future.
- Do not hide the F1 or clustering limitations if asked.

## 7. If Asked About Future Work
1. Validate on anonymized real institutional data from multiple semesters.
2. Compare calibration and fairness across relevant student groups when ethically and legally appropriate.
3. Add longitudinal evaluation to measure whether interventions improve outcomes.
4. Move from SQLite to PostgreSQL for multi-user production deployment.
5. Add stronger automated end-to-end and load testing.
