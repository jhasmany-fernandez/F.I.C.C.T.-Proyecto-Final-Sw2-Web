import { useMemo, useState } from "react";
import {
  Activity,
  CheckCircle2,
  Edit3,
  Eye,
  Map as MapIcon,
  Plus,
  Send,
  XCircle,
} from "lucide-react";
import { useOutletContext } from "react-router-dom";
import { Badge, Button, EmptyState, useToast } from "@/shared/components";
import {
  useAPsPlano,
  useActualizarConjuntoAP,
  useAnalizarMapa,
  useCambiarEstadoConjuntoAP,
  useConjuntosPorPlanos,
  useCrearConjuntoAP,
  useGenerarHeatmapConjunto,
  useMapasPorPlanos,
  usePlanosProyecto,
} from "../hooks/useProyectosOrg";
import type {
  ConjuntoAPOut,
  EstadoGobernanzaConjunto,
  MapaCalorOut,
} from "../types";
import styles from "./ConjuntosAPProyecto.module.css";

type FiltroOrigen = "todos" | "manual_movil" | "manual_web" | "ia";
type ModoHeatmap = "INDIVIDUAL" | "SUBCONJUNTO" | "CONJUNTO_COMPLETO";

export default function ConjuntosAPProyecto() {
  const { proyectoId } = useOutletContext<{ proyectoId: number; proyectoNombre: string }>();
  const toast = useToast();
  const [filtroOrigen, setFiltroOrigen] = useState<FiltroOrigen>("todos");
  const [editorVisible, setEditorVisible] = useState(false);
  const [editando, setEditando] = useState<ConjuntoAPOut | null>(null);
  const [planoEditorId, setPlanoEditorId] = useState<number | null>(null);
  const [nombre, setNombre] = useState("");
  const [proposito, setProposito] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [bssidsEditor, setBssidsEditor] = useState<Set<string>>(() => new Set());
  const [conjuntoRevision, setConjuntoRevision] = useState<ConjuntoAPOut | null>(null);
  const [modo, setModo] = useState<ModoHeatmap>("CONJUNTO_COMPLETO");
  const [bssidsHeatmap, setBssidsHeatmap] = useState<Set<string>>(() => new Set());
  const [mapaGenerado, setMapaGenerado] = useState<MapaCalorOut | null>(null);
  const [mapaTemporalA, setMapaTemporalA] = useState<number | null>(null);
  const [mapaTemporalB, setMapaTemporalB] = useState<number | null>(null);

  const { data: planos, isLoading: cargandoPlanos, isError: errorPlanos } =
    usePlanosProyecto(proyectoId);
  const planoIds = useMemo(() => (planos ?? []).map((plano) => plano.id), [planos]);
  const consultasConjuntos = useConjuntosPorPlanos(planoIds);
  const consultasMapas = useMapasPorPlanos(planoIds);
  const planoActivoEditor = planoEditorId ?? planos?.[0]?.id ?? null;
  const { data: apsEditor } = useAPsPlano(planoActivoEditor);
  const { mutateAsync: crear, isPending: creando } = useCrearConjuntoAP();
  const { mutateAsync: actualizar, isPending: actualizando } = useActualizarConjuntoAP();
  const { mutateAsync: cambiarEstado, isPending: cambiando } =
    useCambiarEstadoConjuntoAP(proyectoId);
  const { mutateAsync: generar, isPending: generando } = useGenerarHeatmapConjunto();
  const { mutateAsync: analizar, isPending: analizando } = useAnalizarMapa();

  const conjuntos = useMemo(
    () =>
      consultasConjuntos
        .flatMap((consulta) => consulta.data ?? [])
        .sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1)),
    [consultasConjuntos],
  );
  const mapas = useMemo(
    () =>
      consultasMapas
        .flatMap((consulta) => consulta.data ?? [])
        .sort((a, b) => (a.created_at < b.created_at ? 1 : -1)),
    [consultasMapas],
  );
  const mapasRevision = conjuntoRevision
    ? mapas.filter((mapa) => mapa.conjunto_ap_id === conjuntoRevision.id)
    : [];
  const mapasPorId = new Map(mapasRevision.map((mapa) => [mapa.id, mapa]));
  const planosPorId = useMemo(
    () => new Map((planos ?? []).map((plano) => [plano.id, plano])),
    [planos],
  );
  const cargandoConjuntos = consultasConjuntos.some((consulta) => consulta.isLoading);
  const errorConjuntos = consultasConjuntos.some((consulta) => consulta.isError);
  const conjuntosFiltrados =
    filtroOrigen === "todos"
      ? conjuntos
      : conjuntos.filter((conjunto) => conjunto.origen === filtroOrigen);
  const resumen = _resumenConjuntos(conjuntos);

  const abrirNuevo = () => {
    setEditando(null);
    setPlanoEditorId(planos?.[0]?.id ?? null);
    setNombre("");
    setProposito("");
    setDescripcion("");
    setBssidsEditor(new Set());
    setEditorVisible(true);
  };

  const abrirEdicion = (conjunto: ConjuntoAPOut) => {
    setEditando(conjunto);
    setPlanoEditorId(conjunto.plano_id);
    setNombre(conjunto.nombre);
    setProposito(conjunto.proposito);
    setDescripcion(conjunto.descripcion ?? "");
    setBssidsEditor(new Set(conjunto.items.map((item) => item.bssid)));
    setEditorVisible(true);
  };

  const guardarConjunto = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!planoActivoEditor || !nombre.trim() || !proposito.trim() || bssidsEditor.size === 0) {
      toast.error("Complete nombre, propósito y seleccione al menos un AP.");
      return;
    }
    const body = {
      nombre: nombre.trim(),
      proposito: proposito.trim(),
      descripcion: descripcion.trim() || null,
      bssids: Array.from(bssidsEditor),
    };
    try {
      if (editando) await actualizar({ conjuntoId: editando.id, body });
      else await crear({ planoId: planoActivoEditor, body });
      toast.exito(editando ? "Conjunto actualizado." : "Conjunto web creado.");
      setEditorVisible(false);
    } catch {
      toast.error("No se pudo guardar el conjunto.");
    }
  };

  const revisar = (conjunto: ConjuntoAPOut) => {
    setConjuntoRevision(conjunto);
    setModo("CONJUNTO_COMPLETO");
    setBssidsHeatmap(new Set(conjunto.items.map((item) => item.bssid)));
    setMapaGenerado(null);
    setMapaTemporalA(null);
    setMapaTemporalB(null);
  };

  const generarMapa = async () => {
    if (!conjuntoRevision) return;
    const bssids = Array.from(bssidsHeatmap);
    if ((modo === "INDIVIDUAL" && bssids.length !== 1) || (modo === "SUBCONJUNTO" && bssids.length === 0)) {
      toast.error(modo === "INDIVIDUAL" ? "Seleccione exactamente un AP." : "Seleccione al menos un AP.");
      return;
    }
    try {
      const mapa = await generar({
        conjuntoId: conjuntoRevision.id,
        body: { modo, bssids, algoritmo: "IDW", resolucion: 128 },
      });
      setMapaGenerado(mapa);
      toast.exito("Heatmap operativo generado.");
    } catch {
      toast.error("No se pudo generar el heatmap con la selección actual.");
    }
  };

  const analizarMapa = async () => {
    if (!mapaGenerado) return;
    try {
      const resultado = await analizar(mapaGenerado.id);
      setMapaGenerado((prev) => prev ? { ...prev, analisis_id: resultado.id } : prev);
      toast.exito(`Análisis generado: ${resultado.pct_cobertura.toFixed(1)}% de cobertura.`);
    } catch {
      toast.error("No se pudo analizar el heatmap.");
    }
  };

  const handleEstado = async (conjunto: ConjuntoAPOut, estado: EstadoGobernanzaConjunto) => {
    try {
      await cambiarEstado({ conjuntoId: conjunto.id, estadoGobernanza: estado });
      toast.exito(`Conjunto "${conjunto.nombre}" actualizado.`);
    } catch {
      toast.error("No se pudo actualizar el estado del conjunto.");
    }
  };

  if (cargandoPlanos || cargandoConjuntos) return <div className={styles.skeleton} />;
  if (errorPlanos || errorConjuntos) return <EmptyState mensaje="No se pudieron cargar los conjuntos de APs." />;
  if (!planos || planos.length === 0) return <EmptyState mensaje="El proyecto todavía no tiene planos." />;

  return (
    <section className={styles.contenedor}>
      <div className={styles.encabezadoSeccion}>
        <div>
          <h2>Gobernanza de conjuntos de APs</h2>
          <p>Creación web, revisión de APs y heatmaps operativos por selección.</p>
        </div>
        <Button type="button" onClick={abrirNuevo}>
          <Plus size={16} aria-hidden="true" /> Nuevo conjunto
        </Button>
      </div>

      {editorVisible && (
        <form className={styles.editor} onSubmit={guardarConjunto}>
          <div className={styles.editorCampos}>
            <label>Plano<select value={planoActivoEditor ?? ""} disabled={Boolean(editando)} onChange={(e) => { setPlanoEditorId(Number(e.target.value)); setBssidsEditor(new Set()); }}>{planos.map((plano) => <option key={plano.id} value={plano.id}>{plano.nombre}</option>)}</select></label>
            <label>Nombre<input value={nombre} onChange={(e) => setNombre(e.target.value)} /></label>
            <label>Propósito<input value={proposito} onChange={(e) => setProposito(e.target.value)} /></label>
            <label>Descripción<input value={descripcion} onChange={(e) => setDescripcion(e.target.value)} /></label>
          </div>
          <div className={styles.apSelector}>
            {(apsEditor ?? []).map((ap) => (
              <label key={ap.bssid}>
                <input type="checkbox" checked={bssidsEditor.has(ap.bssid)} onChange={() => setBssidsEditor((prev) => _toggleTexto(prev, ap.bssid))} />
                <span><strong>{ap.ssid || "SSID oculto"}</strong><small>{ap.bssid} · {ap.rssi_promedio.toFixed(1)} dBm</small></span>
              </label>
            ))}
          </div>
          <div className={styles.accionesEditor}>
            <Button type="button" variante="ghost" onClick={() => setEditorVisible(false)}>Cancelar</Button>
            <Button type="submit" isLoading={creando || actualizando}>Guardar</Button>
          </div>
        </form>
      )}

      <div className={styles.resumen}>
        <ResumenItem etiqueta="Móvil" valor={resumen.manual_movil} />
        <ResumenItem etiqueta="Web" valor={resumen.manual_web} />
        <ResumenItem etiqueta="IA" valor={resumen.ia} />
        <ResumenItem etiqueta="Publicados" valor={resumen.publicado_cliente} />
      </div>

      <div className={styles.filtros}>
        {(["todos", "manual_movil", "manual_web", "ia"] as FiltroOrigen[]).map((origen) => (
          <button key={origen} type="button" className={filtroOrigen === origen ? styles.filtroActivo : ""} onClick={() => setFiltroOrigen(origen)}>{_labelOrigen(origen)}</button>
        ))}
      </div>

      {conjuntosFiltrados.length === 0 ? <EmptyState mensaje="No hay conjuntos de APs para el filtro seleccionado." /> : (
        <div className={styles.tablaWrapper}>
          <table className={styles.tabla}>
            <thead><tr><th>Conjunto</th><th>Plano</th><th>Origen</th><th>Estado</th><th>APs</th><th>Acciones</th></tr></thead>
            <tbody>{conjuntosFiltrados.map((conjunto) => (
              <tr key={conjunto.id}>
                <td className={styles.nombre}><strong>{conjunto.nombre}</strong><small>{conjunto.proposito}</small></td>
                <td>{planosPorId.get(conjunto.plano_id)?.nombre ?? `Plano #${conjunto.plano_id}`}</td>
                <td>{_labelOrigen(conjunto.origen)}</td>
                <td><Badge variante="en_progreso" etiqueta={_labelEstado(conjunto.estado_gobernanza)} /></td>
                <td>{conjunto.cantidad_aps}</td>
                <td><div className={styles.acciones}>
                  <Button variante="ghost" tamano="sm" onClick={() => revisar(conjunto)}><Eye size={14} aria-hidden="true" /> Revisar</Button>
                  <Button variante="ghost" tamano="sm" onClick={() => abrirEdicion(conjunto)}><Edit3 size={14} aria-hidden="true" /> Editar</Button>
                  <Button variante="secondary" tamano="sm" disabled={cambiando} onClick={() => handleEstado(conjunto, "aprobado_interno")}><CheckCircle2 size={14} aria-hidden="true" /> Aprobar</Button>
                  <Button variante="secondary" tamano="sm" disabled={cambiando} onClick={() => handleEstado(conjunto, "publicado_cliente")}><Send size={14} aria-hidden="true" /> Publicar</Button>
                  <Button variante="ghost" tamano="sm" disabled={cambiando} onClick={() => handleEstado(conjunto, "descartado")}><XCircle size={14} aria-hidden="true" /> Descartar</Button>
                </div></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}

      {conjuntoRevision && (
        <section className={styles.revision}>
          <div className={styles.revisionHeader}><div><h2>{conjuntoRevision.nombre}</h2><p>{conjuntoRevision.cantidad_aps} APs disponibles para revisión.</p></div><MapIcon size={20} aria-hidden="true" /></div>
          <div className={styles.modos}>
            {(["INDIVIDUAL", "SUBCONJUNTO", "CONJUNTO_COMPLETO"] as ModoHeatmap[]).map((item) => <button key={item} type="button" className={modo === item ? styles.modoActivo : ""} onClick={() => { setModo(item); if (item === "CONJUNTO_COMPLETO") setBssidsHeatmap(new Set(conjuntoRevision.items.map((ap) => ap.bssid))); else setBssidsHeatmap(new Set()); }}>{_labelModo(item)}</button>)}
          </div>
          {modo !== "CONJUNTO_COMPLETO" && <div className={styles.apSelector}>{conjuntoRevision.items.map((ap) => <label key={ap.bssid}><input type="checkbox" checked={bssidsHeatmap.has(ap.bssid)} onChange={() => setBssidsHeatmap((prev) => _toggleTexto(prev, ap.bssid))} /><span><strong>{ap.ssid || "SSID oculto"}</strong><small>{ap.bssid}</small></span></label>)}</div>}
          <div className={styles.accionesEditor}><Button type="button" isLoading={generando} onClick={generarMapa}>Generar heatmap</Button>{mapaGenerado && <Button type="button" variante="secondary" isLoading={analizando} onClick={analizarMapa}><Activity size={15} aria-hidden="true" /> Analizar</Button>}</div>
          {mapaGenerado && <VistaMapa mapa={mapaGenerado} titulo="Heatmap generado" />}

          <div className={styles.comparacionTemporal}>
            <h3>Comparación temporal</h3>
            <div className={styles.selectoresTemporales}>
              <select value={mapaTemporalA ?? ""} onChange={(e) => setMapaTemporalA(Number(e.target.value) || null)}><option value="">Mapa anterior</option>{mapasRevision.map((mapa) => <option key={mapa.id} value={mapa.id}>{_fechaMapa(mapa)}</option>)}</select>
              <select value={mapaTemporalB ?? ""} onChange={(e) => setMapaTemporalB(Number(e.target.value) || null)}><option value="">Mapa posterior</option>{mapasRevision.map((mapa) => <option key={mapa.id} value={mapa.id}>{_fechaMapa(mapa)}</option>)}</select>
            </div>
            {mapaTemporalA && mapaTemporalB && <div className={styles.mapasComparados}><VistaMapa mapa={mapasPorId.get(mapaTemporalA)!} titulo="Anterior" /><VistaMapa mapa={mapasPorId.get(mapaTemporalB)!} titulo="Posterior" /></div>}
          </div>
        </section>
      )}
    </section>
  );
}

function VistaMapa({ mapa, titulo }: { mapa: MapaCalorOut; titulo: string }) {
  return <figure className={styles.vistaMapa}><figcaption>{titulo} · {mapa.modo_generacion}</figcaption><img src={mapa.url_imagen} alt={`${titulo} de ${mapa.ssid || mapa.bssid}`} /><small>{mapa.rssi_min.toFixed(1)} a {mapa.rssi_max.toFixed(1)} dBm · {mapa.cantidad_puntos} puntos</small></figure>;
}

function ResumenItem({ etiqueta, valor }: { etiqueta: string; valor: number }) {
  return <div className={styles.resumenItem}><span>{etiqueta}</span><strong>{valor}</strong></div>;
}

function _toggleTexto(prev: Set<string>, valor: string): Set<string> {
  const siguiente = new Set(prev);
  if (siguiente.has(valor)) siguiente.delete(valor); else siguiente.add(valor);
  return siguiente;
}

function _resumenConjuntos(conjuntos: ConjuntoAPOut[]) {
  return conjuntos.reduce((acc, conjunto) => {
    if (conjunto.origen in acc) acc[conjunto.origen as "manual_movil" | "manual_web" | "ia"] += 1;
    if (conjunto.estado_gobernanza === "publicado_cliente") acc.publicado_cliente += 1;
    return acc;
  }, { manual_movil: 0, manual_web: 0, ia: 0, publicado_cliente: 0 });
}

function _fechaMapa(mapa: MapaCalorOut): string {
  return `${new Date(mapa.created_at).toLocaleString("es-BO")} · ${_labelModo(mapa.modo_generacion as ModoHeatmap)}`;
}

function _labelModo(modo: ModoHeatmap): string {
  return { INDIVIDUAL: "AP individual", SUBCONJUNTO: "Subconjunto", CONJUNTO_COMPLETO: "Conjunto completo" }[modo];
}

function _labelOrigen(origen: string): string {
  return ({ todos: "Todos", manual_movil: "Móvil", manual_web: "Web", ia: "IA" } as Record<string, string>)[origen] ?? origen;
}

function _labelEstado(estado: string): string {
  return ({ borrador_tecnico: "Borrador técnico", preliminar: "Preliminar", pendiente_revision: "Pendiente revisión", aprobado_interno: "Aprobado interno", publicado_cliente: "Publicado cliente", descartado: "Descartado" } as Record<string, string>)[estado] ?? estado;
}
