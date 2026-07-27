import json
import logging
import traceback
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request

from app.config.configuracion import settings
from app.database.conexion import SessionLocal
from app.services.claude_servicio import generar_respuesta
from app.services.conversacion_servicio import (
    cambiar_modo_atencion,
    construir_historial,
    guardar_mensaje,
    obtener_o_crear_cliente,
)
from app.services.whatsapp_servicio import descargar_media, enviar_mensaje, imagen_a_base64

# Configurar el logger nativo compatible con Uvicorn/FastAPI
logger = logging.getLogger("uvicorn.error")

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
    try:
        entry = payload.get("entry", [])[0]
        cambio = entry.get("changes", [])[0]
        valor = cambio.get("value", {})
        mensajes = valor.get("messages")

        if not mensajes:
            return None

        mensaje = mensajes[0]
        numero = mensaje.get("from")
        tipo = mensaje.get("type")

        logger.info(f"🔍 Deteccion de mensaje -> Tipo: '{tipo}', De: {numero}")

        if tipo == "text":
            return {"numero": numero, "tipo": "text", "texto": mensaje["text"]["body"]}

        if tipo == "image":
            return {
                "numero": numero,
                "tipo": "image",
                "media_id": mensaje["image"]["id"],
                "texto": mensaje["image"].get("caption", "El cliente envio una imagen."),
            }

        if tipo in ["audio", "voice"]:
            return {
                "numero": numero,
                "tipo": "audio",
                "media_id": mensaje[tipo]["id"]
            }

        logger.warning(f"⚠️ Tipo de mensaje recibido no configurado: '{tipo}'")
        return None
    except Exception as e:
        logger.error(f"❌ Error interno dentro de _extraer_mensaje: {e}")
        logger.error(traceback.format_exc())
        return None


def _procesar_texto(numero: str, texto: str) -> None:
    try:
        db = SessionLocal()
        try:
            cliente = obtener_o_crear_cliente(db, numero)

            # --- COMANDOS DEL ASESOR HUMANO ---
            if texto.strip().lower() in ["/bot", "!bot"]:
                cambiar_modo_atencion(db, cliente.id, "IA")
                guardar_mensaje(db, cliente.id, remitente="asistente", contenido="[Control devuelto a la IA]")
                enviar_mensaje(numero, "🤖 *IA Reactivada:* A partir de ahora el asistente virtual continuará atendiendo este chat.")
                return

            if texto.strip().lower() in ["/humano", "!humano"]:
                cambiar_modo_atencion(db, cliente.id, "HUMANO")
                guardar_mensaje(db, cliente.id, remitente="asistente", contenido="[Chat derivado a Humano]")
                enviar_mensaje(numero, "👤 *Atención Humana:* Un asesor ha tomado el control de la conversación.")
                return

            # --- VERIFICACIÓN DE MODO ---
            if cliente.modo_atencion == "HUMANO":
                logger.info(f"👤 Cliente {numero} en modo HUMANO. Guardando mensaje sin respuesta de IA.")
                guardar_mensaje(db, cliente.id, remitente="cliente", contenido=texto)
                return

            # --- FLUJO NORMAL DE IA ---
            guardar_mensaje(db, cliente.id, remitente="cliente", contenido=texto)
            historial = construir_historial(db, cliente.id)
            respuesta = generar_respuesta(historial)
            guardar_mensaje(db, cliente.id, remitente="asistente", contenido=respuesta)
        finally:
            db.close()

        enviar_mensaje(numero, respuesta)
    except Exception as e:
        logger.error(f"❌ Error en _procesar_texto: {e}")
        logger.error(traceback.format_exc())


def _procesar_imagen(numero: str, media_id: str, texto_cliente: str) -> None:
    try:
        db = SessionLocal()
        try:
            cliente = obtener_o_crear_cliente(db, numero)

            # --- VERIFICACIÓN DE MODO ---
            if cliente.modo_atencion == "HUMANO":
                logger.info(f"👤 Cliente {numero} en modo HUMANO. Guardando imagen sin respuesta de IA.")
                guardar_mensaje(db, cliente.id, remitente="cliente", contenido=f"[Imagen] {texto_cliente}")
                return

            logger.info(f"📸 Descargando imagen desde Meta (Media ID: {media_id})...")
            contenido_binario, mime_type = descargar_media(media_id)
            logger.info(f"✅ Descargados {len(contenido_binario)} bytes. MimeType: {mime_type}")

            imagen_base64 = imagen_a_base64(contenido_binario)

            guardar_mensaje(db, cliente.id, remitente="cliente", contenido=f"[Imagen] {texto_cliente}")
            historial = construir_historial(db, cliente.id)
            respuesta = generar_respuesta(historial, imagen_base64=imagen_base64, mime_type=mime_type)
            guardar_mensaje(db, cliente.id, remitente="asistente", contenido=respuesta)
        finally:
            db.close()

        enviar_mensaje(numero, respuesta)
        logger.info(f"✅ Respuesta para imagen enviada con exito a {numero}")
    except Exception as e:
        logger.error(f"❌ Error en _procesar_imagen: {e}")
        logger.error(traceback.format_exc())


def _procesar_audio(numero: str) -> None:
    try:
        logger.info(f"🎙️ Audio recibido de {numero}. Activando modo HUMANO...")
        
        db = SessionLocal()
        try:
            cliente = obtener_o_crear_cliente(db, numero)
            # 1. Cambiamos el modo a HUMANO
            cambiar_modo_atencion(db, cliente.id, "HUMANO")
            
            # 2. Registramos el evento en el historial
            guardar_mensaje(
                db, 
                cliente.id, 
                remitente="cliente", 
                contenido="[Nota de voz recibida - Derivado a asesor humano]"
            )
        finally:
            db.close()

        # 3. Notificamos al cliente que un humano tomará su caso
        mensaje_notificacion = (
            "¡Hola! 👋 Hemos recibido tu nota de voz. "
            "En breve un asesor de nuestro equipo la escuchará y te responderá por este medio."
        )
        enviar_mensaje(numero, mensaje_notificacion)
        logger.info(f"✅ Notificación de audio enviada a {numero}")

    except Exception as e:
        logger.error(f"❌ Error en _procesar_audio: {e}")
        logger.error(traceback.format_exc())


@router.post("/webhook")
async def recibir_mensaje(request: Request, background_tasks: BackgroundTasks) -> dict:
    payload = await request.json()

    logger.info("==========================================")
    logger.info("📩 JSON COMPLETO RECIBIDO DE META:")
    logger.info(json.dumps(payload, indent=2))
    logger.info("==========================================")

    datos = _extraer_mensaje(payload)

    if datos is None:
        logger.info("⚠️ El mensaje fue ignorado por _extraer_mensaje() (posiblemente una notificacion de estado).")
        return {"status": "ignorado"}

    logger.info(f"🚀 Procesando mensaje de tipo '{datos['tipo']}'")

    if datos["tipo"] == "text":
        background_tasks.add_task(_procesar_texto, datos["numero"], datos["texto"])
    elif datos["tipo"] == "image":
        background_tasks.add_task(_procesar_imagen, datos["numero"], datos["media_id"], datos["texto"])
    elif datos["tipo"] == "audio":
        background_tasks.add_task(_procesar_audio, datos["numero"])

    return {"status": "recibido"}

