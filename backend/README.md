# AquaSentinel+ Backend API

AI-Powered Smart Water Quality Monitoring and Decision-Support System for Coastal Aquaculture Farms.

## Architecture
- **Framework**: Python FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **Machine Learning**: Scikit-Learn, XGBoost, SMOTE (imbalanced-learn)
- **Model Evaluation**: 5-Fold Stratified Cross-Validation
- **Models Trained**: Random Forest, XGBoost, SVM, KNN, Decision Tree

## Setup & Execution
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Train ML Models:
   ```bash
   python -m backend.model_training
   ```
3. Run FastAPI Server:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

## REST API Endpoints
- `POST /api/predict` - Run real-time prediction, Pollution Index calculation, and anomaly detection.
- `GET /api/species` - Get species safe parameters configuration (Shrimp, Tilapia, Carp).
- `POST /api/simulate/start` - Initialize live dataset simulation.
- `GET /api/simulate/latest` - Get latest simulated live reading.
- `GET /api/alerts` - Fetch recent moderate and critical alerts.
- `GET /api/model/metrics` - Return genuine ML model performance evaluation metrics.
- `GET /api/history` - Retrieve prediction history.
- `GET /api/report` - Export water quality data as CSV.
