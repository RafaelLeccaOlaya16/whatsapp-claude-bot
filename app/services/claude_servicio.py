from anthropic import Anthropic

from app.config.configuracion import settings

SYSTEM_PROMPT = (
    "Eres un asistente de ventas de una tienda de gorras y lentes. "
    "Respondes de forma natural y cercana, como una persona real del equipo de ventas. "
    "Solo hablas de temas relacionados a la tienda: productos, precios, disponibilidad, "
    "pedidos, envios y preguntas frecuentes. "
    "Si te preguntan algo fuera de ese tema, indicas amablemente que no puedes ayudar "
    "con eso y rediriges la conversacion a como puedes ayudar con la tienda."
)


def _respuesta_simulada(historial: list[dict[str, str]]) -> str:
    """Genera una respuesta falsa para pruebas, sin usar la API real."""
    ultimo_mensaje = historial[-1]["content"]
    return f"[MOCK] Recibi tu mensaje: '{ultimo_mensaje}'. Esta es una respuesta simulada."


def _respuesta_real(historial: list[dict[str, str]]) -> str:
    """Envia el historial completo a la API real de Claude y devuelve su respuesta."""
    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=historial,
    )
    return response.content[0].text


def generar_respuesta(historial: list[dict[str, str]]) -> str:
    """
    Punto de entrada unico del servicio. Decide si usar modo mock o real.

    `historial` debe ser una lista de mensajes en formato:
    [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    """
    if settings.claude_mock_mode:
        return _respuesta_simulada(historial)
    return _respuesta_real(historial)