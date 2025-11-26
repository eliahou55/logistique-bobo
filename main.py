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

    # --- Lire texte brut ---
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    # Nettoyage & découpage en lignes approximatives
    raw_lines = re.split(r"\s{2,}", text)  # Deux espaces = changement logique
    lines = [l.strip() for l in raw_lines if l.strip()]

    # --- Récupérer la date ---
    date_match = re.search(r"ARRIVAGE DU\s*[: ]\s*(\d{2}/\d{2}/\d{4})", text)
    date_doc = date_match.group(1) if date_match else None

    # Codes cibles
    codes = {"AARMQT", "AARMQP", "AARRCA", "AARAVA"}

    # Dictionnaire anomalies
    map_anomalie = {
        "AARMQT": "COLIS MANQUANT TOTAL-Missing",
        "AARMQP": "COLIS MANQUANT PARTIEL-Partiel Missing",
        "AARRCA": "R EMB",
        "AARAVA": "CASSE broken"
    }

    resultats = []

    # --- Parcourir les lignes comme ton ancien script ---
    for line in lines:
        parts = line.split()

        # Vérifier si un code est présent dans la ligne
        for code in codes:
            if code in parts:
                idx = parts.index(code)

                # COMMANDES DO = la valeur juste avant le code
                commande_do = parts[idx - 1] if idx >= 1 else None

                anomalie = map_anomalie.get(code, "")

                # EXPEDITEUR = juste après le code
                expediteur = parts[idx + 1] if len(parts) > idx + 1 else None

                # BORDEREAU = nombre à 10 chiffres
                bord_match = re.search(r"\b\d{10}\b", line)
                bordereau = bord_match.group(0) if bord_match else None

                # VIR = nombre à 9 chiffres
                vir_match = re.search(r"\b\d{9}\b", line)
                vir = vir_match.group(0) if vir_match else None

                # EAN = nombre à 13 chiffres
                ean_match = re.search(r"\b\d{13}\b", line)
                ean = ean_match.group(0) if ean_match else None

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

                break

    return {"resultats": resultats}
