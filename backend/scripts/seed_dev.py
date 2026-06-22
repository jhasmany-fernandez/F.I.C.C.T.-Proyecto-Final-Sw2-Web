"""seed_dev.py — Inserta usuarios, clientes y proyectos de prueba para desarrollo local.

Solo debe ejecutarse en entornos de desarrollo (DEBUG=true).
Idempotente: no duplica registros si ya existen.

Usuarios creados:
  admin@bulldogtech.bo   / Admin2026!    rol: admin
  tecnico@bulldogtech.bo / Tecnico2026!  rol: tecnico

Clientes de prueba:
  Bulldog Tech.
  Cliente Beta S.A.

Proyectos de prueba:
  3 proyectos asignados al técnico demo (Sprint 1 — PB-18, PB-19 seed data)
"""

import os
import sys

# Guardia: solo corre en modo debug / desarrollo
if os.getenv("DEBUG", "false").lower() != "true":
    print("[seed_dev] No estoy en modo DEBUG — omitiendo seed.")
    sys.exit(0)

import bcrypt

from app.core.database import SessionLocal  # noqa: E402
from app.models.cliente import Cliente  # noqa: E402
from app.models.proyecto import Proyecto  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402

USUARIOS_PRUEBA = [
    {
        "nombre": "Administrador",
        "email": "admin@bulldogtech.bo",
        "password": "Admin2026!",
        "rol": "admin",
    },
    {
        "nombre": "Técnico Demo",
        "email": "tecnico@bulldogtech.bo",
        "password": "Tecnico2026!",
        "rol": "tecnico",
    },
]

CLIENTES_PRUEBA = [
    "Bulldog Tech.",
    "Cliente Beta S.A.",
]

PROYECTOS_PRUEBA = [
    {
        "nombre": "Oficinas Central Bulldog Tech.",
        "cliente": "Bulldog Tech.",
        "estado": "en_progreso",
    },
    {"nombre": "Sucursal Norte", "cliente": "Bulldog Tech.", "estado": "completado"},
    {
        "nombre": "Almacén Logístico",
        "cliente": "Cliente Beta S.A.",
        "estado": "en_progreso",
    },
]


def seed() -> None:
    with SessionLocal() as db:
        # Usuarios
        for datos in USUARIOS_PRUEBA:
            existe = db.query(Usuario).filter_by(email=datos["email"]).first()
            if existe:
                print(f"[seed_dev] Ya existe: {datos['email']} — omitido.")
                continue
            usuario = Usuario(
                nombre=datos["nombre"],
                email=datos["email"],
                password_hash=bcrypt.hashpw(
                    datos["password"].encode(), bcrypt.gensalt()
                ).decode(),
                rol=datos["rol"],
                activo=True,
            )
            db.add(usuario)
            print(f"[seed_dev] Creado: {datos['email']} (rol={datos['rol']})")
        db.commit()

        # Clientes (PB-19)
        clientes_map: dict[str, int] = {}
        for nombre in CLIENTES_PRUEBA:
            cliente = db.query(Cliente).filter_by(nombre=nombre).first()
            if not cliente:
                cliente = Cliente(nombre=nombre)
                db.add(cliente)
                db.flush()
                print(f"[seed_dev] Cliente creado: {nombre}")
            else:
                print(f"[seed_dev] Ya existe cliente: {nombre} — omitido.")
            clientes_map[nombre] = cliente.id
        db.commit()

        # Proyectos (asignados al técnico demo)
        tecnico = db.query(Usuario).filter_by(email="tecnico@bulldogtech.bo").first()
        if tecnico:
            proyectos_existentes = (
                db.query(Proyecto).filter_by(tecnico_id=tecnico.id).count()
            )
            if proyectos_existentes == 0:
                for datos in PROYECTOS_PRUEBA:
                    proyecto = Proyecto(
                        nombre=datos["nombre"],
                        cliente_id=clientes_map.get(datos["cliente"]),
                        estado=datos["estado"],
                        tecnico_id=tecnico.id,
                    )
                    db.add(proyecto)
                    print(f"[seed_dev] Proyecto creado: {datos['nombre']}")
                db.commit()

    print("[seed_dev] Seed completado.")


if __name__ == "__main__":
    seed()
