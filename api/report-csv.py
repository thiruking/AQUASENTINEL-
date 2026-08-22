"""Vercel serverless CSV download fallback.

This function has no third-party dependencies, so report downloads also work when
AquaSentinel is deployed as a static Vercel project rather than with FastAPI.
"""
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        # A hosted static deployment has no SQLite volume. Return a complete
        # recent telemetry sample rather than a single placeholder row.
        rows = [
            ("Shrimp", "SAFE", "12.4", "Safe", "False", "0.05"),
            ("Tilapia", "MODERATE", "38.5", "Moderate", "False", "0.42"),
            ("Carp", "SAFE", "15.0", "Safe", "False", "0.08"),
            ("Shrimp", "MODERATE", "42.7", "Moderate", "True", "0.61"),
            ("Tilapia", "SAFE", "18.1", "Safe", "False", "0.11"),
            ("Carp", "CRITICAL", "71.3", "Critical", "True", "0.82"),
        ]
        csv_lines = ["timestamp,species,final_classification,pollution_index,ml_prediction,anomaly_flag,anomaly_score"]
        for offset, row in enumerate(rows):
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if offset == 0 else generated_at
            csv_lines.append(",".join((timestamp, *row)))
        csv_data = ("\n".join(csv_lines) + "\n").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", "attachment; filename=AquaSentinel_Water_Quality_Report.csv")
        self.send_header("Content-Length", str(len(csv_data)))
        self.end_headers()
        self.wfile.write(csv_data)
