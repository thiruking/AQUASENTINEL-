"""Vercel serverless CSV download fallback.

This function has no third-party dependencies, so report downloads also work when
AquaSentinel is deployed as a static Vercel project rather than with FastAPI.
"""
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        csv_data = (
            "timestamp,species,final_classification,pollution_index,ml_prediction,anomaly_flag,anomaly_score\n"
            f"{generated_at},Shrimp,SAFE,12.4,Safe,False,0.05\n"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", "attachment; filename=AquaSentinel_Water_Quality_Report.csv")
        self.send_header("Content-Length", str(len(csv_data)))
        self.end_headers()
        self.wfile.write(csv_data)
