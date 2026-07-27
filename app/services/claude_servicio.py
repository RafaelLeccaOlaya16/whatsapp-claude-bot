from anthropic import Anthropic
from app.config.configuracion import settings
from app.prompts.catalogo_macles import CATALOGO

SYSTEM_PROMPT = f"""
Eres un asistente de ventas de Macles, una tienda de gorras.
Respondes de forma natural y cercana, como una persona real del equipo de ventas.
Solo hablas de temas relacionados a la tienda: productos, precios, disponibilidad,
pedidos, envios y preguntas frecuentes.
Si te preguntan algo fuera de ese tema, indicas amablemente que no puedes ayudar
con eso y rediriges la conversacion a como puedes ayudar con la tienda.

Usa exclusivamente la siguiente informacion del negocio para responder.
Si te preguntan algo que no esta en esta informacion (por ejemplo, un producto
que no existe en el catalogo), indica que no tienes esa informacion disponible
y ofrece derivar la consulta a un vendedor.

{CATALOGO}
"""


def _respuesta_simulada(historial: list[dict[str, str]]) -> str:
    """Genera una respuesta falsa para pruebas, sin usar la API real."""
    ultimo_mensaje = historial[-1]["content"]
    return f"[MOCK] Recibi tu mensaje: '{ultimo_mensaje}'. Esta es una respuesta simulada."


def _respuesta_real(historial: list[dict], imagen_base64: str | None = None, mime_type: str | None = None) -> str:
    """Envia el historial (y opcionalmente una imagen) a la API real de Claude."""
    client = Anthropic(api_key=settings.anthropic_api_key)

    mensajes = historial.copy()

    if imagen_base64:
        ultimo = mensajes[-1]
        mensajes[-1] = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": imagen_base64,
                    },
                },
                {"type": "text", "text": ultimo["content"]},
            ],
        }

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=mensajes,
    )
    return response.content[0].text


def generar_respuesta(historial: list[dict], imagen_base64: str | None = None, mime_type: str | None = None) -> str:
    """
    Punto de entrada unico del servicio. Decide si usar modo mock o real.
    Si se provee imagen_base64, se incluye en el mensaje para que Claude la analice.
    """
    if settings.claude_mock_mode:
        return _respuesta_simulada(historial)
    return _respuesta_real(historial, imagen_base64, mime_type)