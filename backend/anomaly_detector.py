import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

class AnomalyDetector:
    def __init__(self):
        self.model = None
        self._load_or_train()

    def _load_or_train(self):
        model_path = os.path.join(ARTIFACTS_DIR, "isolation_forest.joblib")
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                return
            except Exception:
                pass

        # Train baseline Isolation Forest model
        np.random.seed(42)
        normal_data = np.random.normal(loc=[7.8, 28.0, 30.0, 6.5, 0.02, 3.5, 15.0], scale=[0.3, 1.2, 5.0, 0.8, 0.01, 0.8, 3.0], size=(1000, 7))
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.model.fit(normal_data)

        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        joblib.dump(self.model, model_path)

    def detect(self, feature_vector: list[float]) -> tuple[bool, float]:
        if not self.model or len(feature_vector) < 7:
            return False, 0.05

        vec = np.array(feature_vector[:7]).reshape(1, -1)
        pred = self.model.predict(vec)[0]  # 1: normal, -1: anomaly
        score = float(-self.model.score_samples(vec)[0]) # higher score = more anomalous

        is_anomaly = bool(pred == -1)
        return is_anomaly, round(score, 3)

anomaly_detector_instance = AnomalyDetector()
