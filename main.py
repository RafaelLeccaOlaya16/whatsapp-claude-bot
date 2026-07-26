from fastapi import FastAPI

from app.routes.whatsapp_routes import router as whatsapp_router

app = FastAPI(title="WhatsApp Claude Bot")

app.include_router(whatsapp_router)


@app.get("/")
def inicio() -> dict:
    """Endpoint simple para confirmar que el servidor esta corriendo."""
    return {"mensaje": "El servidor esta funcionando correctamente"}