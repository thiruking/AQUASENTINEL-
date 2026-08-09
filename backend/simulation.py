from datetime import datetime
from sqlalchemy.orm import Session
from .data_loader import generate_or_load_awd_dataset
from .models import Reading, PredictionRecord, AlertRecord, SimulationStateRecord
from .pollution_index import calculate_pollution_index, validate_and_reconcile_status
from .anomaly_detector import anomaly_detector_instance
from .classifier import classifier_instance
from .recommendations import generate_recommendations

class SimulationEngine:
    def __init__(self):
        self.df = None
        self._load_data()

    def _load_data(self):
        self.df = generate_or_load_awd_dataset()

    def get_state(self, db: Session) -> SimulationStateRecord:
        state = db.query(SimulationStateRecord).first()
        if not state:
            state = SimulationStateRecord(is_running=False, current_index=0)
            db.add(state)
            db.commit()
            db.refresh(state)
        return state

    def start(self, db: Session) -> SimulationStateRecord:
        state = self.get_state(db)
        state.is_running = True
        state.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(state)
        return state

    def step_multi_ponds(self, db: Session) -> list[dict]:
        """
        Multi-Pond Simulation:
        Simulates 3 ponds simultaneously:
          Pond A - Shrimp (P. vannamei)
          Pond B - Tilapia (O. niloticus)
          Pond C - Carp (C. carpio)
        """
        state = self.get_state(db)
        if self.df is None or len(self.df) == 0:
            self._load_data()

        ponds_config = [
            {"pond_id": "Pond A", "species": "Shrimp", "offset": 0},
            {"pond_id": "Pond B", "species": "Tilapia", "offset": 10},
            {"pond_id": "Pond C", "species": "Carp", "offset": 25}
        ]

        results = []

        for p_cfg in ponds_config:
            pond_id = p_cfg["pond_id"]
            species = p_cfg["species"]
            idx = (state.current_index + p_cfg["offset"]) % len(self.df)
            row = self.df.iloc[idx].to_dict()

            reading = Reading(
                species=species,
                temperature=float(row.get("temperature", 28.5)),
                turbidity=float(row.get("turbidity", 35.0)),
                dissolved_oxygen=float(row.get("dissolved_oxygen", 6.5)),
                bod=float(row.get("bod", 4.0)),
                co2=float(row.get("co2", 5.0)),
                ph=float(row.get("ph", 7.8)),
                alkalinity=float(row.get("alkalinity", 120.0)),
                hardness=float(row.get("hardness", 150.0)),
                calcium=float(row.get("calcium", 60.0)),
                ammonia=float(row.get("ammonia", 0.02)),
                nitrite=float(row.get("nitrite", 0.05)),
                phosphorus=float(row.get("phosphorus", 0.1)),
                h2s=float(row.get("h2s", 0.002)),
                plankton=float(row.get("plankton", 45000.0)),
                nitrate=float(row.get("nitrate", 5.0)),
                salinity=float(row.get("salinity", 15.0)),
                is_simulated=True
            )
            db.add(reading)
            db.commit()
            db.refresh(reading)

            reading_dict = {c.name: getattr(reading, c.name) for c in reading.__table__.columns}
            ml_pred, raw_conf, shap_scores = classifier_instance.predict(reading_dict)
            pi_score, contributions = calculate_pollution_index(reading_dict, species)

            final_class, conf = validate_and_reconcile_status(pi_score, ml_pred, raw_conf)

            features = [
                reading.ph, reading.temperature, reading.turbidity,
                reading.dissolved_oxygen, reading.ammonia, reading.bod, reading.salinity
            ]
            is_anomaly, anomaly_score = anomaly_detector_instance.detect(features)

            recs = generate_recommendations(reading_dict, species, final_class, contributions)

            explanation = (
                f"{pond_id} ({species}): AquaSentinel+ AI classified water status as '{final_class}' "
                f"with Pollution Index {pi_score}/100 and {int(conf*100)}% model confidence."
            )

            db_pred = PredictionRecord(
                reading_id=reading.id,
                species=species,
                ml_prediction=ml_pred,
                pollution_index=pi_score,
                anomaly_flag=is_anomaly,
                anomaly_score=anomaly_score,
                trend_flag=False,
                final_classification=final_class,
                explanation=explanation,
                recommendations_json=str(recs)
            )
            db.add(db_pred)

            # CLEAN HUMAN READABLE ALERT FORMATTING (FIXES BUG 3)
            if final_class in ["MODERATE", "CRITICAL"]:
                trig_param = "Ammonia" if reading.ammonia > 0.05 else ("DO" if reading.dissolved_oxygen < 5.0 else "pH")
                trig_val = round(reading.ammonia if trig_param == "Ammonia" else (reading.dissolved_oxygen if trig_param == "DO" else reading.ph), 2)
                limit_val = "0.05 ppm" if trig_param == "Ammonia" else ("5.0 mg/L" if trig_param == "DO" else "7.5 - 8.5")
                reason_phrase = f"{trig_param} reached {trig_val} (safe limit: {limit_val}), elevating Pollution Index to {pi_score}."

                alert = AlertRecord(
                    species=species,
                    severity=final_class,
                    parameter=f"{pond_id} - {species} | {trig_param} {trig_val} (limit {limit_val})",
                    value=float(trig_val),
                    reason=reason_phrase
                )
                db.add(alert)

            results.append({
                "pond_id": pond_id,
                "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
                "species": species,
                "ml_prediction": ml_pred,
                "pollution_index": pi_score,
                "anomaly_flag": is_anomaly,
                "anomaly_score": round(anomaly_score, 2),
                "final_classification": final_class,
                "confidence": conf,
                "explanation": explanation,
                "parameter_contributions": contributions,
                "feature_importances": shap_scores,
                "recommendations": recs,
                "readings": {
                    "ph": round(reading.ph, 2),
                    "dissolved_oxygen": round(reading.dissolved_oxygen, 2),
                    "ammonia": round(reading.ammonia, 3),
                    "temperature": round(reading.temperature, 1),
                    "turbidity": round(reading.turbidity, 1)
                }
            })

        state.current_index = (state.current_index + 1) % len(self.df)
        state.last_updated = datetime.utcnow()
        db.commit()

        return results

simulation_engine_instance = SimulationEngine()
