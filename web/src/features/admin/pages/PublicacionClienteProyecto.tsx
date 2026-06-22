import { useMemo, useState, type ReactNode } from "react";
import { Copy, ExternalLink, Link2, RotateCcw, XCircle } from "lucide-react";
import { useOutletContext } from "react-router-dom";
import { Button, EmptyState, useToast } from "@/shared/components";
import {
  useActualizarEnlaceCliente,
  useConjuntosPorPlanos,
  useCrearEnlaceCliente,
  useEnlacesCliente,
  useEscenariosProyecto,
  useMapasPorPlanos,
  usePlanosProyecto,
  useReportesProyecto,
} from "../hooks/useProyectosOrg";
import type {
  ConjuntoAPOut,
  EscenarioOptimizadoOut,
  MapaCalorOut,
  ReporteOut,
} from "../types";
import styles from "./PublicacionClienteProyecto.module.css";

export default function PublicacionClienteProyecto() {
  const { proyectoId } = useOutletContext<{
    proyectoId: number;
    proyectoNombre: string;
  }>();
  const toast = useToast();
  const [diasEnlace, setDiasEnlace] = useState(7);
  const [ultimoEnlace, setUltimoEnlace] = useState<string | null>(null);
  const [escenariosSeleccionados, setEscenariosSeleccionados] = useState<Set<number>>(
    () => new Set(),
  );
  const [conjuntosSeleccionados, setConjuntosSeleccionados] = useState<Set<number>>(
    () => new Set(),
  );
  const [mapasSeleccionados, setMapasSeleccionados] = useState<Set<number>>(
    () => new Set(),
  );
  const [analisisSeleccionados, setAnalisisSeleccionados] = useState<Set<number>>(
    () => new Set(),
  );
  const [reporteSeleccionado, setReporteSeleccionado] = useState<number | null>(null);

  const { data: escenarios, isLoading: cargandoEscenarios, isError: errorEscenarios } =
    useEscenariosProyecto(proyectoId);
  const { data: planos, isLoading: cargandoPlanos, isError: errorPlanos } =
    usePlanosProyecto(proyectoId);
  const planoIds = useMemo(() => (planos ?? []).map((plano) => plano.id), [planos]);
  const consultasConjuntos = useConjuntosPorPlanos(planoIds);
  const consultasMapas = useMapasPorPlanos(planoIds);
  const { data: reportes, isLoading: cargandoReportes, isError: errorReportes } =
    useReportesProyecto(proyectoId);
  const { data: enlacesCliente, isLoading: cargandoEnlaces } =
    useEnlacesCliente(proyectoId);
  const { mutateAsync: crearEnlace, isPending: creandoEnlace } =
    useCrearEnlaceCliente(proyectoId);
  const { mutateAsync: actualizarEnlace, isPending: actualizandoEnlace } =
    useActualizarEnlaceCliente(proyectoId);

  const escenariosPublicados = useMemo(
    () =>
      [...(escenarios ?? [])]
        .filter((escenario) => escenario.estado_gobernanza === "publicado_cliente")
        .sort((a, b) => b.pct_cobertura - a.pct_cobertura),
    [escenarios],
  );
  const conjuntosPublicados = useMemo(
    () =>
      consultasConjuntos
        .flatMap((consulta) => consulta.data ?? [])
        .filter((conjunto) => conjunto.estado_gobernanza === "publicado_cliente")
        .sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1)),
    [consultasConjuntos],
  );
  const cargandoConjuntos = consultasConjuntos.some((consulta) => consulta.isLoading);
  const errorConjuntos = consultasConjuntos.some((consulta) => consulta.isError);
  const mapas = useMemo(
    () =>
      consultasMapas
        .flatMap((consulta) => consulta.data ?? [])
        .sort((a, b) => (a.created_at < b.created_at ? 1 : -1)),
    [consultasMapas],
  );
  const reportesListos = useMemo(
    () => (reportes ?? []).filter((reporte) => reporte.estado === "LISTO"),
    [reportes],
  );
  const cargandoMapas = consultasMapas.some((consulta) => consulta.isLoading);
  const errorMapas = consultasMapas.some((consulta) => consulta.isError);
  const cargando =
    cargandoEscenarios || cargandoPlanos || cargandoConjuntos || cargandoMapas || cargandoReportes;
  const error = errorEscenarios || errorPlanos || errorConjuntos || errorMapas || errorReportes;

  const totalSeleccionado =
    escenariosSeleccionados.size +
    conjuntosSeleccionados.size +
    mapasSeleccionados.size +
    analisisSeleccionados.size +
    Number(reporteSeleccionado !== null);

  const handleCrearEnlace = async () => {
    const escenarios = escenariosPublicados.filter((escenario) =>
      escenariosSeleccionados.has(escenario.id),
    );
    const conjuntos = conjuntosPublicados.filter((conjunto) =>
      conjuntosSeleccionados.has(conjunto.id),
    );
    if (totalSeleccionado === 0) {
      toast.error("Seleccione al menos un contenido publicado para el cliente.");
      return;
    }
    try {
      const enlace = await crearEnlace({
        expira_en_dias: diasEnlace,
        contenido: {
          conjunto_ids: conjuntos.map((item) => item.id),
          escenario_ids: escenarios.map((item) => item.id),
          mapa_ids: Array.from(mapasSeleccionados),
          analisis_ids: Array.from(analisisSeleccionados),
          reporte_id: reporteSeleccionado,
        },
      });
      const url = `${window.location.origin}${enlace.url_publica}`;
      setUltimoEnlace(url);
      const copiado = await _copiar(url);
      toast.exito(
        copiado
          ? "Enlace de cliente creado y copiado."
          : "Enlace de cliente creado.",
      );
    } catch {
      toast.error("No se pudo crear el enlace de cliente.");
    }
  };

  const handleActualizarEnlace = async (enlaceId: number, revocado: boolean) => {
    try {
      await actualizarEnlace({ enlaceId, revocado });
      toast.exito(revocado ? "Enlace revocado." : "Enlace reactivado.");
    } catch {
      toast.error("No se pudo actualizar el enlace.");
    }
  };

  const handleCopiar = async (urlPublica: string) => {
    const url = `${window.location.origin}${urlPublica}`;
    setUltimoEnlace(url);
    const copiado = await _copiar(url);
    toast.exito(copiado ? "Enlace copiado." : "Enlace disponible en pantalla.");
  };

  if (cargando) return <div className={styles.skeleton} />;
  if (error) return <EmptyState mensaje="No se pudo cargar el contenido publicable." />;

  return (
    <section className={styles.contenedor}>
      <div className={styles.encabezadoSeccion}>
        <div>
          <h2>Publicación al cliente</h2>
          <p>El enlace incluye únicamente el contenido seleccionado en esta pantalla.</p>
        </div>
        <div className={styles.generador}>
          <label>
            Vigencia
            <select
              value={diasEnlace}
              onChange={(event) => setDiasEnlace(Number(event.target.value))}
            >
              <option value={1}>1 día</option>
              <option value={7}>7 días</option>
              <option value={30}>30 días</option>
              <option value={90}>90 días</option>
            </select>
          </label>
          <Button
            type="button"
            disabled={totalSeleccionado === 0}
            isLoading={creandoEnlace}
            onClick={handleCrearEnlace}
          >
            <Link2 size={16} aria-hidden="true" />
            Generar enlace
          </Button>
        </div>
      </div>

      <div className={styles.selectorGrid}>
        <PanelSeleccion
          titulo="Conjuntos publicados"
          vacio="No hay conjuntos publicados para cliente."
        >
          {conjuntosPublicados.map((conjunto) => (
            <SeleccionConjunto
              key={conjunto.id}
              conjunto={conjunto}
              seleccionado={conjuntosSeleccionados.has(conjunto.id)}
              onToggle={() =>
                setConjuntosSeleccionados((prev) =>
                  _toggleSet(prev, conjunto.id),
                )
              }
            />
          ))}
        </PanelSeleccion>

        <PanelSeleccion titulo="Heatmaps" vacio="No hay heatmaps generados.">
          {mapas.map((mapa) => (
            <SeleccionMapa
              key={mapa.id}
              mapa={mapa}
              seleccionado={mapasSeleccionados.has(mapa.id)}
              onToggle={() =>
                setMapasSeleccionados((prev) => _toggleSet(prev, mapa.id))
              }
            />
          ))}
        </PanelSeleccion>

        <PanelSeleccion titulo="Análisis" vacio="No hay análisis generados.">
          {mapas
            .filter((mapa) => mapa.analisis_id !== null)
            .map((mapa) => (
              <SeleccionAnalisis
                key={mapa.analisis_id}
                mapa={mapa}
                seleccionado={analisisSeleccionados.has(mapa.analisis_id ?? 0)}
                onToggle={() =>
                  setAnalisisSeleccionados((prev) =>
                    _toggleSet(prev, mapa.analisis_id ?? 0),
                  )
                }
              />
            ))}
        </PanelSeleccion>

        <PanelSeleccion
          titulo="Alternativas IA publicadas"
          vacio="No hay alternativas IA publicadas para cliente."
        >
          {escenariosPublicados.map((escenario) => (
            <SeleccionEscenario
              key={escenario.id}
              escenario={escenario}
              seleccionado={escenariosSeleccionados.has(escenario.id)}
              onToggle={() =>
                setEscenariosSeleccionados((prev) =>
                  _toggleSet(prev, escenario.id),
                )
              }
            />
          ))}
        </PanelSeleccion>

        <PanelSeleccion titulo="Reporte" vacio="No hay reportes listos.">
          {reportesListos.map((reporte) => (
            <SeleccionReporte
              key={reporte.id}
              reporte={reporte}
              seleccionado={reporteSeleccionado === reporte.id}
              onToggle={() =>
                setReporteSeleccionado((prev) =>
                  prev === reporte.id ? null : reporte.id,
                )
              }
            />
          ))}
        </PanelSeleccion>
      </div>

      {ultimoEnlace && <p className={styles.enlaceReciente}>{ultimoEnlace}</p>}

      <section className={styles.enlaces}>
        <h2>Enlaces generados</h2>
        {cargandoEnlaces ? (
          <div className={styles.skeletonMini} />
        ) : !enlacesCliente || enlacesCliente.length === 0 ? (
          <EmptyState mensaje="Todavía no hay enlaces de cliente para este proyecto." />
        ) : (
          <div className={styles.enlacesLista}>
            {enlacesCliente.map((enlace) => (
              <div key={enlace.id} className={styles.enlaceRow}>
                <div>
                  <strong>
                    {enlace.revocado ? "Revocado" : "Activo"} · vence{" "}
                    {_fechaCorta(enlace.expira_en)}
                  </strong>
                  <small>
                    {enlace.accesos} acceso(s) ·{" "}
                    {enlace.contenido.conjunto_ids.length} conjunto(s) ·{" "}
                    {enlace.contenido.escenario_ids.length} alternativa(s)
                  </small>
                </div>
                <div className={styles.enlaceAcciones}>
                  <Button
                    type="button"
                    variante="ghost"
                    tamano="sm"
                    onClick={() => handleCopiar(enlace.url_publica)}
                  >
                    <Copy size={14} aria-hidden="true" />
                    Copiar
                  </Button>
                  <a
                    className={styles.abrirEnlace}
                    href={enlace.url_publica}
                    target="_blank"
                    rel="noreferrer"
                    aria-label="Abrir enlace"
                  >
                    <ExternalLink size={14} aria-hidden="true" />
                  </a>
                  <Button
                    type="button"
                    variante={enlace.revocado ? "secondary" : "danger"}
                    tamano="sm"
                    disabled={actualizandoEnlace}
                    onClick={() =>
                      handleActualizarEnlace(enlace.id, !enlace.revocado)
                    }
                  >
                    {enlace.revocado ? (
                      <RotateCcw size={14} aria-hidden="true" />
                    ) : (
                      <XCircle size={14} aria-hidden="true" />
                    )}
                    {enlace.revocado ? "Reactivar" : "Revocar"}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}

function PanelSeleccion({
  titulo,
  vacio,
  children,
}: {
  titulo: string;
  vacio: string;
  children: ReactNode;
}) {
  const items = Array.isArray(children) ? children.filter(Boolean) : children;
  const estaVacio = Array.isArray(items) ? items.length === 0 : !items;
  return (
    <section className={styles.panelSeleccion}>
      <h2>{titulo}</h2>
      {estaVacio ? <p className={styles.vacio}>{vacio}</p> : <div>{items}</div>}
    </section>
  );
}

function SeleccionConjunto({
  conjunto,
  seleccionado,
  onToggle,
}: {
  conjunto: ConjuntoAPOut;
  seleccionado: boolean;
  onToggle: () => void;
}) {
  return (
    <label className={styles.itemSeleccion}>
      <input type="checkbox" checked={seleccionado} onChange={onToggle} />
      <span>
        <strong>{conjunto.nombre}</strong>
        <small>
          {_labelOrigen(conjunto.origen)} · {conjunto.cantidad_aps} APs
        </small>
      </span>
    </label>
  );
}

function SeleccionEscenario({
  escenario,
  seleccionado,
  onToggle,
}: {
  escenario: EscenarioOptimizadoOut;
  seleccionado: boolean;
  onToggle: () => void;
}) {
  return (
    <label className={styles.itemSeleccion}>
      <input type="checkbox" checked={seleccionado} onChange={onToggle} />
      <span>
        <strong>{escenario.nombre}</strong>
        <small>
          {escenario.pct_cobertura.toFixed(1)}% cobertura ·{" "}
          {escenario.cantidad_aps} APs
        </small>
      </span>
    </label>
  );
}

function SeleccionMapa({
  mapa,
  seleccionado,
  onToggle,
}: {
  mapa: MapaCalorOut;
  seleccionado: boolean;
  onToggle: () => void;
}) {
  return (
    <label className={styles.itemSeleccion}>
      <input type="checkbox" checked={seleccionado} onChange={onToggle} />
      <span>
        <strong>{mapa.ssid || mapa.bssid || `Heatmap #${mapa.id}`}</strong>
        <small>{mapa.modo_generacion} · {mapa.cantidad_puntos} puntos</small>
      </span>
    </label>
  );
}

function SeleccionAnalisis({
  mapa,
  seleccionado,
  onToggle,
}: {
  mapa: MapaCalorOut;
  seleccionado: boolean;
  onToggle: () => void;
}) {
  return (
    <label className={styles.itemSeleccion}>
      <input type="checkbox" checked={seleccionado} onChange={onToggle} />
      <span>
        <strong>Análisis #{mapa.analisis_id}</strong>
        <small>Heatmap {mapa.ssid || mapa.bssid || `#${mapa.id}`}</small>
      </span>
    </label>
  );
}

function SeleccionReporte({
  reporte,
  seleccionado,
  onToggle,
}: {
  reporte: ReporteOut;
  seleccionado: boolean;
  onToggle: () => void;
}) {
  return (
    <label className={styles.itemSeleccion}>
      <input type="checkbox" checked={seleccionado} onChange={onToggle} />
      <span>
        <strong>Reporte #{reporte.id}</strong>
        <small>{_fechaCorta(reporte.created_at)} · {reporte.tamanio_bytes} bytes</small>
      </span>
    </label>
  );
}

function _toggleSet(prev: Set<number>, id: number): Set<number> {
  const siguiente = new Set(prev);
  if (siguiente.has(id)) {
    siguiente.delete(id);
  } else {
    siguiente.add(id);
  }
  return siguiente;
}

async function _copiar(texto: string): Promise<boolean> {
  if (!navigator.clipboard?.writeText) return false;
  try {
    await navigator.clipboard.writeText(texto);
    return true;
  } catch {
    return false;
  }
}

function _fechaCorta(valor: string): string {
  return new Intl.DateTimeFormat("es-BO", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(valor));
}

function _labelOrigen(origen: string): string {
  const mapa: Record<string, string> = {
    manual_movil: "Móvil",
    manual_web: "Web",
    ia: "IA",
  };
  return mapa[origen] ?? origen;
}
