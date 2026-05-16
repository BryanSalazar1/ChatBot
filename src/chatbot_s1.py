import re
from db import guardar_sesion, estadisticas

# Base de conocimiento oficial de la Fase 2
BASE = {
    "hola": "Hola, bienvenido. ¿Cómo puedo ayudarte?",
    "adios": "Hasta luego. Fue un placer atenderte.",
    "precio": "Nuestros productos van de $100 a $500 MXN.",
    "horario": "Atendemos lunes a viernes de 9am a 6pm.",
    "direccion": "Estamos en Av. Universidad 123, Guadalajara.",
    "telefono": "Llámanos al 33-1234-5678.",
    "garantia": "Todos los productos tienen 1 año de garantía.",
    "envio": "Enviamos a toda la república en 3 a 5 días hábiles.",
    "devolucion": "Aceptamos devoluciones en 30 días con ticket.",
    "gracias": "Con mucho gusto. ¿Hay algo más en que pueda ayudar?",
}

REEMPLAZOS_ACENTO = str.maketrans(
    "áéíóúÁÉÍÓÚüÜñÑ",
    "aeiouaeiouuunn"
)

def normalizar(texto):
    """Limpia el texto para comparación."""
    texto = texto.lower().strip()
    texto = texto.translate(REEMPLAZOS_ACENTO)
    texto = re.sub(r"[^\w\s]", "", texto)
    return texto

def buscar(normalizado):
    """Dos estrategias de búsqueda: Match exacto y Palabra clave."""
    if normalizado in BASE:
        return BASE[normalizado], "exacto"
    for clave in BASE:
        if clave in normalizado.split():
            return BASE[clave], "keyword"
    return None, None

def chatbot_s1(mensaje_raw):
    """Procesa un mensaje, busca respuesta y guarda en MongoDB."""
    normalizado = normalizar(mensaje_raw)
    respuesta, metodo = buscar(normalizado)
    
    if respuesta:
        reconocido = True
    else:
        reconocido = False
        respuesta = ("No tengo una respuesta para eso. "
                     "Tu pregunta queda registrada para mejorar el sistema.")
    
    # Guardar en MongoDB con el formato de Fase 2
    guardar_sesion(
        fase="s1",
        usuario_raw=mensaje_raw,
        usuario_norm=normalizado,
        respuesta=respuesta,
        reconocido=recononcido if 'recononcido' in locals() else reconocido, # salvaguarda por typos del pdf
        metodo=metodo or "sin_match"
    )
    return respuesta

if __name__ == "__main__":
    print("Chatbot S1 activo. Escribe 'stats' para ver estadísticas.")
    print("Escribe 'salir' para terminar.\n")
    while True:
        entrada = input("Tú: ").strip()
        if not entrada:
            continue
        if entrada.lower() == "salir":
            stats = estadisticas()
            print(f"\nResumen final: {stats}")
            break
        if entrada.lower() == "stats":
            print(estadisticas())
            continue
        print(f"Bot: {chatbot_s1(entrada)}\n")