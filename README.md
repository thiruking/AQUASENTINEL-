# AquaSentinel+ | AI-Powered Smart Water Quality Monitoring System (v1.3.0)

**AquaSentinel+** is an end-to-end AI-powered smart water quality monitoring and decision-support system designed for coastal aquaculture farms (*Shrimp*, *Tilapia*, *Carp*).

---

## 🌟 New Features in Version 1.3.0

### 1. New Page: "Pond Health Guide" (`/guide` or `guide.html`)
A dedicated, plain-language handbook built for non-technical farmers:
- **Parameter Glossary**: Cards for pH, DO, Ammonia, Nitrate, Turbidity, Temp, Salinity with plain analogies (*"DO is like air for fish — too little and they suffocate"*).
- **Thermometer Gauge Bars**: Visual indicators comparing current readings against species-specific ideal green zones.
- **"Will My Fish Survive?" Verdict Widget**: Single-sentence farmer verdict with high-contrast status icons (🟢 Safe, 🟡 Moderate, 🔴 Critical) and a plain-language action box (*"Turn on the aerator immediately"*).
- **Species Survival Reference Table**: Quick reference table for Shrimp, Tilapia, and Carp.

### 2. Beginner-Friendly UX Mode
- **Simple Mode / Advanced Mode Header Toggle**:
  - *Simple Mode*: Hides technical panels (SHAP, ML leaderboard, architecture). Displays top summary status banner, Pollution Index card, farmer verdict, multi-pond stream, recommendations, and sliders.
  - *Advanced Mode*: Full technical AI engine dashboard.
- **Hover Tooltips (`?`)**: Interactive tooltips explaining technical terms (Pollution Index, Anomaly Detection, F1 Score, SHAP, etc.).
- **First-Time User Guided Tour**: Interactive step-by-step onboarding walkthrough overlay.
- **Persistent Floating Help Button & FAQ Accordion**: Fixed `? Help` button opening quick farmer FAQ accordion.
- **Always-Visible Top Status Summary Banner**: Sticky top banner displaying instant farm status (`🟢 All 3 Ponds Healthy`).

### 3. User Authentication & Per-User Pond Management System
- **JWT-Based Authentication**: `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`.
- **Seeded Evaluator Demo Admin Credentials**:
  - **Email**: `admin@aquasentinel.demo` (or `admin`)
  - **Password**: `demo1234` (or `aquasentinel123`)
- **Per-User Pond Ownership**: `User` & `Pond` database tables allowing farmers to register & manage custom ponds.
- **Header Avatar & User Menu**: Profile badge, My Ponds, "+ Add New Pond" modal, and Logout.

---

## 🛠️ Critical Bug Fixes & Technical Refinements

### 1. Data Leakage & Realistic Model Accuracy Fix
- **Dataset Deduplication**: `df.drop_duplicates()` applied prior to split.
- **Train-Fold Preprocessing Isolation**: `StandardScaler` and `SMOTE` fit strictly on `X_train`.
- **Pure Input Features**: Raw 16 physical parameters ONLY (Pollution Index and labels excluded).
- **Realistic 5-Fold Stratified Cross Validation Benchmark**:
  - **SVM Classifier (Best Model)**: **91.98% Accuracy** | 0.9197 F1-Score
  - **Random Forest**: **91.86% Accuracy** | 0.9181 F1-Score
  - **XGBoost**: **91.86% Accuracy** | 0.9181 F1-Score
  - **K-Nearest Neighbors (KNN)**: **91.51% Accuracy** | 0.9149 F1-Score
  - **Decision Tree**: **90.23% Accuracy** | 0.8983 F1-Score

### 2. Pollution Index Score Convention & Consistency Reconciler
- **Strict 0–100 Score Convention**: `0.0` = **OPTIMAL / SAFE**, `100.0` = **CRITICAL RISK**.
- **Consistency Validator**: `validate_and_reconcile_status()` forces Pollution Index score, ML model confidence %, and Safe/Moderate/Critical badges to stay 100% aligned.

---

## ⚡ Quick Run Instructions

### 1. Install dependencies
```bash
python -m pip install -r backend/requirements.txt pytest
```

### 2. Run the test suite
```bash
python -m pytest backend/tests/test_aquasentinel.py
```

### 3. Run AquaSentinel+
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000` for the dashboard and
`http://localhost:8000/guide.html` for the Pond Health Guide.

The FastAPI server now serves the dashboard and API from the same origin, so
predictions, authentication, reports, and live telemetry work without a
separate static server or browser-side `localhost` API configuration.

## Vercel report downloads

The repository includes dependency-free Vercel serverless download handlers at
`/api/report` and `/api/report-pdf`. They make CSV and PDF report downloads work
on a Vercel static deployment as well as during a local FastAPI run. For live
predictions, authentication, and database-backed telemetry on a public site,
deploy the FastAPI service to a Python-capable backend and keep the dashboard
and API on the same origin (or configure a reverse proxy).

---

## 📌 Demo Credentials for Evaluators
- **Admin Email**: `admin@aquasentinel.demo`
- **Password**: `demo1234`

## Public API deployment (Render + Vercel)

1. In Render, create a **Blueprint** from this repository. Render reads
   `render.yaml` and deploys the FastAPI service. Copy its public URL, for
   example `https://aquasentinel-api.onrender.com`.
2. In Vercel project settings, add the production environment variable
   `AQUASENTINEL_API_URL` with that URL (**without** `/api` at the end).
3. Redeploy Vercel. Its build writes the public value into `runtime-config.js`.
   The dashboard then sends predictions, trends, alerts, authentication, CSV,
   and PDF downloads to the public FastAPI API instead of `localhost`.

The FastAPI CORS middleware permits the Vercel frontend origin. Do not put
secrets in `AQUASENTINEL_API_URL`; it is intentionally a browser-visible URL.
