import re
import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from db import guardar_sesion, get_db

# Descargar recursos necesarios de NLTK
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords

# 1. Base de conocimiento enriquecida (Corpus)
# Aquí añadimos las preguntas reales que fallaron en S1 para que ahora las entienda
CONOCIMIENTO_NLP = {
    "oferta academica carreras ingenierias": "En la UNE ofrecemos carreras del futuro como Ingeniería en Computación, Licenciatura en Administración, Diseño Gráfico y más.",
    "ingenieria computacion semestres duracion": "La Ingeniería en Computación consta de 8 semestres (4 años) con un plan actualizado hacia la IA.",
    "costo mensualidad inscripcion precio": "Las mensualidades de las ingenierías se adaptan a tus necesidades, van desde los $2,500 hasta los $4,000 MXN.",
    "modalidades maneras titulacion requisitos": "Contamos con opciones de titulación por promedio mínimo de 9.0, examen general de conocimientos o tesis profesional.",
    "clases ingles idiomas certificado": "Sí, todas nuestras carreras incluyen niveles obligatorios de inglés técnico y de negocios para tu preparación global.",
    "hola saludos buenas tardes": "¡Hola! Bienvenido al asistente de la UNE. ¿En qué carrera estás interesado hoy?",
    "adios hasta luego gracias": "Con gusto. Quedo a tus órdenes si tienes más dudas sobre nuestro plan de estudios."
}

# Preparar las listas para el modelo matemático
PREGUNTAS_CORPUS = list(CONOCIMIENTO_NLP.keys())
RESPUESTAS_CORPUS = list(CONOCIMIENTO_NLP.values())

def limpiar_texto_nlp(texto):
    """Pipeline NLP: Minúsculas, remover caracteres especiales, tokenización y remoción de stopwords."""
    texto = texto.lower().strip()
    # Quitar acentos de manera simple
    texto = re.sub(r'[áá]', 'a', texto)
    texto = re.sub(r'[éé]', 'e', texto)
    texto = re.sub(r'[íí]', 'i', texto)
    texto = re.sub(r'[óó]', 'o', texto)
    texto = re.sub(r'[úú]', 'u', texto)
    # Quitar signos de puntuación
    texto = re.sub(r"[^\w\s]", "", texto)
    
    # Tokenización manual por palabras
    palabras = texto.split()
    
    # Filtrar Stopwords (Palabras vacías en español como 'el', 'la', 'un', 'de')
    palabras_vacias = set(stopwords.words('spanish'))
    palabras_filtradas = [p for p in palabras if p not in palabras_vacias]
    
    return " ".join(palabras_filtradas)

def procesar_pregunta_tfidf(pregunta_usuario):
    """Calcula la similitud de coseno usando vectores TF-IDF."""
    pregunta_limpia = limpiar_texto_nlp(pregunta_usuario)
    
    # Si al limpiar queda vacío el mensaje
    if not pregunta_limpia:
        return "Por favor, introduce una pregunta más clara.", False, 0.0
        
    # Añadimos la pregunta temporalmente al corpus para vectorizar todo junto
    corpus_temporal = PREGUNTAS_CORPUS + [pregunta_limpia]
    
    # Inicializar el Vectorizador TF-IDF
    vectorizador = TfidfVectorizer()
    matriz_tfidf = vectorizador.fit_transform(corpus_temporal)
    
    # Separar los vectores del corpus y el vector del usuario (el último)
    vectores_corpus = matriz_tfidf[:-1]
    vector_usuario = matriz_tfidf[-1]
    
    # Calcular similitud de coseno entre el usuario y todas las preguntas base
    similitudes = cosine_similarity(vector_usuario, vectores_corpus).flatten()
    
    # Obtener el índice del elemento con mayor similitud
    indice_mejor_match = np.argmax(similitudes)
    mayor_similitud = similitudes[indice_mejor_match]
    
    # UMBRAL DE CONFIANZA: Si se parece en más del 25% (0.25) lo damos por válido
    if mayor_similitud >= 0.25:
        respuesta = RESPUESTAS_CORPUS[indice_mejor_match]
        reconocido = True
    else:
        respuesta = "Lo siento, mi modelo de lenguaje aún está aprendiendo sobre ese tema. Tu duda fue guardada."
        reconocido = False
        
    # Guardar en la colección de MongoDB especificando la fase s2
    guardar_sesion(
        fase="s2",
        usuario_raw=pregunta_usuario,
        usuario_norm=pregunta_limpia,
        respuesta=respuesta,
        reconocido=reconocido,
        similitud=float(mayor_similitud),
        metodo="tfidf"
    )
    
    return respuesta, reconocido, mayor_similitud

def chat_nlp():
    print("--- CHATBOT UNE FASE 2: MODELO NLP ACTIVO ---")
    print("(Escribe 'salir' para finalizar)\n")
    
    while True:
        usuario_input = input("Tú: ")
        if usuario_input.lower() in ["salir", "exit"]:
            break
            
        resp, rec, sim = procesar_pregunta_tfidf(usuario_input)
        print(f"Bot (Similitud: {round(sim, 2)}): {resp}\n")

if __name__ == "__main__":
    chat_nlp()