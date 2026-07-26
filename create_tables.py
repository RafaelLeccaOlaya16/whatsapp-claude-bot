from app.database.conexion import Base, engine
import app.models  # noqa: F401  (necesario para registrar los modelos)


def main() -> None:
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("Listo. Tablas creadas (o ya existentes).")


if __name__ == "__main__":
    main()