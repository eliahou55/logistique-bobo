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

    # ===== 1. TEXTE BRUT =====
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    # normalisation
    text = re.sub(r"\s+", " ", text)

    # ===== 2. DATE =====
    date_match = re.search(r"ARRIVAGE DU\s*:\s*(\d{2}/\d{2}/\d{4})", text)
    date_doc = date_match.group(1) if date_match else None

    # ===== 3. CHAQUE ANOMALIE (code uniquement) =====
    codes = re.finditer(r"(AARMQT|AARMQP|AARRCA|AARAVA)", text)

    resultats = []

    for match in codes:
        idx = match.start()

        # On prend une fenêtre de texte autour du code
        bloc = text[idx:idx+300]

        # Commande DO = mot alphanum proche (8–10)
        do_match = re.search(r"\b[A-Z0-9]{8,10}\b", bloc)
        commande_do = do_match.group(0) if do_match else None

        # VIR = 9 chiffres
        vir_match = re.search(r"\b\d{9}\b", bloc)
        vir = vir_match.group(0) if vir_match else None

        # Bordereau = 10 chiffres
        bordereau_match = re.search(r"\b\d{10}\b", bloc)
        bordereau = bordereau_match.group(0) if bordereau_match else None

        # EAN = 13 chiffres
        ean_match = re.search(r"\b\d{13}\b", bloc)
        ean = ean_match.group(0) if ean_match else None

        resultats.append({
            "date": date_doc,
            "code": match.group(1),
            "commande_do": commande_do,
            "bordereau": bordereau,
            "vir": vir,
            "ean": ean
        })

    return {"resultats": resultats}
