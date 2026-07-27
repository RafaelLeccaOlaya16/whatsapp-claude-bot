from sqlalchemy.orm import Session

from app.config.configuracion import settings
from app.database.conexion import SessionLocal
from app.models.cliente import Cliente
from app.models.mensaje import Mensaje
from app.services.claude_servicio import generar_respuesta


def obtener_o_crear_cliente(db: Session, numero_whatsapp: str) -> Cliente:
    """Busca un cliente por su numero de WhatsApp. Si no existe, lo crea."""
    cliente = db.query(Cliente).filter(Cliente.numero_whatsapp == numero_whatsapp).first()

    if cliente is None:
        cliente = Cliente(numero_whatsapp=numero_whatsapp)
        db.add(cliente)
        db.commit()
        db.refresh(cliente)

    return cliente


def guardar_mensaje(db: Session, cliente_id: int, remitente: str, contenido: str) -> Mensaje:
    """Guarda un mensaje en la base de datos, asociado a un cliente."""
    mensaje = Mensaje(cliente_id=cliente_id, remitente=remitente, contenido=contenido)
    db.add(mensaje)
    db.commit()
    db.refresh(mensaje)
    return mensaje


def construir_historial(db: Session, cliente_id: int) -> list[dict[str, str]]:
    """Arma el historial reciente de un cliente en el formato que espera Claude."""
    mensajes = (
        db.query(Mensaje)
        .filter(Mensaje.cliente_id == cliente_id)
        .order_by(Mensaje.creado_en.desc())
        .limit(settings.limite_historial_mensajes)
        .all()
    )

    mensajes.reverse()  # queremos orden cronologico: mas antiguo primero

    historial = []
    for m in mensajes:
        rol = "user" if m.remitente == "cliente" else "assistant"
        historial.append({"role": rol, "content": m.contenido})

    return historial


def procesar_mensaje_entrante(numero_whatsapp: str, texto: str) -> str:
    """
    Punto de entrada unico del servicio de conversacion.

    Recibe el numero de WhatsApp del cliente y el texto que escribio.
    Devuelve la respuesta generada por el asistente.
    """
    db = SessionLocal()

    try:
        cliente = obtener_o_crear_cliente(db, numero_whatsapp)

        guardar_mensaje(db, cliente.id, remitente="cliente", contenido=texto)

        historial = construir_historial(db, cliente.id)

        respuesta = generar_respuesta(historial)

        guardar_mensaje(db, cliente.id, remitente="asistente", contenido=respuesta)

        return respuesta
    finally:
        db.close()