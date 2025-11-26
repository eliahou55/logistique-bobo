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

    # Texte complet
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    # =========================
    # ✅ DATE DU RAPPORT
    # =========================
    date_match = re.search(
        r"RAPPORT\s+D['’]ARRIVAGE\s+DU\s*:\s*(\d{2}/\d{2}/\d{4})",
        text,
        re.IGNORECASE
    )
    date_doc = date_match.group(1) if date_match else None

    # =========================
    # ✅ REGEX LIGNE ANOMALIE
    # =========================
    pattern = re.compile(
        r"(AARMQT|AARMQP|AARRCA|AARAVA)\s+"
        r"(COLIS MANQUANT TOTAL-Missing|COLIS MANQUANT PARTIEL-Partiel Missing|R EMB|CASSE broken)\s+"
        r"([A-Z0-9]{8,10})\s+"        # ✅ Commande DO
        r"(\d{9,12})\s+"              # ✅ Commande VIR
        r"(\d{10})\s+"                # ✅ Bordereau
        r"([A-Z0-9]+)\s+"             # ✅ Expéditeur
        r"(\d{13})",                  # ✅ EAN
        re.MULTILINE
    )

    matches = pattern.findall(text)

    resultats = []

    for m in matches:
        code, anomalie, commande_do, vir, bordereau, expediteur, ean = m

        resultats.append({
            "date": date_doc,
            "commande_do": commande_do,
            "code": code,
            "anomalie": anomalie,
            "expediteur": expediteur,
            "bordereau": bordereau,
            "vir": vir,
            "ean": ean
        })

    return {"resultats": resultats}
