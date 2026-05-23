import os
from dotenv import load_dotenv
from src.database import registrar_empresa, indexar_manual_empresa

# Cargar entorno
load_dotenv()

def main():
    print("=== INICIANDO PROCESO DE CARGA DE CLIENTE ===")
    
    # Configuración de la empresa de prueba
    nombre_cliente = "Pizzería Don Tomás"
    # El número debe ser continuo: código de país + código de área + número (sin el 15, ni guiones, ni +)
    whatsapp_cliente = "543811234567" 
    archivo_manual = "manual_pizzeria.txt"
    
    # Validaciones previas
    if not os.path.exists(archivo_manual):
        print(f"Error: No se encuentra el archivo '{archivo_manual}' en la raíz del proyecto.")
        return
        
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: Falta la GOOGLE_API_KEY en el archivo .env")
        return

    try:
        # 1. Registrar empresa en la base de datos
        id_empresa = registrar_empresa(nombre_cliente, whatsapp_cliente)
        print(f"-> ID de la empresa asignado: {id_empresa}")
        
        # 2. Subir el manual vectorizado
        indexar_manual_empresa(id_empresa, archivo_manual)
        
        print("\n=== PROCESO FINALIZADO CON ÉXITO ===")
        print("Ya podés revisar las tablas 'empresas' y 'documents' en tu panel web de Supabase.")
        
    except Exception as e:
        print(f"\n❌ Ocurrió un error durante la carga: {e}")

if __name__ == "__main__":
    main()