import Link from "next/link";

import { Icon } from "@/components/icons";
import { PageIntro } from "@/components/page-intro";
import { SectionCard } from "@/components/section-card";
import {
  activityFeed,
  floorPlans,
  recentMeasurements,
  signalTrend,
  summaryStats,
  taskBoard,
} from "@/lib/data";

export default function DashboardPage() {
  return (
    <>
      <PageIntro
        eyebrow="Wireless HeatMapper"
        title="Dashboard de cobertura y levantamiento"
        description="Base en Next.js para reutilizar la interfaz del tema actual y empezar a conectar datos reales de planos, puntos y escaneos WiFi."
        actions={
          <>
            <Link className="secondary-button" href="/floor-plans">
              Ver planos
            </Link>
            <Link className="primary-button" href="/measurements">
              Abrir mediciones
            </Link>
          </>
        }
      />

      <section className="stats-grid" aria-label="Resumen principal">
        {summaryStats.map((stat) => (
          <article className={`stat-card stat-card--${stat.tone}`} key={stat.label}>
            <div className="stat-card__icon">
              <Icon name={stat.icon} />
            </div>
            <p className="stat-card__label">{stat.label}</p>
            <h2 className="stat-card__value">{stat.value}</h2>
            <p className="stat-card__detail">{stat.detail}</p>
            <div className="progress-track">
              <span
                className={`progress-track__fill progress-track__fill--${stat.tone}`}
                style={{ width: `${stat.progress}%` }}
              />
            </div>
          </article>
        ))}
      </section>

      <section className="page-grid">
        <SectionCard
          title="Tendencia de intensidad"
          subtitle="Promedio diario de calidad de senal por jornada de medicion"
          action={<span className="status-badge status-badge--blue">Ultimos 7 dias</span>}
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

        <SectionCard title="Resumen operativo" subtitle="Estado rapido del trabajo de campo">
          <div className="stack-list">
            <div className="stack-list__item">
              <strong>Ultimo barrido completo</strong>
              <span>Biblioteca Este con 11 AP detectados y 6 puntos medidos.</span>
            </div>
            <div className="stack-list__item">
              <strong>Objetivo del sprint</strong>
              <span>Asociar mediciones reales sobre plano y persistirlas localmente.</span>
            </div>
            <div className="stack-list__item">
              <strong>Bloqueo actual</strong>
              <span>Falta terminar el relevo del Bloque Sur para cerrar cobertura.</span>
            </div>
          </div>
        </SectionCard>
      </section>

      <section className="page-grid">
        <SectionCard
          title="Ultimas mediciones"
          subtitle="Lecturas listas para conectarse a la capa de datos"
          action={<Link className="inline-link" href="/measurements">Ir al detalle</Link>}
        >
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Punto</th>
                  <th>Plano</th>
                  <th>SSID</th>
                  <th>RSSI</th>
                  <th>Calidad</th>
                </tr>
              </thead>
              <tbody>
                {recentMeasurements.map((measurement) => (
                  <tr key={`${measurement.point}-${measurement.capturedAt}`}>
                    <td>{measurement.point}</td>
                    <td>{measurement.plan}</td>
                    <td>{measurement.ssid}</td>
                    <td>{measurement.rssi}</td>
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

        <SectionCard title="Tareas activas" subtitle="Checklist del sprint actual">
          <ul className="check-list">
            {taskBoard.map((task) => (
              <li className="check-list__item" key={task.title}>
                <span
                  className={
                    task.done
                      ? "check-list__marker check-list__marker--done"
                      : "check-list__marker"
                  }
                />
                <div>
                  <strong>{task.title}</strong>
                  <p>{task.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        </SectionCard>
      </section>

      <section className="page-grid">
        <SectionCard
          title="Planos disponibles"
          subtitle="Vista previa de ambientes listos para captura"
          action={<Link className="inline-link" href="/floor-plans">Administrar</Link>}
        >
          <div className="plan-summary-grid">
            {floorPlans.map((plan) => (
              <article className="mini-plan-card" key={plan.name}>
                <div className="mini-plan-card__head">
                  <div>
                    <strong>{plan.name}</strong>
                    <p>{plan.location}</p>
                  </div>
                  <span className={`status-badge status-badge--${plan.tone}`}>
                    {plan.coverage}
                  </span>
                </div>
                <p className="mini-plan-card__meta">
                  {plan.points} puntos registrados · {plan.lastSync}
                </p>
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Actividad reciente" subtitle="Eventos relevantes del sistema">
          <ul className="timeline">
            {activityFeed.map((item) => (
              <li className="timeline__item" key={item.title}>
                <span className="timeline__dot" />
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                  <small>{item.time}</small>
                </div>
              </li>
            ))}
          </ul>
        </SectionCard>
      </section>
    </>
  );
}
