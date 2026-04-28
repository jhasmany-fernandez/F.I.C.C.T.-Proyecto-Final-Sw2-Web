/**
 * Pantalla de listado de proyectos de la organización para el admin.
 * Sp1-25 — PB-18 (CA-1, CA-2, CA-3, CA-4, CA-5).
 * Sp1-51 — PB-18 acción admin: archivar proyecto.
 * Sp1-52 — PB-18 acción admin: reasignar técnico.
 */

import { useState } from "react";
import { Archive, UserCog } from "lucide-react";
import { useUsuarios } from "../hooks/useUsuarios";
import {
  useArchivarProyectoAdmin,
  useProyectosOrg,
  useReasignarTecnico,
} from "../hooks/useProyectosOrg";
import type { ProyectoListOut, ProyectosFilter } from "../types";
import { Badge, Button, ConfirmDialog, EmptyState } from "@/shared/components";
import { useToast } from "@/shared/components";
import styles from "./ListadoProyectosOrg.module.css";

const ESTADOS = [
  { value: "", label: "Todos los estados" },
  { value: "nuevo", label: "Nuevo" },
  { value: "en_progreso", label: "En progreso" },
  { value: "completado", label: "Completado" },
  { value: "archivado", label: "Archivado" },
];

export default function ListadoProyectosOrg() {
  const [page, setPage] = useState(1);
  const [filtros, setFiltros] = useState<ProyectosFilter>({});

  // Diálogo archivar
  const [proyectoArchivar, setProyectoArchivar] =
    useState<ProyectoListOut | null>(null);
  // Modal reasignar técnico
  const [proyectoReasignar, setProyectoReasignar] =
    useState<ProyectoListOut | null>(null);
  const [nuevoTecnicoId, setNuevoTecnicoId] = useState<number | "">("");
  const [errorModal, setErrorModal] = useState<string | null>(null);
  const toast = useToast();

  const { data, isLoading, isError, isFetching } = useProyectosOrg(
    page,
    20,
    filtros,
  );
  const { data: usuarios } = useUsuarios();
  const { mutateAsync: archivar, isPending: archivando } =
    useArchivarProyectoAdmin();
  const { mutateAsync: reasignar, isPending: reasignando } =
    useReasignarTecnico();

  const tecnicos = (usuarios ?? []).filter(
    (u) => u.activo && u.rol === "tecnico",
  );

  const handleEstadoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFiltros((prev) => ({ ...prev, estado: e.target.value || undefined }));
    setPage(1);
  };

  const confirmarArchivar = async () => {
    if (!proyectoArchivar) return;
    try {
      await archivar(proyectoArchivar.id);
      toast.exito(`Proyecto "${proyectoArchivar.nombre}" archivado.`);
    } catch {
      toast.error("No se pudo archivar el proyecto.");
    } finally {
      setProyectoArchivar(null);
    }
  };

  const handleAbrirReasignar = (p: ProyectoListOut) => {
    setProyectoReasignar(p);
    setNuevoTecnicoId("");
    setErrorModal(null);
  };

  const handleConfirmarReasignar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!proyectoReasignar || nuevoTecnicoId === "") return;
    setErrorModal(null);
    try {
      await reasignar({
        id: proyectoReasignar.id,
        body: { tecnico_id: Number(nuevoTecnicoId) },
      });
      toast.exito("Proyecto reasignado correctamente.");
      setProyectoReasignar(null);
    } catch {
      setErrorModal(
        "No se pudo reasignar el proyecto. Verifique que el técnico esté activo.",
      );
    }
  };

  const totalPaginas = data ? Math.ceil(data.total / 20) : 1;

  return (
    <div>
      <div className={styles.encabezado}>
        <div>
          <h1 className={styles.titulo}>Proyectos de la organización</h1>
          <p className={styles.subtitulo}>
            Supervisión de todos los relevamientos WiFi de Bulldog Tech.
          </p>
        </div>
      </div>

      {/* Filtros */}
      <div className={styles.filtros}>
        <select
          value={filtros.estado ?? ""}
          onChange={handleEstadoChange}
          className={styles.select}
          aria-label="Filtrar por estado"
        >
          {ESTADOS.map((e) => (
            <option key={e.value} value={e.value}>
              {e.label}
            </option>
          ))}
        </select>
        {isFetching && !isLoading && (
          <span className={styles.actualizando}>Actualizando…</span>
        )}
      </div>

      {/* Estados de carga */}
      {isLoading ? (
        <div className={styles.skeletonWrapper}>
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className={styles.skeleton} />
          ))}
        </div>
      ) : isError ? (
        <EmptyState mensaje="Error al cargar los proyectos." />
      ) : !data || data.total === 0 ? (
        <EmptyState mensaje="No hay proyectos registrados aún." />
      ) : (
        <>
          <div className={styles.tablaWrapper}>
            <table className={styles.tabla}>
              <thead>
                <tr>
                  <th>Proyecto</th>
                  <th>Cliente</th>
                  <th>Técnico</th>
                  <th>Estado</th>
                  <th>Última actividad</th>
                  <th>Puntos</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((p) => (
                  <tr key={p.id}>
                    <td className={styles.nombreProyecto}>{p.nombre}</td>
                    <td>{p.cliente?.nombre ?? "—"}</td>
                    <td>{p.tecnico.nombre}</td>
                    <td>
                      <Badge
                        variante={
                          p.estado as "en_progreso" | "completado" | "archivado"
                        }
                        etiqueta={_labelEstado(p.estado)}
                      />
                    </td>
                    <td>
                      {new Date(p.ultima_actividad).toLocaleDateString("es-BO")}
                    </td>
                    <td>{p.cantidad_puntos}</td>
                    <td>
                      <div className={styles.acciones}>
                        {p.estado !== "archivado" && (
                          <Button
                            variante="danger"
                            tamano="sm"
                            onClick={() => setProyectoArchivar(p)}
                            isLoading={
                              archivando && proyectoArchivar?.id === p.id
                            }
                          >
                            <Archive size={14} aria-hidden="true" />
                            Archivar
                          </Button>
                        )}
                        <Button
                          variante="secondary"
                          tamano="sm"
                          onClick={() => handleAbrirReasignar(p)}
                        >
                          <UserCog size={14} aria-hidden="true" />
                          Reasignar
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Paginación */}
          {totalPaginas > 1 && (
            <div className={styles.paginacion}>
              <Button
                variante="secondary"
                tamano="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                ‹ Anterior
              </Button>
              <span className={styles.infoPag}>
                Página {page} de {totalPaginas} — {data.total} proyectos
              </span>
              <Button
                variante="secondary"
                tamano="sm"
                onClick={() => setPage((p) => Math.min(totalPaginas, p + 1))}
                disabled={page === totalPaginas}
              >
                Siguiente ›
              </Button>
            </div>
          )}
        </>
      )}

      {/* Diálogo de confirmación para archivar */}
      {proyectoArchivar && (
        <ConfirmDialog
          titulo={`¿Archivar "${proyectoArchivar.nombre}"?`}
          descripcion="El proyecto ya no aparecerá en la lista activa del técnico. Esta acción puede revertirse contactando al administrador."
          textoConfirmar="Archivar"
          cargando={archivando}
          onCancelar={() => setProyectoArchivar(null)}
          onConfirmar={confirmarArchivar}
        />
      )}

      {/* Modal reasignar técnico */}
      {proyectoReasignar && (
        <div
          className={styles.overlay}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-reasignar"
        >
          <div className={styles.modal}>
            <h2 id="modal-reasignar" className={styles.modalTitulo}>
              Reasignar técnico
            </h2>
            <p className={styles.modalSubtitulo}>
              Proyecto: <strong>{proyectoReasignar.nombre}</strong>
              <br />
              Técnico actual:{" "}
              <strong>{proyectoReasignar.tecnico.nombre}</strong>
            </p>
            <form onSubmit={handleConfirmarReasignar}>
              <label className={styles.modalLabel} htmlFor="select-tecnico">
                Nuevo técnico
              </label>
              <select
                id="select-tecnico"
                className={styles.modalSelect}
                value={nuevoTecnicoId}
                onChange={(e) =>
                  setNuevoTecnicoId(
                    e.target.value ? Number(e.target.value) : "",
                  )
                }
                required
              >
                <option value="">— Seleccione un técnico —</option>
                {tecnicos
                  .filter((t) => t.id !== proyectoReasignar.tecnico.id)
                  .map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.nombre} ({t.email})
                    </option>
                  ))}
              </select>
              {errorModal && (
                <p className={styles.modalError} role="alert">
                  {errorModal}
                </p>
              )}
              <div className={styles.modalAcciones}>
                <Button
                  variante="secondary"
                  type="button"
                  onClick={() => setProyectoReasignar(null)}
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  isLoading={reasignando}
                  disabled={nuevoTecnicoId === ""}
                >
                  Confirmar
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function _labelEstado(estado: string): string {
  const mapa: Record<string, string> = {
    en_progreso: "En progreso",
    completado: "Completado",
    archivado: "Archivado",
  };
  return mapa[estado] ?? estado;
}
