import os

import psycopg
from agents import (
    Agent,
    ModelSettings,
    OpenAIChatCompletionsModel,
    function_tool,
    set_tracing_disabled,
)
from openai import AsyncOpenAI
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

URL_POR_DEFECTO = "postgresql://parachute:parachute@localhost:5432/parachute"
MODELO_EMBEDDINGS = "paraphrase-multilingual-MiniLM-L12-v2"

INSTRUCCIONES = """Sos el agente de preguntas frecuentes de la empresa Parachute S.A.
Para cada pregunta del usuario usá la herramienta buscar_en_base_de_conocimientos y respondé
únicamente con la información que devuelva.

Reglas:
- Usá los resultados que respondan la pregunta, aunque estén redactados de otra forma.
- Si ningún resultado responde la pregunta, contestá exactamente: "No puedo responder esa pregunta, no está en la información que tengo disponible."
- No inventés fechas, precios, direcciones ni contactos que no estén en la información devuelta.
- No uses conocimiento externo, aunque estés seguro de la respuesta.
- Contestá en español, de forma corta y directa."""


def crear_agente():
    """Arma el agente con su herramienta de consulta a la base de conocimientos en pgvector."""
    modelo_embeddings = SentenceTransformer(MODELO_EMBEDDINGS)
    conexion = psycopg.connect(os.getenv("DATABASE_URL", URL_POR_DEFECTO), autocommit=True)
    register_vector(conexion)

    @function_tool
    def buscar_en_base_de_conocimientos(consulta: str) -> list[dict]:
        """Busca en la base de conocimientos de Parachute S.A. las preguntas frecuentes más parecidas a la consulta.

        Args:
            consulta: La pregunta del usuario, copiada tal cual la escribió, sin reformularla.
        """
        vector = modelo_embeddings.encode(consulta)
        filas = conexion.execute(
            "SELECT pregunta, respuesta FROM faqs ORDER BY embedding <=> %s LIMIT 3",
            (vector,),
        ).fetchall()
        return [{"pregunta": p, "respuesta": r} for p, r in filas]

    # Las trazas del SDK se suben a OpenAI; con Groq no hay a dónde mandarlas.
    set_tracing_disabled(True)

    cliente = AsyncOpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url=os.getenv("BASE_URL", "https://api.groq.com/openai/v1"),
    )

    return Agent(
        name="Agente FAQ Parachute S.A.",
        instructions=INSTRUCCIONES,
        tools=[buscar_en_base_de_conocimientos],
        model=OpenAIChatCompletionsModel(
            model=os.getenv("MODELO", "openai/gpt-oss-120b"), openai_client=cliente
        ),
        model_settings=ModelSettings(temperature=0),
    )
