import sys
import os

# Asegurar que Python encuentre la carpeta src
sys.path.insert(0, 'src')

from db import get_db

def ejecutar_consulta_escuela():
    # 1. Conectarse a la base de datos usando el Singleton
    db = get_db()
    
    print("=" * 60)
    print("EJECUTANDO CONSULTA: MATCHES DE ALTA CALIDAD (SIMILITUD > 0.5)")
    print("=" * 60)
    
    # 2. LA CONSULTA SOLICITADA POR LA ESCUELA
    cursor = db["sesiones"].find(
        {"fase": "s2", "similitud": {"$gt": 0.5}}
    ).sort("similitud", -1)
    
    # 3. Mostrar los resultados en la terminal
    conteo = 0
    for doc in cursor:
        conteo += 1
        print(f"\nMatch #{conteo}:")
        print(f"  Pregunta Usuario : {doc['usuario_raw']}")
        print(f"  Respuesta Bot    : {doc['respuesta']}")
        print(f"  Similitud (IA)   : {round(doc['similitud'], 4)}")
        print("-" * 40)
        
    if conteo == 0:
        print("\n[!] No se encontraron documentos de la fase 's2' con similitud mayor a 0.5.")
        print("Asegúrate de haber interactuado antes con tu nuevo bot corriendo: python src/chatbot_s2.py")

if __name__ == "__main__":
    ejecutar_consulta_escuela()