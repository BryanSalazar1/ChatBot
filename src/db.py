from pymongo import MongoClient, ASCENDING
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

# Variables globales para el patrón Singleton
_client = None
_db = None

def get_db():
    """Patrón Singleton: reutiliza la conexión si ya existe."""
    global _client, _db
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise ValueError("MONGODB_URI no está definida en .env")
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _db = _client["chatbot_db"]
        
        # Crear índices para consultas eficientes
        _db["sesiones"].create_index([("timestamp", ASCENDING)])
        _db["sesiones"].create_index([("reconocido", ASCENDING)])
        _db["memoria"].create_index([("session_id", ASCENDING)])
        _db["memoria"].create_index([("timestamp", ASCENDING)])
        print("[DB] Conexión a MongoDB establecida.")
    return _db

def guardar_sesion(fase, usuario_raw, usuario_norm, respuesta, reconocido, similitud=None, metodo="desconocido"):
    """Guarda un turno de conversación en la colección 'sesiones'."""
    db = get_db()
    doc = {
        "fase": fase,
        "timestamp": datetime.now(timezone.utc),
        "usuario_raw": usuario_raw,
        "usuario": usuario_norm,
        "respuesta": respuesta,
        "reconocido": reconocido,
        "similitud": similitud,
        "metodo": metodo
    }
    resultado = db["sesiones"].insert_one(doc)
    return str(resultado.inserted_id)

def obtener_no_reconocidos(fase="s1", limite=200):
    """Recupera mensajes que el bot NO pudo responder."""
    db = get_db()
    cursor = db["sesiones"].find(
        {"fase": fase, "reconocido": False},
        {"usuario": 1, "usuario_raw": 1, "_id": 0}
    ).sort("timestamp", ASCENDING).limit(limite)
    return list(cursor)

def estadisticas():
    """Resumen estadístico de las conversaciones almacenadas."""
    db = get_db()
    col = db["sesiones"]
    total = col.count_documents({})
    reconocidos = col.count_documents({"reconocido": True})
    
    pipeline = [
        {"$group": {"_id": "$fase", "count": {"$sum": 1}}}
    ]
    por_fase = {doc["_id"]: doc["count"] for doc in col.aggregate(pipeline)}
    
    return {
        "total": total,
        "reconocidos": reconocidos,
        "no_reconocidos": total - reconocidos,
        "tasa_exito": round((reconocidos / total * 100), 1) if total else 0,
        "por_fase": por_fase
    }

# ── Fase 3: Memoria conversacional ───────────────────────────────────────────

def nueva_sesion_id():
    """Genera un ID único para una sesión de conversación."""
    return str(uuid.uuid4())

def guardar_turno_memoria(session_id, role, content):
    """Guarda un turno (usuario o asistente) en la colección 'memoria'."""
    db = get_db()
    doc = {
        "session_id": session_id,
        "role": role,        # "user" o "assistant"
        "content": content,
        "timestamp": datetime.now(timezone.utc),
    }
    return str(db["memoria"].insert_one(doc).inserted_id)

def obtener_historial(session_id, limite=10):
    """Devuelve los últimos N turnos de una sesión (sin _id ni timestamp)."""
    db = get_db()
    cursor = db["memoria"].find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "content": 1}
    ).sort("timestamp", ASCENDING).limit(limite)
    return list(cursor)

# ── Fase 3: RAG desde MongoDB ─────────────────────────────────────────────────

def buscar_contexto_rag(query_texto, limite=5):
    """Recupera Q&A previas relevantes para enriquecer el prompt del LLM (RAG)."""
    db = get_db()
    docs = list(
        db["sesiones"].find(
            {"reconocido": True},
            {"_id": 0, "usuario_raw": 1, "respuesta": 1, "similitud": 1}
        ).sort("similitud", -1).limit(80)
    )
    if not docs:
        return []

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        textos = [d["usuario_raw"] for d in docs]
        vectorizer = TfidfVectorizer()
        matrix = vectorizer.fit_transform(textos + [query_texto])
        sims = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
        indices = sims.argsort()[-limite:][::-1]
        return [docs[i] for i in indices if sims[i] > 0.05]
    except Exception:
        return docs[:limite]