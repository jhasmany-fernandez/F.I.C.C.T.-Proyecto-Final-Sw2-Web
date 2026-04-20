import { PageIntro } from "@/components/page-intro";
import { SectionCard } from "@/components/section-card";
import { coverageZones, reportHighlights, signalTrend } from "@/lib/data";

export default function ReportsPage() {
  return (
    <>
      <PageIntro
        eyebrow="Reportes"
        title="Cobertura, observaciones y acciones sugeridas"
        description="Esta base deja preparado el frontend para convertir mediciones en hallazgos legibles sin depender todavia de un heatmap final."
      />

      <section className="page-grid">
        <SectionCard
          title="Resumen por zonas"
          subtitle="Prioridades de cobertura detectadas"
        >
          <div className="report-list">
            {coverageZones.map((zone) => (
              <article className="report-list__item" key={zone.zone}>
                <div>
                  <strong>{zone.zone}</strong>
                  <p>{zone.note}</p>
                </div>
                <span className={`status-badge status-badge--${zone.tone}`}>{zone.score}</span>
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          title="Evolucion semanal"
          subtitle="Lectura compacta para calidad media de senal"
        >
          <div className="mini-chart">
            {signalTrend.map((point) => (
              <div className="mini-chart__column" key={point.day}>
                <span className="mini-chart__value">{point.rssi} dBm</span>
                <span className="mini-chart__bar-wrap">
                  <span
                    className="mini-chart__bar"
                    style={{ height: `${point.score}%` }}
                  />
                </span>
                <span className="mini-chart__label">{point.day}</span>
              </div>
            ))}
          </div>
        </SectionCard>
      </section>

      <section className="page-grid page-grid--single">
        <SectionCard
          title="Hallazgos destacados"
          subtitle="Observaciones listas para convertirse en tarjetas de reporte"
        >
          <div className="stack-list">
            {reportHighlights.map((highlight) => (
              <div className="stack-list__item" key={highlight.title}>
                <div className="stack-list__row">
                  <strong>{highlight.title}</strong>
                  <span className={`status-badge status-badge--${highlight.tone}`}>
                    Prioridad
                  </span>
                </div>
                <span>{highlight.description}</span>
              </div>
            ))}
          </div>
        </SectionCard>
      </section>
    </>
  );
}
