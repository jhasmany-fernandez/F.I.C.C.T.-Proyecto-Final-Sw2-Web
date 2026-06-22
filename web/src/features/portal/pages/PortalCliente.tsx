import { useEffect, useMemo, useRef, useState, type PointerEvent } from "react";
import {
  Activity,
  Download,
  Layers3,
  MapPinned,
  Minus,
  Plus,
  RadioTower,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { obtenerPortalCliente, urlReportePortal } from "../api/shareClient";
import type {
  AnalisisCoberturaOut,
  EscenarioOptimizadoOut,
  MapaCalorPortalOut,
  PortalClienteOut,
} from "@/features/admin/types";
import styles from "./PortalCliente.module.css";

const CANVAS_W = 960;
const CANVAS_H = 560;

export default function PortalCliente() {
  const { token = "" } = useParams();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["portal-cliente", token],
    queryFn: () => obtenerPortalCliente(token),
    enabled: token.length > 0,
    retry: false,
  });
  const [mapaActivoId, setMapaActivoId] = useState<number | null>(null);

  const mapaActivo = useMemo(
    () =>
      data?.heatmaps.find((mapa) => mapa.id === mapaActivoId) ??
      data?.heatmaps[0] ??
      null,
    [data?.heatmaps, mapaActivoId],
  );
  const analisisActivo = useMemo(
    () =>
      mapaActivo
        ? data?.analisis.find((item) => item.mapa_calor_id === mapaActivo.id) ?? null
        : null,
    [data?.analisis, mapaActivo],
  );

  if (isLoading) {
    return <div className={styles.estado}>Cargando publicación...</div>;
  }

  if (isError || !data) {
    return (
      <div className={styles.estado}>
        <h1>Enlace no disponible</h1>
        <p>La publicación no existe, expiró o fue revocada por Bulldog Tech.</p>
      </div>
    );
  }

  return (
    <main className={styles.portal}>
      <header className={styles.encabezado}>
        <div>
          <span className={styles.marca}>Bulldog Tech.</span>
          <h1>{data.proyecto.nombre}</h1>
          <p>{data.proyecto.cliente ?? "Cliente"}</p>
        </div>
        {data.reporte_disponible && (
          <a className={styles.descarga} href={urlReportePortal(token)}>
            <Download size={18} aria-hidden="true" />
            Descargar reporte
          </a>
        )}
      </header>

      <section className={styles.layout}>
        <div className={styles.panelMapa}>
          <div className={styles.panelHeader}>
            <MapPinned size={18} aria-hidden="true" />
            <h2>Heatmaps publicados</h2>
          </div>

          {data.heatmaps.length === 0 ? (
            <div className={styles.vacio}>No hay heatmaps publicados en este enlace.</div>
          ) : (
            <>
              <div className={styles.tabs}>
                {data.heatmaps.map((mapa) => (
                  <button
                    key={mapa.id}
                    className={mapa.id === mapaActivo?.id ? styles.tabActiva : ""}
                    onClick={() => setMapaActivoId(mapa.id)}
                    type="button"
                  >
                    {mapa.ssid || mapa.bssid || `Mapa #${mapa.id}`}
                  </button>
                ))}
              </div>
              {mapaActivo && <HeatmapCanvas mapa={mapaActivo} />}
            </>
          )}
        </div>

        <aside className={styles.panelLateral}>
          <ResumenProyecto data={data} />
          {analisisActivo && <AnalisisResumen analisis={analisisActivo} />}
        </aside>
      </section>

      <section className={styles.bloque}>
        <div className={styles.panelHeader}>
          <Layers3 size={18} aria-hidden="true" />
          <h2>Conjuntos de APs publicados</h2>
        </div>
        {data.conjuntos.length === 0 ? (
          <div className={styles.vacio}>No hay conjuntos publicados en este enlace.</div>
        ) : (
          <div className={styles.conjuntos}>
            {data.conjuntos.map((conjunto) => (
              <article key={conjunto.id} className={styles.conjunto}>
                <div>
                  <h3>{conjunto.nombre}</h3>
                  <p>{conjunto.proposito}</p>
                  {conjunto.descripcion && <p>{conjunto.descripcion}</p>}
                </div>
                <div className={styles.apsConjunto}>
                  {conjunto.items.map((ap) => (
                    <span key={ap.bssid}>
                      {ap.ssid || "SSID oculto"} · {ap.bssid}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {data.analisis.length > 0 && (
        <section className={styles.bloque}>
          <div className={styles.panelHeader}>
            <Activity size={18} aria-hidden="true" />
            <h2>Análisis publicados</h2>
          </div>
          <div className={styles.analisisPublicados}>
            {data.analisis.map((analisis) => (
              <AnalisisResumen key={analisis.id} analisis={analisis} />
            ))}
          </div>
        </section>
      )}

      <section className={styles.bloque}>
        <div className={styles.panelHeader}>
          <RadioTower size={18} aria-hidden="true" />
          <h2>Alternativas publicadas</h2>
        </div>
        {data.escenarios.length === 0 ? (
          <div className={styles.vacio}>No hay alternativas IA publicadas en este enlace.</div>
        ) : (
          <div className={styles.escenarios}>
            {data.escenarios.map((escenario) => (
              <EscenarioCard key={escenario.id} escenario={escenario} />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

function HeatmapCanvas({ mapa }: { mapa: MapaCalorPortalOut }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const dragRef = useRef(false);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    valor: number;
  } | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);
    ctx.fillStyle = "#f7f8fa";
    ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

    const filas = mapa.matriz.length;
    const columnas = mapa.matriz[0]?.length ?? 0;
    if (filas === 0 || columnas === 0) return;

    const celda = Math.min(CANVAS_W / columnas, CANVAS_H / filas) * zoom;
    const origenX = (CANVAS_W - columnas * celda) / 2 + offset.x;
    const origenY = (CANVAS_H - filas * celda) / 2 + offset.y;

    mapa.matriz.forEach((fila, y) => {
      fila.forEach((valor, x) => {
        ctx.fillStyle = _colorRssi(valor, mapa.escala);
        ctx.fillRect(origenX + x * celda, origenY + y * celda, celda + 0.4, celda + 0.4);
      });
    });

    ctx.fillStyle = "#111827";
    mapa.puntos_lectura.forEach((punto) => {
      const x = origenX + (punto.pos_x / Math.max(mapa.resolucion - 1, 1)) * columnas * celda;
      const y = origenY + (punto.pos_y / Math.max(mapa.resolucion - 1, 1)) * filas * celda;
      ctx.beginPath();
      ctx.arc(x, y, 3.5, 0, Math.PI * 2);
      ctx.fill();
    });
  }, [mapa, offset, zoom]);

  const actualizarTooltip = (event: PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const xCanvas = ((event.clientX - rect.left) / rect.width) * CANVAS_W;
    const yCanvas = ((event.clientY - rect.top) / rect.height) * CANVAS_H;
    const filas = mapa.matriz.length;
    const columnas = mapa.matriz[0]?.length ?? 0;
    if (filas === 0 || columnas === 0) return;

    const celda = Math.min(CANVAS_W / columnas, CANVAS_H / filas) * zoom;
    const origenX = (CANVAS_W - columnas * celda) / 2 + offset.x;
    const origenY = (CANVAS_H - filas * celda) / 2 + offset.y;
    const col = Math.floor((xCanvas - origenX) / celda);
    const row = Math.floor((yCanvas - origenY) / celda);
    const valor = mapa.matriz[row]?.[col];
    setTooltip(
      typeof valor === "number"
        ? { x: event.clientX - rect.left, y: event.clientY - rect.top, valor }
        : null,
    );
  };

  return (
    <div className={styles.canvasWrap}>
      <div className={styles.toolbarMapa}>
        <button type="button" onClick={() => setZoom((prev) => Math.max(prev - 0.2, 0.6))}>
          <Minus size={16} aria-hidden="true" />
        </button>
        <span>{Math.round(zoom * 100)}%</span>
        <button type="button" onClick={() => setZoom((prev) => Math.min(prev + 0.2, 2.6))}>
          <Plus size={16} aria-hidden="true" />
        </button>
      </div>
      <canvas
        ref={canvasRef}
        width={CANVAS_W}
        height={CANVAS_H}
        onPointerDown={(event) => {
          dragRef.current = true;
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerLeave={() => setTooltip(null)}
        onPointerMove={(event) => {
          if (dragRef.current) {
            setOffset((prev) => ({ x: prev.x + event.movementX, y: prev.y + event.movementY }));
          }
          actualizarTooltip(event);
        }}
        onPointerUp={(event) => {
          dragRef.current = false;
          event.currentTarget.releasePointerCapture(event.pointerId);
        }}
      />
      {tooltip && (
        <div className={styles.tooltip} style={{ left: tooltip.x + 12, top: tooltip.y + 12 }}>
          {tooltip.valor.toFixed(1)} dBm
        </div>
      )}
      <div className={styles.leyenda}>
        {mapa.escala.map((item) => (
          <span key={`${item.desde}-${item.hasta}`}>
            <i style={{ background: item.color }} />
            {item.etiqueta}
          </span>
        ))}
      </div>
    </div>
  );
}

function ResumenProyecto({ data }: { data: PortalClienteOut }) {
  return (
    <section className={styles.resumen}>
      <h2>Resumen</h2>
      <dl>
        <div>
          <dt>Planos</dt>
          <dd>{data.planos.length}</dd>
        </div>
        <div>
          <dt>Conjuntos</dt>
          <dd>{data.conjuntos.length}</dd>
        </div>
        <div>
          <dt>Heatmaps</dt>
          <dd>{data.heatmaps.length}</dd>
        </div>
        <div>
          <dt>Alternativas</dt>
          <dd>{data.escenarios.length}</dd>
        </div>
      </dl>
    </section>
  );
}

function AnalisisResumen({ analisis }: { analisis: AnalisisCoberturaOut }) {
  return (
    <section className={styles.resumen}>
      <h2>Análisis</h2>
      <p>{analisis.resumen}</p>
      <dl>
        <div>
          <dt>Cobertura</dt>
          <dd>{analisis.pct_cobertura.toFixed(1)}%</dd>
        </div>
        <div>
          <dt>Zonas muertas</dt>
          <dd>{analisis.pct_zonas_muertas.toFixed(1)}%</dd>
        </div>
        <div>
          <dt>APs detectados</dt>
          <dd>{analisis.aps_detectados.length}</dd>
        </div>
      </dl>
    </section>
  );
}

function EscenarioCard({ escenario }: { escenario: EscenarioOptimizadoOut }) {
  return (
    <article className={styles.escenario}>
      <div>
        <h3>{escenario.nombre}</h3>
        <p>{escenario.resumen}</p>
      </div>
      <div className={styles.metricas}>
        <span>{escenario.pct_cobertura.toFixed(1)}% cobertura</span>
        <span>{escenario.cantidad_aps} APs</span>
        <span>{escenario.bandas.join(" / ")} GHz</span>
        <span>Confianza {escenario.confianza}</span>
      </div>
      <div className={styles.recomendaciones}>
        {escenario.recomendaciones.map((rec) => (
          <span key={rec.id}>
            {rec.accion}: x {rec.coord_x.toFixed(0)} / y {rec.coord_y.toFixed(0)}
          </span>
        ))}
      </div>
    </article>
  );
}

function _colorRssi(
  valor: number,
  escala: Array<{ desde: number; hasta: number; color: string }>,
): string {
  const tramo = escala.find((item) => valor >= item.desde && valor <= item.hasta);
  if (tramo) return tramo.color;
  if (valor >= -70) return "#2ecc71";
  if (valor >= -80) return "#f1c40f";
  if (valor >= -90) return "#e67e22";
  return "#c0392b";
}
