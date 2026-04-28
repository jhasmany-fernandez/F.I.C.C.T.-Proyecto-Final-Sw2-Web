/**
 * Pantalla de gestión de usuarios del panel admin.
 * Sp1-09 — PB-13 (CA-1, CA-2, CA-3, CA-4).
 */

import { useState } from "react";
import { UserPlus } from "lucide-react";
import { useActualizarUsuario, useUsuarios } from "../hooks/useUsuarios";
import type { UsuarioOut } from "../types";
import UsuarioModal from "../components/UsuarioModal";
import { Badge, Button, EmptyState } from "@/shared/components";
import { useToast } from "@/shared/components";
import { useAuth } from "@/features/auth/hooks/useAuth";
import styles from "./GestionUsuarios.module.css";

export default function GestionUsuarios() {
  const { data: usuarios, isLoading, isError } = useUsuarios();
  const { mutateAsync: actualizar } = useActualizarUsuario();
  const [mostrarModal, setMostrarModal] = useState(false);
  const [usuarioEditar, setUsuarioEditar] = useState<UsuarioOut | null>(null);
  const usuarioActual = useAuth((s) => s.usuario);
  const toast = useToast();

  const toggleActivo = async (usuario: UsuarioOut) => {
    if (usuario.id === usuarioActual?.id) return;
    try {
      await actualizar({ id: usuario.id, datos: { activo: !usuario.activo } });
      toast.exito(
        usuario.activo
          ? `${usuario.nombre} fue desactivado.`
          : `${usuario.nombre} fue activado.`,
      );
    } catch {
      toast.error("No se pudo actualizar el estado del usuario.");
    }
  };

  if (isLoading) {
    return (
      <div className={styles.estadoCentrado}>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className={styles.skeleton} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className={styles.estadoCentrado}>
        <p className={styles.error}>Error al cargar los usuarios.</p>
      </div>
    );
  }

  return (
    <div>
      <div className={styles.encabezado}>
        <div>
          <h1 className={styles.titulo}>Usuarios</h1>
          <p className={styles.subtitulo}>
            Gestione las cuentas de técnicos y administradores.
          </p>
        </div>
        <Button onClick={() => setMostrarModal(true)}>
          <UserPlus size={15} aria-hidden="true" />
          Nuevo técnico
        </Button>
      </div>

      {!usuarios || usuarios.length === 0 ? (
        <EmptyState mensaje="No hay usuarios registrados aún." />
      ) : (
        <div className={styles.tablaWrapper}>
          <table className={styles.tabla}>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Estado</th>
                <th>Creado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id}>
                  <td>{u.nombre}</td>
                  <td>{u.email}</td>
                  <td>
                    <Badge variante={u.rol === "admin" ? "admin" : "tecnico"} />
                  </td>
                  <td>
                    <Badge variante={u.activo ? "activo" : "inactivo"} />
                  </td>
                  <td>{new Date(u.created_at).toLocaleDateString("es-BO")}</td>
                  <td>
                    <div className={styles.acciones}>
                      <Button
                        variante="secondary"
                        tamano="sm"
                        onClick={() => {
                          setUsuarioEditar(u);
                          setMostrarModal(false);
                        }}
                      >
                        Editar
                      </Button>
                      {u.id !== usuarioActual?.id && (
                        <Button
                          variante={u.activo ? "danger" : "secondary"}
                          tamano="sm"
                          onClick={() => toggleActivo(u)}
                        >
                          {u.activo ? "Desactivar" : "Activar"}
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(mostrarModal || usuarioEditar !== null) && (
        <UsuarioModal
          usuarioEditar={usuarioEditar ?? undefined}
          onCerrar={() => {
            setMostrarModal(false);
            setUsuarioEditar(null);
          }}
        />
      )}
    </div>
  );
}
