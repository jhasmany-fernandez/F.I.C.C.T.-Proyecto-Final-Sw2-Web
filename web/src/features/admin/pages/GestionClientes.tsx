/**
 * Página de gestión de clientes del panel admin.
 * Sp1-35 — PB-19 (CA-1, CA-2, CA-3, CA-4, CA-5).
 */

import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { listarTodosClientes } from "../api/clientesApi";
import {
  CLIENTES_KEY,
  useActualizarCliente,
  useClientes,
  useCrearCliente,
  useDesactivarCliente,
} from "../hooks/useClientes";
import type { ClienteOut } from "../types";
import { Badge, Button, ConfirmDialog, EmptyState } from "@/shared/components";
import { useToast } from "@/shared/components";
import styles from "./GestionClientes.module.css";

export default function GestionClientes() {
  const queryClient = useQueryClient();
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
  const submitCrearEnCursoRef = useRef(false);
  const submitEditarEnCursoRef = useRef(false);

  const revalidarClientePorNombre = async (nombreBuscado: string) => {
    const nombreNormalizado = nombreBuscado.trim().toLowerCase();
    const pausasMs = [0, 250, 750];

    for (const pausaMs of pausasMs) {
      if (pausaMs > 0) {
        await new Promise((resolve) => window.setTimeout(resolve, pausaMs));
      }

      const clientesActualizados = await listarTodosClientes();
      queryClient.setQueryData(CLIENTES_KEY, clientesActualizados);

      const clienteEncontrado = clientesActualizados.find(
        (cliente) =>
          cliente.nombre.trim().toLowerCase() === nombreNormalizado,
      );

      if (clienteEncontrado) {
        return clienteEncontrado;
      }
    }

    return null;
  };

  const revalidarClientePorId = async (clienteId: number) => {
    const pausasMs = [0, 250, 750];

    for (const pausaMs of pausasMs) {
      if (pausaMs > 0) {
        await new Promise((resolve) => window.setTimeout(resolve, pausaMs));
      }

      const clientesActualizados = await listarTodosClientes();
      queryClient.setQueryData(CLIENTES_KEY, clientesActualizados);

      const clienteEncontrado = clientesActualizados.find(
        (cliente) => cliente.id === clienteId,
      );

      if (clienteEncontrado) {
        return clienteEncontrado;
      }
    }

    return null;
  };

  useEffect(() => {
    if (!mostrarModal || !nombre.trim() || !clientes?.length) return;

    const nombreNormalizado = nombre.trim().toLowerCase();
    const clienteVisible = clientes.find(
      (cliente) => cliente.nombre.trim().toLowerCase() === nombreNormalizado,
    );

    if (!clienteVisible) return;

    const timeoutId = window.setTimeout(() => {
      setErrorModal(null);
      setNombre("");
      setMostrarModal(false);

      if (submitCrearEnCursoRef.current) {
        toast.exito(`Cliente "${clienteVisible.nombre}" creado correctamente.`);
      }
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [clientes, mostrarModal, nombre, toast]);

  const handleCrear = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombre.trim()) return;
    if (submitCrearEnCursoRef.current) return;

    submitCrearEnCursoRef.current = true;
    setErrorModal(null);
    const nombreNormalizado = nombre.trim().toLowerCase();
    const clientesAntes = queryClient.getQueryData<ClienteOut[]>(CLIENTES_KEY) ?? [];
    const clienteExistiaAntes = clientesAntes.some(
      (cliente) => cliente.nombre.trim().toLowerCase() === nombreNormalizado,
    );

    try {
      await crearCliente({ nombre: nombre.trim() });
      toast.exito(`Cliente "${nombre.trim()}" creado correctamente.`);
      setNombre("");
      setMostrarModal(false);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response
        ?.status;
      try {
        const clienteTrasError = await revalidarClientePorNombre(nombre.trim());

        if (clienteTrasError) {
          queryClient.invalidateQueries({ queryKey: CLIENTES_KEY });

          if (status === 409 && clienteExistiaAntes) {
            toast.info(`El cliente "${nombre.trim()}" ya estaba registrado.`);
          } else if (status === 409) {
            toast.info(`El cliente "${nombre.trim()}" ya existe en el sistema.`);
          } else {
            toast.exito(`Cliente "${nombre.trim()}" creado correctamente.`);
          }

          setNombre("");
          setMostrarModal(false);
          return;
        }
      } catch {
        // Si tampoco se puede revalidar contra backend, mostramos el error original.
      }

      if (status === 409) {
        setErrorModal(`Ya existe un cliente con el nombre "${nombre.trim()}".`);
      } else {
        setErrorModal("Ocurrió un error al crear el cliente.");
      }
    } finally {
      submitCrearEnCursoRef.current = false;
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
    if (submitEditarEnCursoRef.current) return;

    submitEditarEnCursoRef.current = true;
    setErrorEditar(null);
    const nombreNormalizado = nombreEditar.trim().toLowerCase();

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
        try {
          const clienteActualizado = await revalidarClientePorId(clienteEditar.id);

          if (
            clienteActualizado &&
            clienteActualizado.nombre.trim().toLowerCase() === nombreNormalizado
          ) {
            queryClient.invalidateQueries({ queryKey: CLIENTES_KEY });
            toast.exito("Cliente actualizado correctamente.");
            setClienteEditar(null);
            return;
          }
        } catch {
          // Si tampoco se puede revalidar contra backend, mostramos el error original.
        }

        setErrorEditar("Ocurrió un error al actualizar el cliente.");
      }
    } finally {
      submitEditarEnCursoRef.current = false;
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
