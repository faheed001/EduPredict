# EduPredict 3.0 — Architecture

## High-level architecture

```text
Browser (HTML/CSS/JavaScript)
          |
          v
     Flask Application
     /      |       \
    /       |        \
 Auth   Business Logic   JSON APIs
  |          |             |
  v          v             v
SQLite     ML Pipeline   EduPredict Assistant
              |
     +--------+---------+
     |        |         |
 Regression Risk     Profiles/Anomaly
     |        |         |
     +--------+---------+
              |
          Analytics
```

## Prediction flow

```text
Student/performance inputs
        -> validation
        -> feature vector
        -> trained regression ensemble
        -> predicted performance score
        -> risk classifier / threshold
        -> explanations and recommendations
        -> dashboard/history/intervention
```

## ML components

- RandomForestRegressor and GradientBoostingRegressor are combined using validation-selected weights for the performance score.
- RandomForestClassifier produces an early-warning risk probability.
- K-Means assigns learning-profile clusters.
- IsolationForest identifies unusual patterns.
- Feature importance is surfaced to support explainability.

## Data layer

SQLite stores application users, student profiles, performance records, predictions, intervention records and audit information. The bundled CSV is synthetic demo data and is imported into the live application tables when appropriate.

## Assistant

`/assistant` provides the UI. `POST /api/assistant` accepts user questions and returns answers from the integrated local EduPredict Assistant. It is designed to explain system features, educational/technical concepts and student-specific information available to the logged-in user.
