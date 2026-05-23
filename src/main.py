import os
import httpx
from fastapi import FastAPI, Request, Response, Query
from src.chatbot import responder_consulta
from src.database import obtener_empresa_por_numero_wpp

app = FastAPI(title="SaaS WhatsApp AI Bot")

TOKEN_VERIFICACION = os.getenv("TOKEN_VERIFICACION", "MiTokenSecreto123_DonTomas")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


async def enviar_mensaje_whatsapp(numero_destino: str, mensaje: str):
    """Envía un mensaje de texto al cliente a través de la API de Meta."""
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": mensaje}
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()


@app.get("/")
def inicio():
    return {"estado": "Servidor funcionando correctamente"}


@app.get("/webhook")
def verificar_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Ruta obligatoria para Meta: verifica que el servidor sea legítimo."""
    if hub_mode == "subscribe" and hub_challenge:
        if hub_verify_token == TOKEN_VERIFICACION:
            print("-> ¡Webhook verificado por Meta con éxito!")
            return Response(content=hub_challenge, media_type="text/plain")
        else:
            return Response(content="Token de verificación inválido", status_code=403)
    return Response(content="Parámetros inválidos", status_code=400)


@app.post("/webhook")
async def recibir_mensaje_whatsapp(request: Request):
    """Recibe mensajes entrantes de WhatsApp, genera respuesta con IA y la envía de vuelta."""
    try:
        payload = await request.json()

        print("\n================ PAYLOAD RECIBIDO DE META ================")
        print(payload)
        print("==========================================================\n")

        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return Response(status_code=200)

        msg = messages[0]

        # Ignorar mensajes que no sean texto (imágenes, audio, documentos, etc.)
        if msg.get("type") != "text":
            print(f"-> Mensaje de tipo '{msg.get('type')}' ignorado.")
            return Response(status_code=200)

        telefono_cliente = msg.get("from")
        texto_usuario = msg.get("text", {}).get("body", "")
        numero_empresa_receptor = value.get("metadata", {}).get("display_phone_number", "")

        print(f"-> Mensaje entrante desde WhatsApp!")
        print(f"   Para empresa (número): {numero_empresa_receptor}")
        print(f"   Cliente ({telefono_cliente}): {texto_usuario}")

        # Buscar la empresa en Supabase por su número de WhatsApp
        empresa_id = obtener_empresa_por_numero_wpp(numero_empresa_receptor)

        if not empresa_id:
            print(f"-> AVISO: Empresa con número '{numero_empresa_receptor}' no encontrada en Supabase. Mensaje ignorado.")
            return Response(status_code=200)

        # Generar respuesta con IA
        respuesta_ia = responder_consulta(empresa_id, telefono_cliente, texto_usuario)
        print(f"   Respuesta generada: {respuesta_ia}")

        # Enviar la respuesta de vuelta al cliente por WhatsApp
        await enviar_mensaje_whatsapp(telefono_cliente, respuesta_ia)
        print(f"   -> Respuesta enviada con éxito a {telefono_cliente}")

        return Response(status_code=200)

    except Exception as e:
        print(f"❌ Error al procesar el webhook: {e}")
        return Response(status_code=200)  # Siempre 200 para que Meta no reintente
