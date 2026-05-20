"""Tests – Chatbot S3: LLM + RAG + Memoria Conversacional."""
import pytest
import importlib


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_s3():
    """Carga (o recarga) el módulo chatbot_s3 con el entorno de test activo."""
    import chatbot_s3
    importlib.reload(chatbot_s3)
    return chatbot_s3


# ── RAG ────────────────────────────────────────────────────────────────────────

class TestConstruirContextoRAG:
    def test_retorna_vacio_sin_documentos(self, monkeypatch):
        import db
        monkeypatch.setattr(db, "buscar_contexto_rag", lambda *a, **k: [])
        s3 = load_s3()
        assert s3._construir_contexto_rag("hola") == ""

    def test_incluye_pregunta_y_respuesta(self, monkeypatch):
        docs = [{"usuario_raw": "¿Cuánto cuesta la inscripción?", "respuesta": "$1500 MXN"}]
        import db
        monkeypatch.setattr(db, "buscar_contexto_rag", lambda *a, **k: docs)
        s3 = load_s3()
        ctx = s3._construir_contexto_rag("inscripción")
        assert "¿Cuánto cuesta la inscripción?" in ctx
        assert "$1500 MXN" in ctx

    def test_multiples_docs_incluidos(self, monkeypatch):
        docs = [
            {"usuario_raw": "¿Qué carreras hay?", "respuesta": "Ingeniería, Diseño..."},
            {"usuario_raw": "¿Hay inglés?",        "respuesta": "Sí, es obligatorio."},
        ]
        import db
        monkeypatch.setattr(db, "buscar_contexto_rag", lambda *a, **k: docs)
        s3 = load_s3()
        ctx = s3._construir_contexto_rag("carrera")
        assert "¿Qué carreras hay?" in ctx
        assert "¿Hay inglés?" in ctx


# ── Construcción de mensajes ───────────────────────────────────────────────────

class TestConstruirMensajes:
    def test_primer_rol_es_system(self):
        s3 = load_s3()
        msgs = s3._construir_mensajes("sess-1", "Hola", "")
        assert msgs[0]["role"] == "system"

    def test_ultimo_mensaje_es_usuario(self):
        s3 = load_s3()
        msgs = s3._construir_mensajes("sess-1", "¿Cuánto cuesta?", "")
        assert msgs[-1]["role"] == "user"
        assert msgs[-1]["content"] == "¿Cuánto cuesta?"

    def test_contexto_rag_se_agrega_al_system(self):
        s3 = load_s3()
        ctx = "--- Conversaciones previas ---\nP: test\nR: respuesta"
        msgs = s3._construir_mensajes("sess-1", "pregunta", ctx)
        assert ctx in msgs[0]["content"]

    def test_historial_previo_se_incluye(self, monkeypatch):
        import db
        historial = [
            {"role": "user",      "content": "Pregunta anterior"},
            {"role": "assistant", "content": "Respuesta anterior"},
        ]
        monkeypatch.setattr(db, "obtener_historial", lambda *a, **k: historial)
        s3 = load_s3()
        msgs = s3._construir_mensajes("sess-1", "Nueva pregunta", "")
        roles = [m["role"] for m in msgs]
        assert roles.count("user") == 2
        assert roles.count("assistant") == 1


# ── Proveedor LLM ──────────────────────────────────────────────────────────────

class TestObtenerRespuestaLLM:
    def test_error_ollama_lanza_runtime_error(self, monkeypatch):
        s3 = load_s3()
        monkeypatch.setattr(s3, "LLM_PROVIDER", "ollama")
        monkeypatch.setattr(s3, "_respuesta_ollama", lambda msgs: (_ for _ in ()).throw(RuntimeError("sin conexión")))
        with pytest.raises(RuntimeError):
            s3.obtener_respuesta_llm([{"role": "user", "content": "test"}])

    def test_ruta_openai(self, monkeypatch):
        s3 = load_s3()
        monkeypatch.setattr(s3, "LLM_PROVIDER", "openai")
        monkeypatch.setattr(s3, "_respuesta_openai", lambda msgs: "respuesta openai")
        resultado = s3.obtener_respuesta_llm([{"role": "user", "content": "test"}])
        assert resultado == "respuesta openai"

    def test_ruta_anthropic(self, monkeypatch):
        s3 = load_s3()
        monkeypatch.setattr(s3, "LLM_PROVIDER", "anthropic")
        monkeypatch.setattr(s3, "_respuesta_anthropic", lambda msgs: "respuesta anthropic")
        resultado = s3.obtener_respuesta_llm([{"role": "user", "content": "test"}])
        assert resultado == "respuesta anthropic"

    def test_ruta_ollama_por_defecto(self, monkeypatch):
        s3 = load_s3()
        monkeypatch.setattr(s3, "LLM_PROVIDER", "ollama")
        monkeypatch.setattr(s3, "_respuesta_ollama", lambda msgs: "respuesta ollama")
        resultado = s3.obtener_respuesta_llm([{"role": "user", "content": "test"}])
        assert resultado == "respuesta ollama"
