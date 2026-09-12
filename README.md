# ⚡ EduPredict Pro 3.0
### Enterprise AI Student Retention & Early-Warning Decision Support Platform

[![Python](https://img.shields.io/badge/Python-3.14%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.1-emerald.svg)](https://palletsprojects.com/p/flask/)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn%201.8-orange.svg)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20(WAL%20Mode)-cyan.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-8%2F8%20Passing%20(100%25)-brightgreen.svg)]()
[![Status](https://img.shields.io/badge/Status-Production%20%2F%20Viva%20Ready-purple.svg)]()

---

## 📖 Executive Summary

**EduPredict Pro 3.0** is an enterprise-grade Educational Decision Support System (EDSS) engineered for higher-education institutions. Moving away from retrospective end-of-term grading, EduPredict deploys a **calibrated machine learning ensemble**, **cost-sensitive retention policies**, and **transparent local feature attribution** to detect vulnerable students weeks before critical exam failure and dropout cliffs occur.

The platform is designed around the empirical **Pedagogical Intervention Loop** (grounded in *Vincent Tinto’s Student Integration Model* and *Alexander Astin’s Student Involvement Theory*), providing specialized, role-adaptive workflows for both learners and academic advisors.

> 🏛️ **Academic / Ethical Data Governance Notice:** Included with the system is an empirical, synthetic dataset of **1,500 realistic, multicultural student records** with zero placeholder text. Model predictions operate strictly as decision-support signals designed to empower faculty interventions rather than automate punitive academic outcomes.

---

## 🏆 Key Machine Learning Benchmarks

All models were evaluated under an immutable, stratified 60/20/20 split (900 train, 300 validation, 300 holdout test) using `python tools/audit_project.py`:

| Core Capability | Algorithm / Methodology | Empirical Result | Academic Benchmark / Significance |
| :--- | :--- | :---: | :--- |
| **Early-Warning Risk Classification** | Calibrated Random Forest Ensemble | **99.4% ROC-AUC** | Outstanding ranking separation across all decision thresholds |
| **At-Risk Detection Sensitivity** | Cost-Sensitive Neyman-Pearson ($\tau = 0.15$) | **96.8% Recall** | Catches 61 out of 63 struggling students; minimizes false negatives |
| **Classification Quality ($F_1$)** | Calibrated Probability Mapping | **0.953 $F_1$ Score** | Solves early-warning class imbalance trade-offs ($93.8\%$ precision) |
| **Performance Score Regression** | Weighted Ensemble (RF 55% + GBDT 45%) | **0.978 $R^2$** | Captures non-linear study returns and attendance cliff effects |
| **Regression Prediction Error** | Huber Loss Tuning | **2.164 MAE** | Within $\pm 2.16$ points on a 100-point academic scale |
| **Behavioral Learner Archetypes** | Unsupervised K-Means Clustering | **0.594 Silhouette ($K=2$)** | Mathematically validates distinct behavioral archetypes |
| **Anomaly & Outlier Screening** | Isolation Forest ($c = 0.05$) | **Zero Anomaly Drift** | Automatically flags irregular engagement or score patterns |

---

## 🌟 What Makes EduPredict Pro 3.0 Unique?

### 1. ⚡ High-Throughput Sub-100ms What-If Simulator ($50\times$ Faster)
* **Zero-Allocation Vectorized Matrix Ingestion:** Replaced iterative Python prediction loops with batched NumPy array transforms ($8 \times 8$ local attribution matrix and $5 \times 8$ scenario simulation matrix).
* **Single-Threaded C Traversal (`n_jobs=1`):** Eliminated Windows multiprocessing worker-pool overhead for single-row inference.
* **Frontend Concurrency Safeguards:** Features a debounced 40ms slider pipeline with native `AbortController` cancellation, guaranteeing fluid 60 FPS slider movement without network queue clogging.

### 2. 🤖 Role-Adaptive Intelligent AI Assistant (`assistant_engine.py`)
* **Role-Specific Intelligence:**
  * **For Students:** Analyzes current scorecards, compares against the cohort mean ($68.4$), calculates distance to the $75\%$ attendance penalty cliff, and generates a personalized 14-day spaced repetition recovery timetable.
  * **For Instructors:** Instantly synthesizes cohort health briefings, outputs formatted tables of critical at-risk students, detects systemic bottlenecks, and drafts pedagogical counseling templates.
* **Comprehensive Knowledge Base:** Over 40 curated topics spanning Scikit-Learn architectures, Tinto/Astin retention theory, Neyman-Pearson loss matrices, and security protocols.
* **Modern UI:** Streaming Markdown parser, table generator, animated typing bubble, and dynamic context suggestion chips.

### 3. 🎨 Creative Prismatic Cyber-Aurora Theme & Living Visuals
* **Creative Dual-Mode System:**
  * **Light Theme ("Luminous Prismatic Canvas"):** Electric Iris (`#6366f1`), Neon Cyan (`#06b6d4`), and Synthwave Fuchsia (`#d946ef`) across a crisp slate glassmorphic surface.
  * **Dark Theme ("Deep Cosmic Obsidian Abyss"):** Deep space obsidian canvas (`#070913`) paired with high-contrast glowing neon azure (`#818cf8`) and orchid accents (`#f472b6`).
* **Living Neural Constellation Canvas:** High-DPI HTML5 canvas simulating an interactive 4-color synapse particle web with cursor-magnetic physics and `IntersectionObserver` battery throttling.
* **Interactive Radial Theme Shockwave:** Native View Transitions API with an expanding multi-color supernova wavefront ring radiating from the toggle switch.
* **Platform-Wide Telemetry Tickers:** Synchronized real-time telemetry streams (`.live-stream-bar`) across all platform dashboards.

### 4. 🔒 Enterprise Security & Data Governance
* **FERPA / GDPR Least Privilege Model:** Restricts private behavioral scores strictly to students and their verified instructors.
* **Cryptographic Security:** PBKDF2-SHA256 password hashing, persistent 256-bit secret keys, SameSite/HttpOnly session cookies, and strict per-session CSRF token verification.
* **Immutable Audit Trail:** Dedicated SQLite `audit_log` tracking logins, predictions, and instructor intervention notes.

---

## 👥 Demo User Accounts

| Role | Username | Password | Access Rights & Experience |
| :--- | :--- | :--- | :--- |
| **Instructor / Advisor** | `teacher` | `teacher123` | Cohort Heatmap, Search 1,500 Roster, Add Students, Log Interventions, Export CSV |
| **Student** | `student` | `student123` | Personal Scorecard, What-If Simulator, 14-Day Study Plan, Advisor Intervention Notes |

---

## 🚀 Quickstart Installation Guide

### Prerequisites
* Python 3.10 to 3.14
* Git

### Step-by-Step Setup

```powershell
# 1. Clone the repository
git clone https://github.com/faheed001/EduPredict.git
cd EduPredict

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Linux/macOS: source .venv/bin/activate

# 3. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. (Optional) Re-train models or verify dataset
python model\train_model.py

# 5. Run the comprehensive project audit
python tools\audit_project.py

# 6. Launch the development server
python app.py
```

Open your browser to **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.

---

## 🧪 Automated Testing

Execute the full automated test suite verifying security headers, role enforcement, CSRF protection, What-If simulations, and assistant API contracts:

```powershell
python -m pytest tests/ -v
```

Expected Output:
```text
tests/test_app_functional.py::test_public_health_and_security_headers PASSED [ 12%]
tests/test_app_functional.py::test_role_protection_and_prediction_flow PASSED [ 25%]
tests/test_app_functional.py::test_student_api_requires_csrf PASSED      [ 37%]
tests/test_app_functional.py::test_what_if_api_simulation PASSED         [ 50%]
tests/test_app_functional.py::test_assistant_api_student_and_teacher PASSED [ 62%]
tests/test_contracts.py::test_python_syntax PASSED                       [ 75%]
tests/test_contracts.py::test_metrics_contract PASSED                    [ 87%]
tests/test_contracts.py::test_schema_contract PASSED                     [100%]

============================== 8 passed in 6.50s ==============================
```

---

## 📁 Repository Structure

```text
EduPredict/
├── app.py                      # Flask backend, routing, auth, SQLite integration
├── assistant_engine.py         # Role-adaptive educational AI assistant engine
├── requirements.txt            # Production dependencies (Flask, Scikit-Learn, Pandas)
├── PRESENTATION_95_READY.md    # 5-minute defense demo script & 15 tough judge Q&As
├── JUDGE_VIVA_PREP.md          # Comprehensive viva reference & pedagogical frameworks
├── MODEL_CARD_3.0.md           # Formal ML model card and bias/fairness specifications
│
├── data/
│   ├── generate_dataset.py     # 1,500-sample synthetic dataset generator with 1,500 unique names
│   ├── student_performance_dataset.csv # Golden empirical dataset
│   └── edupredict.db           # SQLite database (WAL mode, 7 relational tables)
│
├── model/
│   ├── train_model.py          # Training pipeline: regression, classification, clustering, XAI
│   ├── artifacts.joblib        # Serialized production pipeline models
│   └── metrics.json            # Stratified holdout evaluation metrics
│
├── static/
│   ├── css/
│   │   └── style.css           # Creative Prismatic Cyber-Aurora design system (2,300+ lines)
│   └── js/
│       └── app.js              # Neural constellation canvas, What-If simulator, chart engine
│
├── templates/
│   ├── base.html               # Master layout with View Transitions theme slider & live telemetry
│   ├── index.html              # Hero section, interactive canvas, live stream bar, feature pillars
│   ├── dashboard.html          # ML analytics dashboard, ROC curve, feature importance, confusion matrix
│   ├── predict.html            # Real-time What-If sensitivity studio with speedometer gauge
│   ├── assistant.html          # Intelligent role-adaptive AI chat assistant
│   ├── teacher_dashboard.html  # Instructor command center, cohort search, risk filters, interventions
│   ├── teacher_student.html    # Detailed longitudinal student record & intervention form
│   ├── student_dashboard.html  # Student success overview, score breakdown, study timetable
│   ├── student_update.html     # Self-reported score submission portal
│   ├── student_profile.html    # Student account & profile settings
│   ├── login.html              # Secure session authentication
│   └── register.html           # New student account registration
│
├── tests/
│   ├── test_app_functional.py  # Security, CSRF, role protection, and API simulation tests
│   └── test_contracts.py       # Syntax, schema, and metrics contract verification
│
├── tools/
│   ├── audit_project.py        # Independent verification script testing accuracy and metrics
│   └── update_student_names.py # Migration utility for realistic student names
│
└── docs/
    ├── API.md                  # Complete REST API specification
    ├── ARCHITECTURE.md         # System components & data flow diagrams
    ├── DATA_DICTIONARY.md      # Feature definitions, scaling, and value ranges
    ├── DEVELOPER_GUIDE.md      # Code style, contribution, and database schemas
    ├── MODEL_CARD.md           # Model specifications, intended use, and limitations
    ├── USER_GUIDE.md           # End-user workflow walkthroughs
    └── VIVA_QUESTIONS.md       # Extended viva preparation & technical answers
```

---

## 📚 Complete Documentation Index

For in-depth project evaluation and viva presentation prep:
* **[PRESENTATION_95_READY.md](PRESENTATION_95_READY.md):** Rapid 5-minute judge demo script, 15 hard questions & answers, mathematical derivations.
* **[JUDGE_VIVA_PREP.md](JUDGE_VIVA_PREP.md):** Theoretical retention frameworks, Neyman-Pearson optimization, and cost-benefit trade-offs.
* **[MODEL_CARD_3.0.md](MODEL_CARD_3.0.md):** Formal ML model card including calibration plots, fairness metrics, and data sheets.
* **[docs/API.md](docs/API.md):** Full documentation for `/api/predict`, `/api/what-if`, `/api/assistant`, and export endpoints.

---

## 📜 License & Citation

Distributed under the MIT License. Developed for educational research, student retention advocacy, and academic analytics demonstration.
