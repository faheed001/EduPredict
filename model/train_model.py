"""
Advanced model training for EduPredict.

Models:
1. RandomForestRegressor + GradientBoostingRegressor ensemble -> final score
2. RandomForestClassifier -> at-risk early warning
3. KMeans -> student learning-profile clustering
4. IsolationForest -> unusual/anomalous student pattern detection

All artifacts and metrics are saved for the Flask application.
"""
import json, os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingRegressor, IsolationForest
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import precision_recall_curve, roc_auc_score, precision_score, recall_score, confusion_matrix, mean_squared_error, roc_curve
from sklearn.cluster import KMeans
from sklearn.metrics import (
    accuracy_score, classification_report, f1_score,
    mean_absolute_error, r2_score, silhouette_score
)
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "student_performance_dataset.csv")
ARTIFACT_PATH = os.path.join(BASE_DIR, "model", "artifacts.joblib")
METRICS_PATH = os.path.join(BASE_DIR, "model", "metrics.json")

FEATURE_COLUMNS = [
    "attendance_percentage", "study_hours_per_week",
    "previous_exam_score", "assignment_score",
    "internal_assessment_score", "extracurricular_activities",
    "parental_support", "sleep_hours",
]

def train():
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLUMNS]
    y_reg, y_clf = df["final_exam_score"], df["at_risk"]

    X_trainval, X_test, y_reg_trainval, y_reg_test, y_clf_trainval, y_clf_test = train_test_split(
        X, y_reg, y_clf, test_size=0.20, random_state=42, stratify=y_clf
    )
    X_train, X_val, y_reg_train, y_reg_val, y_clf_train, y_clf_val = train_test_split(
        X_trainval, y_reg_trainval, y_clf_trainval, test_size=0.25, random_state=43, stratify=y_clf_trainval
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    rf_reg = RandomForestRegressor(
        n_estimators=350, max_depth=10, min_samples_leaf=2, random_state=42
    )
    gb_reg = GradientBoostingRegressor(
        n_estimators=250, learning_rate=0.04, max_depth=3, loss="huber", random_state=42
    )
    rf_reg.fit(X_train_scaled, y_reg_train)
    gb_reg.fit(X_train_scaled, y_reg_train)

    # Model comparison is calculated on the validation set only, so the final test set
    # remains untouched until the final reported metrics below.
    rf_val_pred = rf_reg.predict(X_val_scaled)
    gb_val_pred = gb_reg.predict(X_val_scaled)
    # Tune the ensemble weight on validation data only. This avoids hand-picking
    # weights while keeping the final test set untouched.
    weight_candidates = np.linspace(0.0, 1.0, 101)
    best_weight = min(weight_candidates, key=lambda w: mean_absolute_error(y_reg_val, w * rf_val_pred + (1.0 - w) * gb_val_pred))
    ensemble_val_pred = best_weight * rf_val_pred + (1.0 - best_weight) * gb_val_pred
    model_comparison = {
        "Random Forest": {"mae": round(float(mean_absolute_error(y_reg_val, rf_val_pred)), 3), "r2": round(float(r2_score(y_reg_val, rf_val_pred)), 3)},
        "Gradient Boosting": {"mae": round(float(mean_absolute_error(y_reg_val, gb_val_pred)), 3), "r2": round(float(r2_score(y_reg_val, gb_val_pred)), 3)},
        "Ensemble": {"mae": round(float(mean_absolute_error(y_reg_val, ensemble_val_pred)), 3), "r2": round(float(r2_score(y_reg_val, ensemble_val_pred)), 3), "rf_weight": round(float(best_weight), 2), "gb_weight": round(float(1.0 - best_weight), 2)}
    }

    rf_pred = rf_reg.predict(X_test_scaled)
    gb_pred = gb_reg.predict(X_test_scaled)
    ensemble_pred = best_weight * rf_pred + (1.0 - best_weight) * gb_pred

    reg_mae = mean_absolute_error(y_reg_test, ensemble_pred)
    reg_r2 = r2_score(y_reg_test, ensemble_pred)

    base_classifier = RandomForestClassifier(
        n_estimators=350, max_depth=8, min_samples_leaf=2,
        class_weight="balanced", random_state=42
    )
    classifier = CalibratedClassifierCV(base_classifier, method="sigmoid", cv=5)
    classifier.fit(X_train_scaled, y_clf_train)
    base_classifier.fit(X_train_scaled, y_clf_train)
    val_prob = classifier.predict_proba(X_val_scaled)[:, 1]
    # Select the operating point on validation data only; the test set remains untouched.
    thresholds = np.linspace(0.20, 0.80, 121)
    threshold_scores = []
    for t in thresholds:
        pred = (val_prob >= t).astype(int)
        threshold_scores.append((f1_score(y_clf_val, pred), recall_score(y_clf_val, pred), float(t)))
    _, _, risk_threshold = max(threshold_scores, key=lambda x: (x[0], x[1], -abs(x[2]-0.40)))
    test_prob = classifier.predict_proba(X_test_scaled)[:, 1]
    y_clf_pred = (test_prob >= risk_threshold).astype(int)
    clf_accuracy = accuracy_score(y_clf_test, y_clf_pred)
    clf_precision = precision_score(y_clf_test, y_clf_pred, zero_division=0)
    clf_recall = recall_score(y_clf_test, y_clf_pred, zero_division=0)
    clf_f1 = f1_score(y_clf_test, y_clf_pred, zero_division=0)
    clf_auc = roc_auc_score(y_clf_test, test_prob)
    fpr, tpr, roc_thresholds = roc_curve(y_clf_test, test_prob)
    clf_report = classification_report(y_clf_test, y_clf_pred, output_dict=True, zero_division=0)
    clf_cm = confusion_matrix(y_clf_test, y_clf_pred).tolist()

    # Choose the best-supported exploratory profile count instead of hard-coding K=4.
    cluster_scaler = StandardScaler()
    X_cluster = cluster_scaler.fit_transform(X)
    cluster_candidates = {}
    for k in range(2, 7):
        km = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = km.fit_predict(X_cluster)
        cluster_candidates[k] = float(silhouette_score(X_cluster, labels))
    best_k = max(cluster_candidates, key=cluster_candidates.get)
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=20)
    clusters = kmeans.fit_predict(X_cluster)
    df_profile = df.copy(); df_profile["cluster"] = clusters
    cluster_means = df_profile.groupby("cluster")[FEATURE_COLUMNS].mean()
    overall = cluster_means[["attendance_percentage","study_hours_per_week","previous_exam_score","assignment_score","internal_assessment_score"]].mean(axis=1)
    ordered = list(overall.sort_values().index)
    name_sets = {
        2: ["Needs Support", "Higher Readiness"],
        3: ["Needs Support", "Developing", "Higher Readiness"],
        4: ["Needs Support", "Developing", "Consistent", "High Achiever"],
        5: ["Needs Support", "Developing", "Steady", "Strong", "High Achiever"],
        6: ["Needs Support", "Emerging", "Developing", "Steady", "Strong", "High Achiever"]
    }
    names = name_sets[best_k]
    profile_names = {int(cid): names[i] for i, cid in enumerate(ordered)}
    silhouette = cluster_candidates[best_k]

    anomaly_detector = IsolationForest(
        n_estimators=250, contamination=0.05, random_state=42
    )
    anomaly_detector.fit(X_cluster)

    reg_importance = (0.55 * rf_reg.feature_importances_ +
                      0.45 * gb_reg.feature_importances_)
    clf_importance = base_classifier.feature_importances_
    combined_importance = (reg_importance + clf_importance) / 2
    feature_importance = sorted(
        zip(FEATURE_COLUMNS, combined_importance.tolist()),
        key=lambda x: x[1], reverse=True
    )

    artifacts = {
        "rf_regressor": rf_reg, "gb_regressor": gb_reg, "ensemble_rf_weight": float(best_weight), "ensemble_gb_weight": float(1.0 - best_weight),
        "classifier": classifier, "scaler": scaler,
        "cluster_scaler": cluster_scaler, "kmeans": kmeans,
        "profile_names": profile_names, "anomaly_detector": anomaly_detector,
        "feature_columns": FEATURE_COLUMNS, "feature_importance": feature_importance,
        "risk_threshold": float(risk_threshold),
    }
    joblib.dump(artifacts, ARTIFACT_PATH)

    metrics = {
        "regression": {
            "mae": round(float(reg_mae), 3),
            "r2_score": round(float(reg_r2), 3),
            "model": "Validation-weighted Random Forest + Gradient Boosting Ensemble",
            "rf_weight": round(float(best_weight), 2),
            "gb_weight": round(float(1.0 - best_weight), 2)
        },
        "model_comparison": model_comparison,
        "classification": {
            "accuracy": round(float(clf_accuracy), 3),
            "precision": round(float(clf_precision), 3),
            "recall": round(float(clf_recall), 3),
            "f1_score": round(float(clf_f1), 3),
            "roc_auc": round(float(clf_auc), 3),
            "operating_threshold": round(float(risk_threshold), 3),
            "confusion_matrix": clf_cm,
            "report": clf_report,
            "roc_curve": {
                "fpr": [round(float(x), 4) for x in fpr],
                "tpr": [round(float(x), 4) for x in tpr]
            }
        },
        "clustering": {
            "clusters": int(best_k),
            "silhouette_score": round(float(silhouette), 3),
            "candidate_scores": {str(k): round(v, 3) for k, v in cluster_candidates.items()}
        },
        "feature_importance": [
            {"feature": f, "importance": round(float(v), 4)}
            for f, v in feature_importance
        ],
        "dataset_size": len(df), "train_size": len(X_train), "validation_size": len(X_val), "test_size": len(X_test),
        "validation_design": "60/20/20 train/validation/test split; threshold selected on validation only; final metrics reported on untouched test set"
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print("Advanced training complete.")
    print(f"Regression -> MAE {reg_mae:.2f}, R2 {reg_r2:.3f}")
    print(f"At-risk -> Accuracy {clf_accuracy:.3f}, Precision {clf_precision:.3f}, Recall {clf_recall:.3f}, F1 {clf_f1:.3f}, ROC-AUC {clf_auc:.3f}, threshold {risk_threshold:.3f}")
    print(f"Profiles -> Silhouette {silhouette:.3f}")
    return artifacts, metrics

if __name__ == "__main__":
    train()
