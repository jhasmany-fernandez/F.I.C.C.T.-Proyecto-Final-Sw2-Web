"""Repositorio de acceso a datos para la entidad Usuario.

PB-13 — Sprint 1 (Sp1-03).
"""

from sqlalchemy.orm import Session

from app.models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def crear(
        self,
        nombre: str,
        email: str,
        password_hash: str,
        rol: str,
    ) -> Usuario:
        usuario = Usuario(
            nombre=nombre,
            email=email,
            password_hash=password_hash,
            rol=rol,
        )
        self._db.add(usuario)
        self._db.commit()
        self._db.refresh(usuario)
        return usuario

    def obtener_por_email(self, email: str) -> Usuario | None:
        return self._db.query(Usuario).filter(Usuario.email == email).first()

    def obtener_por_id(self, usuario_id: int) -> Usuario | None:
        return self._db.query(Usuario).filter(Usuario.id == usuario_id).first()

    def listar(self, solo_activos: bool = False) -> list[Usuario]:
        q = self._db.query(Usuario)
        if solo_activos:
            q = q.filter(Usuario.activo.is_(True))
        return q.order_by(Usuario.created_at.desc()).all()

    def guardar(self, usuario: Usuario) -> Usuario:
        self._db.commit()
        self._db.refresh(usuario)
        return usuario
