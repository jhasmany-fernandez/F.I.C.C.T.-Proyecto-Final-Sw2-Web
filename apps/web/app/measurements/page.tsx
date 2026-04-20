import { PageIntro } from "@/components/page-intro";
import { SectionCard } from "@/components/section-card";
import { recentMeasurements, summaryStats } from "@/lib/data";

export default function MeasurementsPage() {
  return (
    <>
      <PageIntro
        eyebrow="Mediciones"
        title="Lecturas y puntos capturados"
        description="Vista inicial para conectar las mediciones del movil con una capa web de consulta, filtros y exportacion."
      />

      <section className="stats-grid stats-grid--compact">
        {summaryStats.slice(0, 3).map((stat) => (
          <article className={`stat-card stat-card--${stat.tone}`} key={stat.label}>
            <p className="stat-card__label">{stat.label}</p>
            <h2 className="stat-card__value">{stat.value}</h2>
            <p className="stat-card__detail">{stat.detail}</p>
          </article>
        ))}
      </section>

      <section className="page-grid page-grid--single">
        <SectionCard
          title="Tabla de mediciones"
          subtitle="Modelo listo para mostrar coordenadas, SSID, banda y calidad de senal"
        >
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Punto</th>
                  <th>Plano</th>
                  <th>SSID</th>
                  <th>Banda</th>
                  <th>RSSI</th>
                  <th>Hora</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {recentMeasurements.map((measurement) => (
                  <tr key={`${measurement.point}-${measurement.capturedAt}`}>
                    <td>{measurement.point}</td>
                    <td>{measurement.plan}</td>
                    <td>{measurement.ssid}</td>
                    <td>{measurement.band}</td>
                    <td>{measurement.rssi}</td>
                    <td>{measurement.capturedAt}</td>
                    <td>
                      <span className={`status-badge status-badge--${measurement.tone}`}>
                        {measurement.quality}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </section>
    </>
  );
}
