import os
from google import genai
from src.database import supabase, EmbeddingsNativosGoogle
from google.genai import types

# Inicializar el cliente de Google para la IA
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client_google = genai.Client(api_key=GOOGLE_API_KEY)

def obtener_historial_chat(empresa_id: str, cliente_telefono: str, limite: int = 5) -> str:
    """Recupera los últimos mensajes de este cliente con esta empresa para darle memoria al bot"""
    historial_data = supabase.table("historial_chats") \
        .select("mensaje_usuario, respuesta_bot") \
        .eq("empresa_id", empresa_id) \
        .eq("cliente_telefono", cliente_telefono) \
        .order("created_at", desc=True) \
        .limit(limite) \
        .execute()
    
    # Formatear el historial de forma cronológica (del más viejo al más nuevo)
    string_historial = ""
    for chat in reversed(historial_data.data):
        string_historial += f"Cliente: {chat['mensaje_usuario']}\nBot: {chat['respuesta_bot']}\n"
    
    return string_historial

def guardar_interaccion_chat(empresa_id: str, cliente_telefono: str, mensaje: str, respuesta: str):
    """Guarda la conversación actual en Supabase para que sirva de memoria en el próximo mensaje"""
    supabase.table("historial_chats").insert({
        "empresa_id": empresa_id,
        "cliente_telefono": cliente_telefono,
        "mensaje_usuario": mensaje,
        "respuesta_bot": respuesta
    }).execute()

def responder_consulta(empresa_id: str, cliente_telefono: str, pregunta_usuario: str) -> str:
    """Proceso RAG completo con memoria y aislamiento de datos para responder por WhatsApp"""
    
    # 1. Obtener la memoria de la conversación
    historial = obtener_historial_chat(empresa_id, cliente_telefono)
    
    # 2. Generar el vector de la pregunta del usuario usando nuestro adaptador
    adaptador_embeddings = EmbeddingsNativosGoogle()
    query_vector = adaptador_embeddings.embed_query(pregunta_usuario)
    
    # 3. Buscar información relevante en Supabase (Filtrado estricto por Empresa)
    # Llamamos a la función RPC 'match_documents' que creamos con SQL
    rpc_response = supabase.rpc("match_documents", {
        "query_embedding": query_vector,
        "match_threshold": 0.3, # Nivel de similitud mínima (30%)
        "match_count": 3,       # Traer los 3 fragmentos más parecidos
        "filter": {"empresa_id": empresa_id} # AISLAMIENTO DE DATOS
    }).execute()
    
    contexto_empresa = "\n".join([doc["content"] for doc in rpc_response.data])
    
    # 4. Definir las instrucciones de comportamiento (Prompt)
    system_instruction = """Eres un asistente de atención al cliente de WhatsApp altamente eficiente y cordial.
    Tu objetivo es responder de manera clara, concisa y profesional basándote ÚNICAMENTE en el CONTEXTO DE LA EMPRESA provisto.
    Usa el HISTORIAL DE LA CONVERSACIÓN para mantener la coherencia si el cliente hace referencia a cosas que dijo antes (como 'y cuánto cuesta esa?').
    Si la información para responder la pregunta no está en el contexto, di amablemente que no posees esa información y ofrece comunicar al cliente con un agente humano. ¡NO INVENTES DATOS BAJO NINGUNA CIRCUNSTANCIA!"""

    prompt_final = f"""
    CONTEXTO DE LA EMPRESA:
    {contexto_empresa}

    HISTORIAL RECIENTE DE LA CHARLA:
    {historial}

    NUEVO MENSAJE DEL CLIENTE:
    {pregunta_usuario}
    """

    # 5. Llamar a Gemini usando el modelo estándar actual de 2026
    response = client_google.models.generate_content(
        model="gemini-2.5-flash", # <--- CAMBIAMOS A VERSIÓN 2.5 FLASH
        contents=prompt_final,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0
        )
    )
    
    respuesta_bot = response.text
    
    # 6. Registrar la nueva charla en la base de datos para actualizar la memoria
    guardar_interaccion_chat(empresa_id, cliente_telefono, pregunta_usuario, respuesta_bot)
    
    return respuesta_bot

# --- BLOQUE DE PRUEBA LOCAL EN CONSOLA ---
if __name__ == "__main__":
    # Usamos los datos reales que ya guardamos en el paso anterior
    ID_PIZZERIA = "9b67b96f-99f1-4022-b872-f50b97641c4f"
    TELEFONO_TEST = "543819999999" # Simulamos un cliente
    
    print("=== MOTOR DEL CHATBOT ACTIVO (Simulación en Consola) ===")
    print("Escribí tu consulta para la pizzería. Escribí 'salir' para terminar.\n")
    
    while True:
        consulta = input("Cliente: ")
        if consulta.lower() == 'salir':
            break
        if consulta.strip() == "":
            continue
            
        respuesta = responder_consulta(ID_PIZZERIA, TELEFONO_TEST, consulta)
        print(f"Bot IA: {respuesta}\n")