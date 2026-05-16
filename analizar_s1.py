import sys
import os

# Asegurar que Python encuentre la carpeta src
sys.path.insert(0, 'src')

from db import get_db, estadisticas

db = get_db()

print("=" * 50)
print("ANALISIS DE DATOS SEMANA 1")
print("=" * 50)

# 1. Obtener estadísticas generales de MongoDB
stats = estadisticas()

print(f"Total conversaciones : {stats['total']}")
print(f"Reconocidas          : {stats['reconocidos']}")
print(f"No reconocidas       : {stats['no_reconocidos']}")
print(f"Tasa de éxito        : {stats['tasa_exito']}%")

# 2. Mostrar qué preguntas no se reconocieron
print("\nPreguntas NO reconocidas (ordenadas):")
cursor = db["sesiones"].find(
    {"fase": "s1", "reconocido": False},
    {"usuario_raw": 1, "_id": 0}
)

for doc in cursor:
    print(f" - {doc['usuario_raw']}")