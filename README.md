# Hoja de trabajo #4 - Herramientas

Agente de preguntas frecuentes para Parachute S.A. que consulta una base de datos vectorial
(PostgreSQL + pgvector) a través de una herramienta configurada con el SDK de OpenAI Agents.

## Estructura

- `data/Corpus_FAQs_Parachute_SA_2026.txt`: dump de FAQs enviado por Parachute S.A.
- `cargar.py`: script de carga. Lee el corpus, genera los embeddings con
  `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers) y llena la tabla `faqs` de
  PostgreSQL. Es la versión multilingüe de `all-MiniLM-L6-v2`, del mismo tamaño (384
  dimensiones); se usa porque el corpus está en español.
- `agent.py`: agente con la herramienta `buscar_en_base_de_conocimientos`, que busca las FAQs
  más parecidas a la pregunta por distancia coseno en pgvector.
- `main.py`: loop de terminal de la sesión.

## Requisitos

- Python 3.10 o superior.
- Podman (o Docker).
- Una API key de Groq ([console.groq.com/keys](https://console.groq.com/keys)).

## Inicializar la infraestructura

1. Crear e iniciar la máquina de Podman (solo la primera vez, en Windows o macOS):

   ```
   podman machine init
   podman machine start
   ```

2. Levantar el contenedor de PostgreSQL con la extensión pgvector:

   ```
   podman run -d --name parachute-pgvector -e POSTGRES_USER=parachute -e POSTGRES_PASSWORD=parachute -e POSTGRES_DB=parachute -p 5432:5432 docker.io/pgvector/pgvector:pg17
   ```

   Con Docker es el mismo comando cambiando `podman` por `docker`. Para volver a levantarlo
   después de reiniciar la computadora: `podman machine start` y `podman start parachute-pgvector`.

3. Crear el entorno de Python e instalar las dependencias:

   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Copiar `.env.example` a `.env` y llenar `GROQ_API_KEY`. El `.env` está en el `.gitignore`.

## Ejecución

Primero se cargan los embeddings (crea la extensión `vector` y la tabla `faqs`; si se vuelve a
correr, recrea la tabla):

```
python cargar.py
```

Después se corre el agente:

```
python main.py
```

El agente responde preguntas seguidas dentro de la misma sesión. Para salir se escribe `Bye`
o se presiona Ctrl-C.
