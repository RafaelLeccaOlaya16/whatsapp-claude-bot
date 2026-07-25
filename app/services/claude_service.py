from anthropic import Anthropic

from app.config.settings import settings

SYSTEM_PROMPT = (
    "Eres un asistente de ventas de una tienda de gorras. "
    "Respondes de forma natural y cercana, como una persona real del equipo de ventas. "
    "Solo hablas de temas relacionados a la tienda: productos, precios, disponibilidad, "
    "pedidos, envios y preguntas frecuentes. "
    "Si te preguntan algo fuera de ese tema, indicas amablemente que no puedes ayudar "
    "con eso y rediriges la conversacion a como puedes ayudar con la tienda."
)


def _respuesta_simulada(mensaje: str) -> str:
    """Genera una respuesta falsa para pruebas, sin usar la API real."""
    return f"[MOCK] Recibi tu mensaje: '{mensaje}'. Esta es una respuesta simulada."


def _respuesta_real(mensaje: str) -> str:
    """Envia el mensaje a la API real de Claude y devuelve su respuesta."""
    client = Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": mensaje}],
    )

    return response.content[0].text


def generar_respuesta(mensaje: str) -> str:
    """Punto de entrada unico del servicio. Decide si usar modo mock o real."""
    if settings.claude_mock_mode:
        return _respuesta_simulada(mensaje)

    return _respuesta_real(mensaje)
