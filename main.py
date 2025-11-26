from fastapi import FastAPI, UploadFile, File
from PyPDF2 import PdfReader
import io
import re

app = FastAPI()

@app.get("/")
def home():
    return {"message": "API PDF OK"}

@app.post("/extract-json")
async def extract_json(pdf: UploadFile = File(...)):
    content = await pdf.read()
    reader = PdfReader(io.BytesIO(content))

    # Lecture complète du texte
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    # =========================
    # 1️⃣ DATE DU RAPPORT
    # =========================
    date_match = re.search(
        r"RAPPORT D['’]ARRIVAGE DU\s*:\s*(\d{2}/\d{2}/\d{4})",
        text
    )
    date_doc = date_match.group(1) if date_match else None

    # =========================
    # 2️⃣ EAN (13 chiffres dans le texte article)
    # =========================
    eans = re.findall(r"\b\d{13}\b", text)

    # =========================
    # 3️⃣ Extraction anomalies
    # =========================
    pattern = (
        r"(COLIS MANQUANT TOTAL-Missing|"
        r"COLIS MANQUANT PARTIEL-Partiel Missing|"
        r"R EMB|CASSE broken)"
        r"\s+(AARMQT|AARMQP|AARRCA|AARAVA)"
        r"\s+([A-Z0-9]+)"          # Expediteur
        r"\s+(\d{10})"             # Bordereau
        r"\s+(\d{8,12})"           # VIR
    )

    matches = re.findall(pattern, text)

    resultats = []

    for idx, m in enumerate(matches):
        anomalie_text, code, expediteur, bordereau, vir = m

        ean = eans[idx] if idx < len(eans) else None

        resultats.append({
            "date": date_doc,
            "commande_do": None,   # non disponible dans ce PDF
            "code": code,
            "anomalie": anomalie_text,
            "expediteur": expediteur,
            "bordereau": bordereau,
            "vir": vir,
            "ean": ean
        })

    return {"resultats": resultats}
