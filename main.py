from fastapi import FastAPI, UploadFile, File
from PyPDF2 import PdfReader
import io

app = FastAPI()

@app.get("/")
def home():
    return {"message": "API PDF OK"}

@app.post("/test-pdf")
async def test_pdf(pdf: UploadFile = File(...)):
    content = await pdf.read()
    reader = PdfReader(io.BytesIO(content))

    texte = ""
    for page in reader.pages:
        texte += page.extract_text() or ""

    return {"raw_text": texte}
