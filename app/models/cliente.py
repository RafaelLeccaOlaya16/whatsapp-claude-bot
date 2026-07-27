from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.conexion import Base

if TYPE_CHECKING:
    from app.models.mensaje import Mensaje


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_whatsapp: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Nuevo campo para controlar si atiende la IA o un Asesor Humano ("IA" / "HUMANO")
    modo_atencion: Mapped[str] = mapped_column(String(10), default="IA", nullable=False)
    
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mensajes: Mapped[List["Mensaje"]] = relationship(
        back_populates="cliente", 
        order_by="Mensaje.creado_en"
    )