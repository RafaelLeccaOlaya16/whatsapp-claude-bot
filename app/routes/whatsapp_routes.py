import traceback
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request

from app.config.configuracion import settings
from app.database.conexion import SessionLocal
from app.services.claude_servicio import generar_respuesta
from app.services.conversacion_servicio import (
    construir_historial,
    guardar_mensaje,
    obtener_o_crear_cliente,
)
from app.services.whatsapp_servicio import descargar_media, enviar_mensaje, imagen_a_base64

router = APIRouter()


@router.get("/webhook")
def verificar_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> int:
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificacion invalido")


def _extraer_mensaje(payload: dict) -> dict | None:
    """
    Extrae los datos del mensaje entrante de Meta, sea texto o imagen.
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
        tipo = mensaje["type"]

        if tipo == "text":
            return {"numero": numero, "tipo": "text", "texto": mensaje["text"]["body"]}

        if tipo == "image":
            return {
                "numero": numero,
                "tipo": "image",
                "media_id": mensaje["image"]["id"],
                "texto": mensaje["image"].get("caption", "El cliente envio una imagen."),
            }

        return None
    except (KeyError, IndexError):
        return None


def _procesar_texto(numero: str, texto: str) -> None:
    """Tarea en segundo plano para mensajes de texto."""
    try:
        db = SessionLocal()
        try:
            cliente = obtener_o_crear_cliente(db, numero)
            guardar_mensaje(db, cliente.id, remitente="cliente", contenido=texto)
            historial = construir_historial(db, cliente.id)
            respuesta = generar_respuesta(historial)
            guardar_mensaje(db, cliente.id, remitente="asistente", contenido=respuesta)
        finally:
            db.close()

        enviar_mensaje(numero, respuesta)
    except Exception as e:
        print(f"❌ Error al procesar mensaje de texto para {numero}: {e}")
        traceback.print_exc()


def _procesar_imagen(numero: str, media_id: str, texto_cliente: str) -> None:
    """Tarea en segundo plano para mensajes de imagen."""
    try:
        print(f"📸 Iniciando procesamiento de imagen (Media ID: {media_id})")
        contenido_binario, mime_type = descargar_media(media_id)
        imagen_base64 = imagen_a_base64(contenido_binario)

        db = SessionLocal()
        try:
            cliente = obtener_o_crear_cliente(db, numero)
            guardar_mensaje(db, cliente.id, remitente="cliente", contenido=f"[Imagen] {texto_cliente}")
            historial = construir_historial(db, cliente.id)
            respuesta = generar_respuesta(historial, imagen_base64=imagen_base64, mime_type=mime_type)
            guardar_mensaje(db, cliente.id, remitente="asistente", contenido=respuesta)
        finally:
            db.close()

        enviar_mensaje(numero, respuesta)
        print(f"✅ Imagen procesada y respuesta enviada con exito a {numero}")
    except Exception as e:
        print(f"❌ Error al procesar imagen para {numero}: {e}")
        traceback.print_exc()


@router.post("/webhook")
async def recibir_mensaje(request: Request, background_tasks: BackgroundTasks) -> dict:
    payload = await request.json()
    datos = _extraer_mensaje(payload)
    print(f"📩 Payload extraido: {datos}")

    if datos is None:
        return {"status": "ignorado"}

    if datos["tipo"] == "text":
        background_tasks.add_task(_procesar_texto, datos["numero"], datos["texto"])
    elif datos["tipo"] == "image":
        background_tasks.add_task(_procesar_imagen, datos["numero"], datos["media_id"], datos["texto"])

    return {"status": "recibido"}