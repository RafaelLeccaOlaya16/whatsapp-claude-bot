from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.conexion import Base
from app.models.cliente import Cliente


class Mensaje(Base):
    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    remitente: Mapped[str] = mapped_column(String(20), nullable=False)  # "cliente" o "asistente"
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cliente: Mapped["Cliente"] = relationship(back_populates="mensajes")