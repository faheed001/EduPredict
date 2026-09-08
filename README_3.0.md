# EduPredict 3.0 — Judge-Ready AI Early Warning Platform

## What changed in 3.0
- **Leakage-safe evaluation design:** stratified 60/20/20 train/validation/test split.
- **Calibrated risk probabilities:** Random Forest wrapped with sigmoid calibration.
- **Validation-only threshold selection:** operating threshold is selected on validation data; the test set is untouched until final evaluation.
- **Better classification reporting:** ROC-AUC, precision, recall, F1 and confusion matrix are stored.
- **Automatic learner-profile selection:** K is selected from 2–6 using silhouette score rather than hard-coded K=4.
- **Consistent risk policy:** the exact trained threshold is stored in the model artifact and used by both batch import and live prediction.
- **Human-in-the-loop policy:** risk flags are recommendations for teacher review, not automatic academic decisions.
- **Model card:** limitations, intended use and responsible-use guidance are documented.
- **Regression tests:** syntax, metrics contract and database schema checks are included.
- **Database schema versioning marker:** the application records schema version 3.0.
- **Analytics transparency:** the UI now displays validation design, threshold, precision/recall/F1 and clustering quality.

## Remaining scientific limitation
The bundled 1,500-row dataset is synthetic. The project therefore demonstrates the complete ML/software pipeline but does **not** claim external validity on real students. Real deployment requires institution-approved anonymized data, temporal validation, fairness analysis, calibration monitoring, privacy review and human oversight.


## Judge-ready upgrades in this build
- **System architecture diagram:** `ARCHITECTURE.svg` shows users, Flask, ML engine, analytics, database and decision-support flow.
- **Model comparison:** validation-set MAE/R² for Random Forest, Gradient Boosting and the ensemble are displayed in the ML Analytics dashboard.
- **ROC + confusion matrix:** the dashboard now shows the held-out test ROC curve and confusion matrix so accuracy is not presented in isolation.
- **Synthetic-data disclosure:** the dashboard, README and Model Card explicitly state that the 1,500 records are synthetic and that external validity is not claimed.
- **Viva preparation:** `JUDGE_VIVA_PREP.md` contains judge-safe answers and the key numbers to remember.
- **Deployment hardening:** Flask debug mode is disabled by default and production deployments are expected to provide `EDUPREDICT_SECRET`.

## Final Judge-Readiness Improvements
- The Flask app now uses the validation-selected ensemble weights stored with the trained model, so runtime predictions match the evaluated ensemble configuration.
- Security response headers are applied centrally, including content-type, framing and referrer protections.
- A functional/security test suite is included under `tests/test_app_functional.py` for environments with the project dependencies installed.
- `PRESENTATION_95_READY.md` contains the recommended live-demo order, key metrics and judge-safe wording.
