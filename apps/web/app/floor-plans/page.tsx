import Link from "next/link";

import { PageIntro } from "@/components/page-intro";
import { SectionCard } from "@/components/section-card";
import { floorPlans } from "@/lib/data";

export default function FloorPlansPage() {
  return (
    <>
      <PageIntro
        eyebrow="Planos"
        title="Ambientes listos para relevamiento"
        description="Cada tarjeta usa el lenguaje visual del dashboard original, pero ya organizada para un flujo real de planos, puntos y cobertura."
        actions={
          <Link className="primary-button" href="/measurements">
            Ver puntos medidos
          </Link>
        }
      />

      <section className="plan-grid">
        {floorPlans.map((plan) => (
          <SectionCard
            key={plan.name}
            title={plan.name}
            subtitle={plan.location}
            action={<span className={`status-badge status-badge--${plan.tone}`}>{plan.status}</span>}
          >
            <div className="plan-preview">
              {plan.hotspots.map((hotspot, index) => (
                <span
                  key={`${plan.name}-${index}`}
                  className={`plan-preview__dot plan-preview__dot--${hotspot.tone}`}
                  style={{ left: hotspot.x, top: hotspot.y }}
                />
              ))}
            </div>

            <div className="metric-grid">
              <div className="metric-grid__item">
                <span>Cobertura estimada</span>
                <strong>{plan.coverage}</strong>
              </div>
              <div className="metric-grid__item">
                <span>Puntos medidos</span>
                <strong>{plan.points}</strong>
              </div>
              <div className="metric-grid__item">
                <span>Ultima sincronizacion</span>
                <strong>{plan.lastSync}</strong>
              </div>
            </div>
          </SectionCard>
        ))}
      </section>
    </>
  );
}
