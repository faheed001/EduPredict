# EduPredict 3.0 — Judge/Viva Preparation

## Core 10 questions and model answers

1. **Why did you choose this problem?**  EduPredict addresses early identification of students who may need academic support and connects prediction with actionable teacher intervention.
2. **Why Random Forest and Gradient Boosting?**  They capture non-linear relationships and work well with mixed educational indicators. The ensemble combines their predictions to improve robustness.
3. **Why use regression?**  Final exam score is a continuous value, so regression predicts the expected score.
4. **Why classification as well?**  Teachers need an interpretable early-warning flag, so a separate classifier estimates the probability of being at risk.
5. **Why is accuracy not enough?**  The at-risk class is smaller. Precision, recall, F1, confusion matrix and ROC-AUC give a more complete view.
6. **Is the dataset real?**  No. The bundled 1,500 records are synthetic and are used to demonstrate the complete software/ML pipeline. We do not claim external validity.
7. **How did you prevent test leakage?**  We use a stratified 60/20/20 train/validation/test split. The risk threshold is selected on validation data and final metrics are computed on the untouched test set.
8. **What does ROC-AUC 0.907 mean?**  It indicates strong ranking ability for distinguishing higher-risk from lower-risk cases on this held-out synthetic test set; it is not proof of real-world deployment performance.
9. **Why is the silhouette score low?**  The clustering is exploratory. A low score means the learner groups are not strongly separated, so profiles should not be treated as definitive categories.
10. **Can the AI decide whether a student fails?**  No. EduPredict is a decision-support system. Risk flags should trigger human review and supportive intervention, not automatic academic decisions.

## Five numbers to remember
- Dataset: **1,500 synthetic records**
- Split: **60/20/20 train/validation/test**
- Regression: **MAE 4.494, R² 0.648**
- Risk: **ROC-AUC 0.907, F1 0.525**
- Clustering: **K selected automatically, silhouette 0.134**

## Judge-safe wording
Say **"demonstrates the technical pipeline"**, not **"proves the model works on real students."**
Say **"feature sensitivity/counterfactual explanation"**, not **"causal effect."**
Say **"teacher decision support"**, not **"automatic student diagnosis."**
