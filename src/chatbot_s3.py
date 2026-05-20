"""
Chatbot S3 – LLM + RAG + Memoria Conversacional
Soporta: Ollama (local), OpenAI API, Anthropic API
"""
import os
from dotenv import load_dotenv
from db import guardar_sesion, guardar_turno_memoria, obtener_historial, buscar_contexto_rag, nueva_sesion_id

load_dotenv()

LLM_PROVIDER  = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "llama3")
OPENAI_MODEL  = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

SYSTEM_PROMPT = (
    "Eres un asistente virtual académico de la Universidad UNE. "
    "Respondes preguntas sobre carreras, costos de inscripción y mensualidades, "
    "modalidades de titulación, clases de inglés y certificaciones. "
    "Sé siempre amable, claro y conciso. Responde SIEMPRE en español. "
    "Si no tienes certeza de algo, indícalo con honestidad."
)

# ── Proveedores LLM ───────────────────────────────────────────────────────────

def _respuesta_ollama(messages):
    try:
        import ollama
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")


def _respuesta_openai(messages):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"OpenAI error: {e}")


def _respuesta_anthropic(messages):
    try:
        import anthropic
        system = next(
            (m["content"] for m in messages if m["role"] == "system"),
            SYSTEM_PROMPT,
        )
        chat_msgs = [m for m in messages if m["role"] != "system"]
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            system=system,
            messages=chat_msgs,
            max_tokens=512,
        )
        return response.content[0].text
    except Exception as e:
        raise RuntimeError(f"Anthropic error: {e}")


def obtener_respuesta_llm(messages):
    """Enruta al proveedor LLM configurado."""
    if LLM_PROVIDER == "openai":
        return _respuesta_openai(messages)
    if LLM_PROVIDER == "anthropic":
        return _respuesta_anthropic(messages)
    return _respuesta_ollama(messages)

# ── RAG + construcción de mensajes ────────────────────────────────────────────

def _construir_contexto_rag(query):
    """Recupera Q&A relevantes de MongoDB para enriquecer el prompt."""
    docs = buscar_contexto_rag(query, limite=5)
    if not docs:
        return ""
    lineas = ["--- Conversaciones previas relevantes ---"]
    for doc in docs:
        lineas.append(f"P: {doc['usuario_raw']}")
        lineas.append(f"R: {doc['respuesta']}")
        lineas.append("")
    return "\n".join(lineas)


def _construir_mensajes(session_id, query, contexto_rag):
    """Arma la lista de mensajes: system (con RAG) + historial + pregunta actual."""
    system_content = SYSTEM_PROMPT
    if contexto_rag:
        system_content += f"\n\n{contexto_rag}"

    historial = obtener_historial(session_id, limite=10)

    messages = [{"role": "system", "content": system_content}]
    messages.extend(historial)
    messages.append({"role": "user", "content": query})
    return messages

# ── Loop principal ─────────────────────────────────────────────────────────────

def chatbot_s3(session_id=None):
    if session_id is None:
        session_id = nueva_sesion_id()

    print("\n=== Chatbot UNE – Fase 3: LLM + RAG + Memoria ===")
    print(f"Proveedor LLM : {LLM_PROVIDER}")
    print(f"Sesión ID     : {session_id[:8]}...")
    print("Escribe 'salir' para terminar.\n")

    while True:
        try:
            user_input = input("Tú: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSesión finalizada.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("salir", "exit", "quit"):
            print("¡Hasta luego! Que tengas un excelente día.")
            break

        # 1. RAG – recuperar contexto relevante de MongoDB
        contexto_rag = _construir_contexto_rag(user_input)

        # 2. Construir mensajes con historial y contexto RAG
        messages = _construir_mensajes(session_id, user_input, contexto_rag)

        # 3. Llamar al LLM
        try:
            respuesta = obtener_respuesta_llm(messages)
        except RuntimeError as e:
            respuesta = f"[Error al conectar con el modelo: {e}]"

        print(f"Bot: {respuesta}\n")

        # 4. Guardar en memoria conversacional (colección 'memoria')
        guardar_turno_memoria(session_id, "user", user_input)
        guardar_turno_memoria(session_id, "assistant", respuesta)

        # 5. Guardar en 'sesiones' (compatible con fases anteriores)
        guardar_sesion(
            fase="s3",
            usuario_raw=user_input,
            usuario_norm=user_input.lower(),
            respuesta=respuesta,
            reconocido=True,
            similitud=1.0,
            metodo=f"llm_{LLM_PROVIDER}",
        )


if __name__ == "__main__":
    chatbot_s3()
