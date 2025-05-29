from config import client
from docx import Document
from PyPDF2 import PdfReader


def read_docx(ruta_archivo):
    doc = Document(ruta_archivo)
    texto_completo = []

    for para in doc.paragraphs:
        texto_completo.append(para.text)

    return "\n".join(texto_completo)


def read_pdf(ruta_archivo):
    reader = PdfReader(ruta_archivo)
    texto_completo = []

    for page in reader.pages:
        texto_completo.append(page.extract_text())

    return "\n".join(texto_completo)


def get_embedding(text: str, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


if __name__ == "__main__":
    ruta_archivo = "static/Blancanieves-Hermanos_Grimm.pdf"
    texto = read_pdf(ruta_archivo)
    print(texto)
