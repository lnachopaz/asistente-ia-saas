import os
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from google.genai import types
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore

# Cargar las variables del archivo .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Validar que las credenciales existan
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not GOOGLE_API_KEY:
    raise ValueError("Error: Faltan configurar las credenciales en el archivo .env")

# Inicializar el cliente oficial de Supabase y el nuevo cliente de Google GenAI
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
client_google = genai.Client(api_key=GOOGLE_API_KEY)

# --- CLASE ADAPTADORA CON LA LIBRERÍA MODERNA DE GOOGLE (2026) ---
class EmbeddingsNativosGoogle:
    """Clase espejo para que LangChain use la NUEVA API de Google sin romper rutas"""
    def embed_documents(self, texts):
        # Usamos el nuevo método de la librería actual de Google
        response = client_google.models.embed_content(
            model="models/gemini-embedding-001", # El modelo activo en tu cuenta
            contents=texts,
        )
        # Extraemos la lista de vectores numéricos de la respuesta
        return [e.values for e in response.embeddings]

    def embed_query(self, text):
        response = client_google.models.embed_content(
            model="models/gemini-embedding-001",
            contents=text,
        )
        return response.embeddings[0].values

def registrar_empresa(nombre: str, whatsapp_num: str) -> str:
    """Registra la empresa en Supabase si no existe."""
    existente = supabase.table("empresas").select("id").eq("whatsapp_num", whatsapp_num).execute()
    
    if existente.data:
        print(f"-> La empresa '{nombre}' ya se encontraba registrada.")
        return existente.data[0]["id"]
    
    print(f"-> Registrando nueva empresa: {nombre}...")
    nueva_empresa = supabase.table("empresas").insert({
        "nombre": nombre,
        "whatsapp_num": whatsapp_num
    }).execute()
    
    return nueva_empresa.data[0]["id"]

def indexar_manual_empresa(empresa_id: str, ruta_archivo: str):
    """Lee el archivo, lo fragmenta y sube los vectores usando el adaptador de 2026."""
    print(f"-> Leyendo el archivo '{ruta_archivo}'...")
    loader = TextLoader(ruta_archivo, encoding="utf-8")
    documento = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    fragmentos = text_splitter.split_documents(documento)
    
    for frag in fragmentos:
        frag.metadata = {"empresa_id": empresa_id}
        
    print(f"-> Generando vectores con la nueva API GenAI para {len(fragmentos)} fragmentos...")
    
    # Usamos nuestro adaptador de 2026
    embeddings_seguros = EmbeddingsNativosGoogle()
    
    # Subir todo a la tabla 'documents' de Supabase
    SupabaseVectorStore(
        client=supabase,
        embedding=embeddings_seguros,
        table_name="documents",
        query_name="match_documents"
    ).add_documents(fragmentos)
    
    print("-> ¡Carga vectorial completada con éxito en Supabase!")

def obtener_empresa_por_numero_wpp(numero_wpp: str) -> str | None:
    """Busca el ID de empresa en Supabase según su número de WhatsApp receptor."""
    resultado = supabase.table("empresas").select("id").eq("whatsapp_num", numero_wpp).execute()
    if resultado.data:
        return resultado.data[0]["id"]
    return None