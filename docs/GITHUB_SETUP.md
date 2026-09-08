# GitHub Setup Guide

## Create repository
Recommended repository name:

`EduPredict-3.0`

Suggested description:

`AI-based student performance prediction, early-warning analytics, personalized recommendations, and educational assistance using Flask and machine learning.`

## First commit

```powershell
git init
git add .
git status
git commit -m "Initial EduPredict 3.0 release"
```

Then create an empty GitHub repository and connect it to your remote:

```powershell
git branch -M main
git remote add origin <YOUR_GITHUB_REPOSITORY_URL>
git push -u origin main
```

## Suggested topics

`python`, `flask`, `machine-learning`, `scikit-learn`, `student-performance`, `education`, `educational-technology`, `data-science`, `artificial-intelligence`, `sqlite`, `predictive-analytics`, `student-analytics`

## Before pushing
- Verify `.env` is absent.
- Verify no real student data is included.
- Verify `.venv` is ignored.
- Verify the README says the dataset is synthetic.
- Run tests and the project audit.
