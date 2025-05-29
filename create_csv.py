import os

import pandas as pd

from utils import get_embedding, read_docx, read_pdf

if __name__ == "__main__":
    root_path = "static"
    data = {
        "titles": [],
        "embeddings": [],
    }
    for file_name in os.listdir(root_path):
        ruta_completa = os.path.join(root_path, file_name)
        if os.path.isfile(ruta_completa):
            name, ext = os.path.splitext(file_name)
            if ext == ".pdf":
                doc_str = read_pdf(ruta_completa)
            elif ext == ".docx":
                doc_str = read_docx(ruta_completa)
            else:
                continue
            data["titles"].append(name)
            data["embeddings"].append(get_embedding(doc_str))

    df = pd.DataFrame(data)
    df.to_csv("embeddings.csv", index=False)
