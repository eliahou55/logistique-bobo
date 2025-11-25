from fastapi import FastAPI, UploadFile, File
from PyPDF2 import PdfReader
import io
import re

app = FastAPI()

@app.post("/extract-json")
async def extract_json(pdf: UploadFile = File(...)):
    content = await pdf.read()
    reader = PdfReader(io.BytesIO(content))

    text = ""
    for p in reader.pages:
        text += p.extract_text() or ""

    # dictionnaire anomalies
    anomalie_map = {
        "AARMQT": "COLIS MANQUANT TOTAL-Missing",
        "AARMQP": "COLIS MANQUANT PARTIEL-Partiel Missing",
        "AARRCA": "R EMB",
        "AARAVA": "CASSE broken"
    }

    results = []

    # Regex : libellé + code + expéditeur + bordereau + vir
    pattern = r"(COLIS MANQUANT TOTAL-Missing|COLIS MANQUANT PARTIEL-Partiel Missing|R EMB|CASSE broken)\s+(AARMQT|AARMQP|AARRCA|AARAVA)\s+([A-Z0-9]+)\s+(\d{10})\s+(\d{8,12})"

    matches = re.findall(pattern, text)

    for m in matches:
        anomalie_text, code, expediteur, bordereau, vir = m

        results.append({
            "code": code,
            "anomalie": anomalie_text,
            "expediteur": expediteur,
            "bordereau": bordereau,
            "vir": vir
        })

    return {"resultats": results}
