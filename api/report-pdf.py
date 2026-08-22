"""Dependency-free Vercel serverless PDF report download fallback."""
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf() -> bytes:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        ("AquaSentinel+ Water Quality Intelligence Report", 20),
        (f"Generated: {generated_at}", 10),
        ("Executive Summary", 14),
        ("Current dashboard report is ready for download.", 11),
        ("Pollution Index: 12.4 / 100", 11),
        ("Overall Status: SAFE", 11),
        ("Recommendation: Maintain routine monitoring and standard feeding schedule.", 11),
        ("For live farm telemetry, run the FastAPI service with the dashboard.", 9),
    ]
    y = 750
    commands = ["BT"]
    for text, size in lines:
        # Tm resets the text matrix for every line. Using relative Td commands
        # moved later lines outside the page and produced an apparently blank PDF.
        commands.append(f"/F1 {size} Tf")
        commands.append(f"1 0 0 1 50 {y} Tm ({_escape_pdf_text(text)}) Tj")
        y -= 26 if size >= 14 else 20
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        pdf = build_pdf()
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", "attachment; filename=AquaSentinel_Executive_Report.pdf")
        self.send_header("Content-Length", str(len(pdf)))
        self.end_headers()
        self.wfile.write(pdf)
