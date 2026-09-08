# EduPredict 3.0 Model Card

## Purpose
Early-warning decision support for identifying students who may need academic review before a final assessment. The model is not a diagnosis and must not be used as the sole basis for academic decisions.

## Data
The bundled dataset contains 1,500 synthetic student records generated for academic demonstration. It is not evidence of performance on a real institution population.

## Inputs
Attendance, weekly study hours, previous exam score, assignment score, internal assessment score, extracurricular participation, parental support, and sleep hours.

## Validation
A stratified 60/20/20 train/validation/test split is used. The classifier operating threshold is selected using validation data only; the final classification metrics are computed on the untouched test set.

## Outputs
Predicted final score, risk probability, risk flag, performance category, exploratory learner profile, unusual-pattern signal, feature impact explanation, and study recommendations.

## Risk policy
Recall is prioritized because the application is an early-warning workflow. False positives should trigger human review rather than automatic punitive action.

## Limitations
Synthetic data, potential dataset shift, limited feature set, non-causal explanations, and exploratory clustering quality. Real deployment requires institution-specific validation, privacy review, fairness analysis, monitoring, and human oversight.
