import httpx
import base64

from app.config.configuracion import settings

WHATSAPP_API_URL = f"https://graph.facebook.com/v21.0/{settings.whatsapp_phone_number_id}/messages"


def enviar_mensaje(numero_destino: str, texto: str) -> dict:
    """
    Envia un mensaje de texto a un numero de WhatsApp usando la Cloud API de Meta.

    Devuelve la respuesta de la API como diccionario (util para logs o depuracion).
    """
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": texto},
    }

    response = httpx.post(WHATSAPP_API_URL, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


def descargar_media(media_id: str) -> tuple[bytes, str]:
    """
    Descarga un archivo multimedia de WhatsApp (imagen, audio, etc.) usando su ID.

    Proceso de dos pasos, segun la Cloud API de Meta:
    1. Pedir la URL temporal de descarga usando el media_id.
    2. Descargar el archivo real desde esa URL.

    Devuelve (contenido_binario, mime_type).
    """
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}

    # Paso 1: obtener la URL temporal
    info_url = f"https://graph.facebook.com/v21.0/{media_id}"
    info_response = httpx.get(info_url, headers=headers)
    info_response.raise_for_status()
    info = info_response.json()

    url_descarga = info["url"]
    mime_type = info["mime_type"]

    # Paso 2: descargar el archivo real desde esa URL
    archivo_response = httpx.get(url_descarga, headers=headers)
    archivo_response.raise_for_status()

    return archivo_response.content, mime_type


def imagen_a_base64(contenido: bytes) -> str:
    """Convierte bytes de una imagen a un string base64 (formato que espera Claude)."""
    return base64.b64encode(contenido).decode("utf-8")