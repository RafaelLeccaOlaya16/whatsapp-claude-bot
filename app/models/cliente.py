from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.conexion import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_whatsapp: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mensajes: Mapped[list["Mensaje"]] = relationship(back_populates="cliente", order_by="Mensaje.creado_en")
