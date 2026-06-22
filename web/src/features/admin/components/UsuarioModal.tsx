/**
 * Modal para crear o editar un usuario.
 * Sp1-09 — PB-13 (CA-1, CA-3, CA-5).
 */

import { useState } from "react";
import { X } from "lucide-react";
import { useActualizarUsuario, useCrearUsuario } from "../hooks/useUsuarios";
import type { UsuarioCreate, UsuarioOut, UsuarioUpdate } from "../types";
import { Button } from "@/shared/components";
import { useToast } from "@/shared/components";
import styles from "./UsuarioModal.module.css";

interface Props {
  usuarioEditar?: UsuarioOut;
  onCerrar: () => void;
}

export default function UsuarioModal({ usuarioEditar, onCerrar }: Props) {
  const esEdicion = !!usuarioEditar;
  const [form, setForm] = useState({
    nombre: usuarioEditar?.nombre ?? "",
    email: usuarioEditar?.email ?? "",
    password: "",
    rol: usuarioEditar?.rol ?? "tecnico",
  });
  const [errLocal, setErrLocal] = useState<string | null>(null);
  const { mutateAsync: crear, isPending: creando } = useCrearUsuario();
  const { mutateAsync: actualizar, isPending: actualizando } =
    useActualizarUsuario();
  const isPending = creando || actualizando;
  const toast = useToast();

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrLocal(null);

    if (esEdicion) {
      if (!form.nombre.trim() || !form.email.trim()) {
        setErrLocal("Nombre y correo son obligatorios.");
        return;
      }
      if (form.password && form.password.length < 8) {
        setErrLocal("La contraseña debe tener al menos 8 caracteres.");
        return;
      }
      const datos: UsuarioUpdate = {
        nombre: form.nombre.trim(),
        email: form.email.trim(),
        rol: form.rol as "admin" | "tecnico",
      };
      if (form.password) datos.password = form.password;
      try {
        await actualizar({ id: usuarioEditar!.id, datos });
        toast.exito("Usuario actualizado correctamente.");
        onCerrar();
      } catch (err: unknown) {
        setErrLocal(_extraerDetalle(err) ?? "Error al actualizar el usuario.");
      }
    } else {
      if (!form.nombre.trim() || !form.email.trim() || !form.password) {
        setErrLocal("Todos los campos son obligatorios.");
        return;
      }
      if (form.password.length < 8) {
        setErrLocal("La contraseña debe tener al menos 8 caracteres.");
        return;
      }
      try {
        await crear(form as UsuarioCreate);
        toast.exito("Usuario creado correctamente.");
        onCerrar();
      } catch (err: unknown) {
        const detail = _extraerDetalle(err);
        setErrLocal(detail ?? "Error al crear el usuario.");
      }
    }
  };

  return (
    <div className={styles.overlay} role="dialog" aria-modal="true">
      <div className={styles.modal}>
        <header className={styles.header}>
          <h2>{esEdicion ? "Editar usuario" : "Nuevo técnico"}</h2>
          <button
            onClick={onCerrar}
            className={styles.cerrar}
            aria-label="Cerrar"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          {errLocal && (
            <div className={styles.alerta} role="alert">
              {errLocal}
            </div>
          )}

          <label htmlFor="nombre">Nombre completo</label>
          <input
            id="nombre"
            name="nombre"
            type="text"
            value={form.nombre}
            onChange={handleChange}
            disabled={isPending}
            required
          />

          <label htmlFor="email">Correo electrónico</label>
          <input
            id="email"
            name="email"
            type="email"
            value={form.email}
            onChange={handleChange}
            disabled={isPending}
            required
          />

          <label htmlFor="password">
            {esEdicion ? "Nueva contraseña (opcional)" : "Contraseña inicial"}
          </label>
          <input
            id="password"
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            disabled={isPending}
            minLength={8}
            placeholder={esEdicion ? "Dejar en blanco para no cambiar" : ""}
            required={!esEdicion}
          />

          <label htmlFor="rol">Rol</label>
          <select
            id="rol"
            name="rol"
            value={form.rol}
            onChange={handleChange}
            disabled={isPending}
          >
            <option value="tecnico">Técnico de campo</option>
            <option value="admin">Administrador</option>
          </select>

          <footer className={styles.footer}>
            <Button
              type="button"
              variante="secondary"
              onClick={onCerrar}
              disabled={isPending}
            >
              Cancelar
            </Button>
            <Button type="submit" isLoading={isPending}>
              {esEdicion ? "Guardar cambios" : "Crear cuenta"}
            </Button>
          </footer>
        </form>
      </div>
    </div>
  );
}

function _extraerDetalle(err: unknown): string | null {
  if (
    typeof err === "object" &&
    err !== null &&
    "response" in err &&
    typeof (err as { response?: { data?: { detail?: string } } }).response?.data
      ?.detail === "string"
  ) {
    return (err as { response: { data: { detail: string } } }).response.data
      .detail;
  }
  return null;
}
