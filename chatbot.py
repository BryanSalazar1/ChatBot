from db import save_conversation

RESPONSES = {
    "hola": "¡Hola! ¿En qué puedo ayudarte?",
    "hello": "Hello! How can I help you?",
    "¿cómo estás?": "Estoy bien, gracias por preguntar. ¿Y tú?",
    "como estas": "Estoy bien, gracias. ¿En qué te puedo ayudar?",
    "ayuda": "Puedo responder preguntas básicas. Escribe algo y lo intento.",
    "help": "I can answer basic questions. Type something and I'll try!",
    "bye": "¡Hasta luego! 👋",
    "adiós": "¡Hasta luego! 👋",
    "adios": "¡Hasta luego! 👋",
}

DEFAULT_RESPONSE = "No entendí eso. ¿Puedes reformularlo?"


def get_response(user_input: str) -> str:
    key = user_input.strip().lower()
    if key in RESPONSES:
        return RESPONSES[key]
    # Búsqueda parcial si no hay coincidencia exacta
    for keyword, response in RESPONSES.items():
        if keyword in key:
            return response
    return DEFAULT_RESPONSE


def main():
    print("ChatBot iniciado. Escribe 'salir' para terminar.\n")
    while True:
        user_input = input("Tú: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("salir", "exit", "quit"):
            print("Bot: ¡Hasta luego!")
            break
        response = get_response(user_input)
        print(f"Bot: {response}\n")
        save_conversation(user_input, response)


if __name__ == "__main__":
    main()
