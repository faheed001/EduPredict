"""
generate_dataset.py
--------------------
Generates a synthetic but realistic student academic performance dataset.

Features:
    - attendance_percentage      : 40 - 100
    - study_hours_per_week       : 0 - 40
    - previous_exam_score        : 0 - 100  (last term's average score)
    - assignment_score           : 0 - 100  (average assignment marks)
    - internal_assessment_score  : 0 - 100  (mid-term / internal marks)
    - extracurricular_activities : 0 or 1   (participates or not)
    - parental_support           : 0 (Low), 1 (Medium), 2 (High)
    - sleep_hours                : 4 - 10

Target:
    - final_exam_score  (continuous, 0-100)  -> used for regression
    - performance_category (Low / Medium / High) -> used for classification
    - at_risk (1 if final_exam_score < 50 else 0) -> used for early-warning classification

The score is generated using a weighted combination of the features plus
random noise, so the dataset has learnable, realistic relationships
(similar to real educational research findings).
"""

import numpy as np
import pandas as pd

RANDOM_SEED = 42
N_STUDENTS = 1500


def generate_dataset(n=N_STUDENTS, seed=RANDOM_SEED):
    rng = np.random.default_rng(seed)

    student_id = np.arange(1, n + 1)

    attendance_percentage = np.clip(rng.normal(75, 15, n), 40, 100)
    study_hours_per_week = np.clip(rng.normal(13, 8, n), 0, 40)
    previous_exam_score = np.clip(rng.normal(62, 18, n), 0, 100)
    assignment_score = np.clip(rng.normal(67, 16, n), 0, 100)
    internal_assessment_score = np.clip(rng.normal(65, 15, n), 0, 100)
    extracurricular_activities = rng.choice([0, 1], size=n, p=[0.55, 0.45])
    parental_support = rng.choice([0, 1, 2], size=n, p=[0.25, 0.45, 0.30])
    sleep_hours = np.clip(rng.normal(7, 1.3, n), 4, 10)

    # Weighted "true" academic ability signal + noise -> final exam score
    noise = rng.normal(0, 4.5, n)
    final_exam_score = (
        0.22 * attendance_percentage
        + 0.20 * (study_hours_per_week * (100 / 40))  # scale hours to a 0-100 range contribution
        + 0.25 * previous_exam_score
        + 0.15 * assignment_score
        + 0.15 * internal_assessment_score
        + 3.0 * extracurricular_activities
        + 3.0 * parental_support
        + 0.8 * (sleep_hours - 7)
        + noise
    )

    # Clip to realistic 0-100 bounds
    final_exam_score = np.clip(final_exam_score, 0, 100)

    def categorize(score):
        if score >= 75:
            return "High"
        elif score >= 50:
            return "Medium"
        else:
            return "Low"

    performance_category = np.array([categorize(s) for s in final_exam_score])
    at_risk = (final_exam_score < 50).astype(int)

    df = pd.DataFrame(
        {
            "student_id": student_id,
            "attendance_percentage": attendance_percentage.round(1),
            "study_hours_per_week": study_hours_per_week.round(1),
            "previous_exam_score": previous_exam_score.round(1),
            "assignment_score": assignment_score.round(1),
            "internal_assessment_score": internal_assessment_score.round(1),
            "extracurricular_activities": extracurricular_activities,
            "parental_support": parental_support,
            "sleep_hours": sleep_hours.round(1),
            "final_exam_score": final_exam_score.round(1),
            "performance_category": performance_category,
            "at_risk": at_risk,
        }
    )
    return df


if __name__ == "__main__":
    df = generate_dataset()
    out_path = "student_performance_dataset.csv"
    df.to_csv(out_path, index=False)
    print(f"Dataset generated: {out_path}  ({len(df)} rows)")
    print(df.head())
    print("\nClass balance (performance_category):")
    print(df["performance_category"].value_counts())
    print("\nAt-risk balance:")
    print(df["at_risk"].value_counts())
