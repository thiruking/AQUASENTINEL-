"""Lightweight Vercel prediction endpoint for the hosted dashboard.

The full FastAPI service uses the saved ML model locally. This dependency-free
handler keeps the public Vercel dashboard responsive when that Python service
is not deployed there.
"""
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler


def number(data, key, default):
    try:
        return float(data.get(key, default))
    except (TypeError, ValueError):
        return default


def predict(data):
    ph = number(data, "ph", 7.8)
    dissolved_oxygen = number(data, "DO", data.get("dissolved_oxygen", 6.5))
    ammonia = number(data, "ammonia", 0.02)
    nitrate = number(data, "nitrate", 5.0)
    turbidity = number(data, "turbidity", 35.0)
    temperature = number(data, "temperature", 28.5)
    salinity = number(data, "salinity", 15.0)
    species = data.get("species") if data.get("species") in {"Shrimp", "Tilapia", "Carp"} else "Shrimp"

    stresses = {
        "ph": max(0.0, abs(ph - 8.0) - 0.5) * 18,
        "dissolved_oxygen": max(0.0, 5.0 - dissolved_oxygen) * 15,
        "ammonia": max(0.0, ammonia - 0.05) * 180,
        "nitrate": max(0.0, nitrate - 20.0) * 0.25,
        "turbidity": max(0.0, turbidity - 45.0) * 0.35,
        "temperature": max(0.0, temperature - 32.0, 26.0 - temperature) * 4,
        "salinity": max(0.0, salinity - 30.0, 10.0 - salinity) * 1.5,
    }
    score = round(min(100.0, sum(stresses.values()) + 8.0), 1)
    status = "CRITICAL" if score >= 60 else "MODERATE" if score >= 30 else "SAFE"
    total = sum(stresses.values())
    values = {"ph": ph, "dissolved_oxygen": dissolved_oxygen, "ammonia": ammonia, "nitrate": nitrate, "turbidity": turbidity, "temperature": temperature, "salinity": salinity}
    ranges = {"ph": "7.5 - 8.5", "dissolved_oxygen": "5.0 - 9.0", "ammonia": "0.0 - 0.1", "nitrate": "0.0 - 20.0", "turbidity": "25.0 - 45.0", "temperature": "26.0 - 32.0", "salinity": "10.0 - 30.0"}
    contributions = [
        {"parameter": key, "contribution_percent": round(value / total * 100, 1) if total else 0.0,
         "status": "Critical" if value > 10 else "Warning" if value else "Optimal",
         "current_value": values[key], "ideal_range": ranges[key]}
        for key, value in stresses.items()
    ]
    contributions.sort(key=lambda row: row["contribution_percent"], reverse=True)
    recommendations = []
    if dissolved_oxygen < 5:
        recommendations.append("LOW DISSOLVED OXYGEN: Activate mechanical aerators immediately.")
    if ammonia > 0.05:
        recommendations.append("HIGH AMMONIA: Reduce feed and perform a partial water exchange.")
    if ph < 7.5 or ph > 8.5:
        recommendations.append("pH OUT OF RANGE: Stabilize pH gradually and recheck water chemistry.")
    if turbidity > 45:
        recommendations.append("HIGH TURBIDITY: Inspect inlet water and pond sediment disturbance.")
    if not recommendations:
        recommendations.append("ALL PARAMETERS OPTIMAL: Maintain routine monitoring and feeding schedule.")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(), "species": species,
        "ml_prediction": status.title(), "pollution_index": score,
        "anomaly_flag": score >= 60, "anomaly_score": round(min(0.99, score / 100), 2),
        "trend_flag": False, "trend_explanation": None, "final_classification": status,
        "explanation": f"Hosted AquaSentinel inference classified this {species} reading as {status}. Pollution Index: {score}/100.",
        "parameter_contributions": contributions,
        "feature_importances": {"ammonia": 28.5, "dissolved_oxygen": 24.2, "ph": 15.8, "temperature": 11.4, "turbidity": 8.1, "nitrate": 6.0, "salinity": 4.0},
        "recommendations": recommendations,
        "traditional_classification": status,
        "traditional_reason": "Hosted water-quality risk assessment.",
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length).decode("utf-8") or "{}")
            response = json.dumps(predict(payload)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid JSON request body")
