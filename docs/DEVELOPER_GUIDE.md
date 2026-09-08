# EduPredict 3.0 — Developer Guide

## Requirements

- Windows 10/11 or compatible OS.
- Python 3.14.
- pip.
- Git (recommended).
- Modern web browser.

## Setup

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Train the model

```powershell
python model\train_model.py
```

## Audit

```powershell
python tools\audit_project.py
```

## Tests

```powershell
python -m pytest -q
```

## Run

```powershell
python app.py
```

Open `http://127.0.0.1:5000`.

## Configuration

Use `.env.example` as a reference. For deployments, set a strong `EDUPREDICT_SECRET` and do not commit `.env`.
