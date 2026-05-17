/**
 * Página de gestión de clientes del panel admin.
 * Sp1-35 — PB-19 (CA-1, CA-2, CA-3, CA-4, CA-5).
 */

import { useState } from "react";
import { Building2 } from "lucide-react";
import {
  useActualizarCliente,
  useClientes,
  useCrearCliente,
  useDesactivarCliente,
} from "../hooks/useClientes";
import type { ClienteOut } from "../types";
import { Badge, Button, ConfirmDialog, EmptyState } from "@/shared/components";
import { useToast } from "@/shared/components";
import styles from "./GestionClientes.module.css";

function extraerDetalleError(err: unknown): string | null {
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

export default function GestionClientes() {
  const { data: clientes, isLoading, isError } = useClientes();
  const { mutateAsync: crearCliente, isPending: creando } = useCrearCliente();
  const { mutateAsync: desactivar } = useDesactivarCliente();
  const { mutateAsync: actualizarCliente } = useActualizarCliente();
  const toast = useToast();

  const [mostrarModal, setMostrarModal] = useState(false);
  const [nombre, setNombre] = useState("");
  const [errorModal, setErrorModal] = useState<string | null>(null);
  const [clienteEditar, setClienteEditar] = useState<ClienteOut | null>(null);
  const [nombreEditar, setNombreEditar] = useState("");
  const [errorEditar, setErrorEditar] = useState<string | null>(null);
  const [clienteDesactivar, setClienteDesactivar] = useState<ClienteOut | null>(
    null,
  );
  const [desactivando, setDesactivando] = useState(false);

  const handleCrear = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombre.trim()) return;
    setErrorModal(null);
    try {
      await crearCliente({ nombre: nombre.trim() });
      toast.exito(`Cliente "${nombre.trim()}" creado correctamente.`);
      setNombre("");
      setMostrarModal(false);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response
        ?.status;
      if (status === 409) {
        setErrorModal(`Ya existe un cliente con el nombre "${nombre.trim()}".`);
      } else {
        setErrorModal(
          extraerDetalleError(err) ?? "Ocurrió un error al crear el cliente.",
        );
      }
    }
  };

  const confirmarDesactivar = async () => {
    if (!clienteDesactivar) return;
    setDesactivando(true);
    try {
      await desactivar(clienteDesactivar.id);
      toast.exito(`Cliente "${clienteDesactivar.nombre}" desactivado.`);
    } catch {
      toast.error("No se pudo desactivar el cliente.");
    } finally {
      setDesactivando(false);
      setClienteDesactivar(null);
    }
  };

  const handleActivar = async (cliente: ClienteOut) => {
    try {
      await actualizarCliente({ id: cliente.id, datos: { activo: true } });
      toast.exito(`Cliente "${cliente.nombre}" activado.`);
    } catch {
      toast.error("No se pudo activar el cliente.");
    }
  };

  const handleEditar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombreEditar.trim() || !clienteEditar) return;
    setErrorEditar(null);
    try {
      await actualizarCliente({
        id: clienteEditar.id,
        datos: { nombre: nombreEditar.trim() },
      });
      toast.exito("Cliente actualizado correctamente.");
      setClienteEditar(null);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response
        ?.status;
      if (status === 409) {
        setErrorEditar(
          `Ya existe un cliente con el nombre "${nombreEditar.trim()}".`,
        );
      } else {
        setErrorEditar(
          extraerDetalleError(err) ??
            "Ocurrió un error al actualizar el cliente.",
        );
      }
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
        <p className={styles.error}>Error al cargar los clientes.</p>
      </div>
    );
  }

  return (
    <div>
      <div className={styles.encabezado}>
        <div>
          <h1 className={styles.titulo}>Clientes</h1>
          <p className={styles.subtitulo}>
            Administre los clientes que pueden asignarse a proyectos.
          </p>
        </div>
        <Button
          onClick={() => {
            setNombre("");
            setErrorModal(null);
            setMostrarModal(true);
          }}
        >
          <Building2 size={15} aria-hidden="true" />
          Nuevo cliente
        </Button>
      </div>

      {!clientes || clientes.length === 0 ? (
        <EmptyState mensaje="No hay clientes registrados aún." />
      ) : (
        <div className={styles.tablaWrapper}>
          <table className={styles.tabla}>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Estado</th>
                <th>Creado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {clientes.map((c) => (
                <tr key={c.id} className={!c.activo ? styles.filaInactiva : ""}>
                  <td className={styles.nombreCliente}>{c.nombre}</td>
                  <td>
                    <Badge variante={c.activo ? "activo" : "inactivo"} />
                  </td>
                  <td>{new Date(c.created_at).toLocaleDateString("es-BO")}</td>
                  <td>
                    <div className={styles.acciones}>
                      <Button
                        variante="secondary"
                        tamano="sm"
                        onClick={() => {
                          setNombreEditar(c.nombre);
                          setErrorEditar(null);
                          setClienteEditar(c);
                        }}
                      >
                        Editar
                      </Button>
                      {c.activo ? (
                        <Button
                          variante="danger"
                          tamano="sm"
                          onClick={() => setClienteDesactivar(c)}
                        >
                          Desactivar
                        </Button>
                      ) : (
                        <Button
                          variante="secondary"
                          tamano="sm"
                          onClick={() => handleActivar(c)}
                        >
                          Activar
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

      {/* Diálogo de confirmación para desactivar */}
      {clienteDesactivar && (
        <ConfirmDialog
          titulo={`¿Desactivar "${clienteDesactivar.nombre}"?`}
          descripcion="El cliente no aparecerá en los listados activos, pero sus proyectos se conservarán."
          textoConfirmar="Desactivar"
          cargando={desactivando}
          onCancelar={() => setClienteDesactivar(null)}
          onConfirmar={confirmarDesactivar}
        />
      )}

      {/* Modal de creación */}
      {mostrarModal && (
        <div
          className={styles.overlay}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-titulo"
        >
          <div className={styles.modal}>
            <h2 id="modal-titulo" className={styles.modalTitulo}>
              Nuevo cliente
            </h2>
            <form onSubmit={handleCrear} noValidate>
              <div className={styles.campo}>
                <label htmlFor="nombre-cliente" className={styles.label}>
                  Nombre del cliente
                </label>
                <input
                  id="nombre-cliente"
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  className={styles.input}
                  maxLength={100}
                  autoFocus
                  required
                />
              </div>
              {errorModal && (
                <p className={styles.errorModal} role="alert">
                  {errorModal}
                </p>
              )}
              <div className={styles.modalAcciones}>
                <Button
                  variante="secondary"
                  type="button"
                  onClick={() => setMostrarModal(false)}
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  isLoading={creando}
                  disabled={!nombre.trim()}
                >
                  Crear cliente
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de edición */}
      {clienteEditar !== null && (
        <div
          className={styles.overlay}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-editar-titulo"
        >
          <div className={styles.modal}>
            <h2 id="modal-editar-titulo" className={styles.modalTitulo}>
              Editar cliente
            </h2>
            <form onSubmit={handleEditar} noValidate>
              <div className={styles.campo}>
                <label htmlFor="nombre-editar" className={styles.label}>
                  Nombre del cliente
                </label>
                <input
                  id="nombre-editar"
                  type="text"
                  value={nombreEditar}
                  onChange={(e) => setNombreEditar(e.target.value)}
                  className={styles.input}
                  maxLength={100}
                  autoFocus
                  required
                />
              </div>
              {errorEditar && (
                <p className={styles.errorModal} role="alert">
                  {errorEditar}
                </p>
              )}
              <div className={styles.modalAcciones}>
                <Button
                  variante="secondary"
                  type="button"
                  onClick={() => setClienteEditar(null)}
                >
                  Cancelar
                </Button>
                <Button type="submit" disabled={!nombreEditar.trim()}>
                  Guardar cambios
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
