import re
import subprocess

from fastapi import HTTPException, status
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import openai_client


async def get_embedding(text: str, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    response = await openai_client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


def extract_text_from_doc(doc_path):
    result = subprocess.run(["antiword", doc_path], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No antiword installed",
        )


def preprocess_text(text):
    # Convertir a minúsculas
    text = text.lower()
    # Eliminar caracteres especiales
    text = re.sub(r"[^\w\s]", "", text)
    # Tokenización
    tokens = word_tokenize(text)
    # Eliminar stopwords
    stop_words = set(stopwords.words("spanish") + stopwords.words("english"))
    tokens = [word for word in tokens if word not in stop_words]
    # Convertir la lista de tokens de nuevo a texto
    return " ".join(tokens)  # ← Ahora devuelve un string


def create_search_index(document_text):
    chunks = [chunk for chunk in document_text.split("\n") if chunk.strip()]

    vectorizer = TfidfVectorizer(preprocessor=preprocess_text)
    tfidf_matrix = vectorizer.fit_transform(chunks)

    return vectorizer, tfidf_matrix, chunks


def find_most_relevant_chunk(query, vectorizer, tfidf_matrix, chunks):
    query_vec = vectorizer.transform([query])

    similarities = cosine_similarity(query_vec, tfidf_matrix)

    most_similar_idx = similarities.argmax()

    return chunks[most_similar_idx], similarities[0][most_similar_idx], most_similar_idx


def find_answer_in_document(text, query):
    # Crear índice de búsqueda
    vectorizer, tfidf_matrix, chunks = create_search_index(text)

    # Buscar el fragmento más relevante
    most_relevant_chunk, similarity_score, most_similar_idx = find_most_relevant_chunk(
        query, vectorizer, tfidf_matrix, chunks
    )

    return {
        "answer": most_relevant_chunk,
        "context": get_context(text, most_relevant_chunk),
        "paragraph": most_similar_idx,
    }


def get_context(full_text, answer_chunk, window_size=2):
    # Obtener párrafos alrededor de la respuesta para contexto
    paragraphs = [p for p in full_text.split("\n") if p.strip()]
    try:
        idx = paragraphs.index(answer_chunk)
        start = max(0, idx - window_size)
        end = min(len(paragraphs), idx + window_size + 1)
        return "\n".join(paragraphs[start:end])

    except ValueError:
        return answer_chunk


if __name__ == "__main__":
    # asyncio.run(get_embedding("Hola"))

    text = """La mujer es el reflejo de su hombre
Hoy voy a romper una norma o una costumbre y voy a publicar una opinión, sin más. No voy a hablar de coaching ni de desarrollo personal o profesional. Hoy voy a hablar Brad Pitt y una frase que se le atribuye.

«La mujer es el reflejo de su hombre»

Esta frase está circulando por las redes sociales como algo quera para algunas mujeres es hermoso y está atribuía a Brad Pitt.

Igual soy un señor extraño… pero a mi me parece limitante (por ser cuidadoso con mis palabras)

Según interpreto la frase: toda mujer (si naces mujer no tienes otra posibilidad) será feliz si su hombre la trata bien.

La declaración completa es una bonita prueba de amor pero de vedad ¿Una mujer se puede sentir cómoda al identificarse con esta visión?

¿Nos parece mal que digan que las mujeres conducen mal, pero es incluso romántico que nos digan que todas ellas condicionan su estado vital al del hombre con el que conviven?

Se me amontonan las posibilidades negativas de esta afirmación, y lo que me bloquea el pensamiento es la idea de que una mujer pueda realmente sentirse bien leyendo que su felicidad depende de que un hombre la mime.

Aquí dejo el enlace a la noticia origina (uno de ellos): http://www.republica.com.uy/la-mujer-es-un-reflejo-de-su-hombre/

Una lectura de la historia me hace sentir bien, otra no tanto.

La frase, como conclusión, me parece una conclusión guiada por el machismo. Como cualquier conclusión científica errónea, parece que demuestra los hechos, pero no tiene por qué ser la exacta. Es algo así como «Vi a mi mujer sufriendo y la mimé. Eso hizo que se sintiera mejor, así que las mujeres sólo responden a mimos»

Y si extrapolo esa conclusión… «la mujer sólo será feliz si un hombre la hace feliz»

Y esto me lleva a otra línea de pensamiento, ya que me parece que la afirmación está en la línea de esas frases que dicen que todas las mujeres son princesas o que son almas especiales, o que la mujer es lo más hermoso o que hay que cuidarlas por ser mujer …  Esto me parece mal porque, de ser cierto ¿Es entonces un humano-hembra más merecedor de cariño y respeto que los humanos-macho?
"""

    ans = find_answer_in_document(text, "Que representa la mujer para el hombre")
    print(ans)
