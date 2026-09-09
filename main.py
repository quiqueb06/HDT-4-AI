import os
import sys

from agents import Runner
from dotenv import load_dotenv

from agent import crear_agente


def main():
    # Evita que los acentos rompan la salida en terminales de Windows.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    load_dotenv()

    if not os.getenv("GROQ_API_KEY"):
        print("Falta la variable GROQ_API_KEY. Copiá .env.example a .env y agregá tu llave.")
        return 1

    agente = crear_agente()
    # Historial de la sesión: solo las preguntas del usuario y las respuestas del agente.
    historial = []

    print("Agente de preguntas frecuentes - Parachute S.A.")
    print('Escribí "Bye" o presioná Ctrl-C para salir.\n')

    while True:
        try:
            pregunta = input("Vos: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nHasta luego.")
            return 0

        if not pregunta:
            continue

        if pregunta.lower() == "bye":
            print("Hasta luego.")
            return 0

        try:
            mensajes = historial + [{"role": "user", "content": pregunta}]
            respuesta = Runner.run_sync(agente, mensajes).final_output
            historial = mensajes + [{"role": "assistant", "content": respuesta}]
            print(f"Agente: {respuesta}\n")
        except Exception as error:
            print(f"Ocurrió un error al consultar el modelo: {error}\n")


if __name__ == "__main__":
    sys.exit(main())
