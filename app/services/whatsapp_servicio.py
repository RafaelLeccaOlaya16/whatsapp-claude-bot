import httpx

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