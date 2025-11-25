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

    # Lire toutes les pages
    texte = ""
    for page in reader.pages:
        texte += page.extract_text() or ""

    lignes = [l.strip() for l in texte.split("\n") if l.strip()]

    # Trouver la date globale du document
    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", texte)
    date_doc = date_match.group(1) if date_match else None

    resultats = []

    i = 0
    while i < len(lignes):
        ligne = lignes[i]

        # Détection des anomalies (AARMQT / AARRCA / AARMQP / AARAVA)
        m = re.match(r"(A[A-Z]{4,5})\s+(.+)", ligne)
        if m:
            code = m.group(1)
            anomalie = m.group(2).strip()

            # Les 7 lignes suivantes sont normalisées
            commande_do = lignes[i+1]
            commande_vir = lignes[i+2]
            bordereau = lignes[i+3]
            expediteur = lignes[i+4]
            ean = lignes[i+5]

            # Article : peut être sur plusieurs lignes
            article = lignes[i+6]
            j = i + 7
            while j < len(lignes) and not lignes[j].startswith("AARM") and not lignes[j].startswith("AARR") and not lignes[j].startswith("AARAV"):
                # Arrêter quand on tombe sur le destinataire (nom propre → 2 mots typiques)
                if len(lignes[j].split()) == 2 and lignes[j].split()[0].isalpha() and lignes[j].split()[1].isalpha():
                    break
                article += " " + lignes[j]
                j += 1

            # Destinataire = ligne suivante
            destinataire = lignes[j]

            # Ajouter au JSON
            resultats.append({
                "date": date_doc,
                "code": code,
                "anomalie": anomalie,
                "commande_do": commande_do,
                "commande_vir": commande_vir,
                "bordereau": bordereau,
                "expediteur": expediteur,
                "ean": ean,
                "article": article.strip(),
                "destinataire": destinataire.strip()
            })

            # Avancement
            i = j + 1
            continue

        i += 1

    return {"resultats": resultats}
