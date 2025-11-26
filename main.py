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

    # Normalisation des espaces
    text_norm = re.sub(r"\s+", " ", text)

    # ===== 2. DATE =====
    date_match = re.search(
        r"ARRIVAGE DU\s*[: ]\s*(\d{2}/\d{2}/\d{4})",
        text_norm
    )
    date_doc = date_match.group(1) if date_match else None

    # ===== 3. TOUS LES CODES D'ANOMALIE =====
    code_iter = re.finditer(r"(AARMQT|AARMQP|AARRCA|AARAVA)", text_norm)

    resultats = []

    for match in code_iter:
        code = match.group(1)
        idx = match.start()

        # --- Texte AVANT le code : pour DO + anomalie ---
        pre = text_norm[max(0, idx - 120):idx]

        # On cherche : [COMMANDE_DO] [LIBELLÉ ANOMALIE]
        # ex : "IUDPFYSUI COLIS MANQUANT TOTAL-Missing"
        do_anom = re.search(
            r"([A-Z0-9]{8,12})\s+"
            r"(COLIS MANQUANT TOTAL-Missing|"
            r"COLIS MANQUANT PARTIEL-Partiel Missing|"
            r"R EMB|CASSE broken)",
            pre
        )

        commande_do = do_anom.group(1) if do_anom else None
        anomalie = do_anom.group(2) if do_anom else None

        # --- Texte APRÈS le code : expéditeur, bordereau, vir, ean ---
        after = text_norm[idx:idx + 200]
        after_parts = after.split()

        # expéditeur = mot juste après le code
        expediteur = after_parts[1] if len(after_parts) > 1 else None

        # bordereau = 1er nombre à 10 chiffres après le code
        bord_m = re.search(r"\b\d{10}\b", after)
        bordereau = bord_m.group(0) if bord_m else None

        # vir = 1er nombre à 9 chiffres après le code
        vir_m = re.search(r"\b\d{9}\b", after)
        vir = vir_m.group(0) if vir_m else None

        # ean = 1er nombre à 13 chiffres après le code
        ean_m = re.search(r"\b\d{13}\b", after)
        ean = ean_m.group(0) if ean_m else None

        resultats.append({
            "date": date_doc,
            "commande_do": commande_do,
            "code": code,
            "anomalie": anomalie,
            "expediteur": expediteur,
            "bordereau": bordereau,
            "vir": vir,
            "ean": ean,
        })

    return {"resultats": resultats}
