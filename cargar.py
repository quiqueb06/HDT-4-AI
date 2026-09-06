import os
import re
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

RUTA_POR_DEFECTO = "data/Corpus_FAQs_Parachute_SA_2026.txt"
URL_POR_DEFECTO = "postgresql://parachute:parachute@localhost:5432/parachute"
MODELO_EMBEDDINGS = "paraphrase-multilingual-MiniLM-L12-v2"


def leer_fichas(ruta):
    """Separa el corpus en fichas usando las líneas de guiones como divisor."""
    texto = Path(ruta).read_text(encoding="utf-8")
    fichas = []

    for bloque in re.split(r"^-{20,}$", texto, flags=re.MULTILINE):
        campos = dict(re.findall(r"^(ID|CATEGORÍA|PREGUNTA|RESPUESTA): (.*)$", bloque, re.MULTILINE))
        if "ID" in campos:
            fichas.append(campos)

    return fichas


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    load_dotenv()

    fichas = leer_fichas(os.getenv("RUTA_CORPUS", RUTA_POR_DEFECTO))
    print(f"Fichas leídas del corpus: {len(fichas)}")

    modelo = SentenceTransformer(MODELO_EMBEDDINGS)
    textos = [f"{f['PREGUNTA']} {f['RESPUESTA']}" for f in fichas]
    embeddings = modelo.encode(textos, show_progress_bar=True)

    with psycopg.connect(os.getenv("DATABASE_URL", URL_POR_DEFECTO), autocommit=True) as conexion:
        conexion.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conexion)

        conexion.execute("DROP TABLE IF EXISTS faqs")
        conexion.execute(
            f"""CREATE TABLE faqs (
                id TEXT PRIMARY KEY,
                categoria TEXT,
                pregunta TEXT,
                respuesta TEXT,
                embedding vector({modelo.get_embedding_dimension()})
            )"""
        )

        with conexion.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO faqs (id, categoria, pregunta, respuesta, embedding) VALUES (%s, %s, %s, %s, %s)",
                [
                    (f["ID"], f.get("CATEGORÍA"), f["PREGUNTA"], f.get("RESPUESTA"), e)
                    for f, e in zip(fichas, embeddings)
                ],
            )

        total = conexion.execute("SELECT COUNT(*) FROM faqs").fetchone()[0]

    print(f"Filas insertadas en la tabla faqs: {total}")


if __name__ == "__main__":
    main()
