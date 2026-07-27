from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request

from app.config.configuracion import settings
from app.services.conversacion_servicio import procesar_mensaje_entrante
from app.services.whatsapp_servicio import enviar_mensaje

router = APIRouter()


@router.get("/webhook")
def verificar_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> int:
    """
    Meta llama a este endpoint (GET) una sola vez, para verificar que el webhook
    es legitimo. Debemos devolver 'hub_challenge' si el token coincide.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)

    raise HTTPException(status_code=403, detail="Token de verificacion invalido")


def _extraer_mensaje(payload: dict) -> tuple[str, str] | None:
    """
    Intenta extraer (numero_remitente, texto) del payload que manda Meta.
    Devuelve None si el payload no contiene un mensaje de texto valido.
    """
    try:
        entry = payload["entry"][0]
        cambio = entry["changes"][0]
        valor = cambio["value"]
        mensajes = valor.get("messages")

        if not mensajes:
            return None

        mensaje = mensajes[0]
        numero = mensaje["from"]
        texto = mensaje["text"]["body"]

        return numero, texto
    except (KeyError, IndexError):
        return None


def _procesar_y_responder(numero: str, texto: str) -> None:
    """
    Tarea en segundo plano: procesa el mensaje y envia la respuesta por WhatsApp.
    Se ejecuta DESPUES de que Meta ya recibio el 200 OK, por lo que no bloquea
    la respuesta al webhook ni provoca reintentos de Meta por demora.
    """
    respuesta = procesar_mensaje_entrante(numero, texto)
    enviar_mensaje(numero, respuesta)


@router.post("/webhook")
async def recibir_mensaje(request: Request, background_tasks: BackgroundTasks) -> dict:
    """
    Meta llama a este endpoint (POST) cada vez que ocurre un evento.
    Responde inmediatamente con 200 OK, y procesa el mensaje en segundo plano.
    """
    payload = await request.json()

    datos = _extraer_mensaje(payload)

    if datos is None:
        return {"status": "ignorado"}

    numero, texto = datos

    background_tasks.add_task(_procesar_y_responder, numero, texto)

    return {"status": "recibido"}