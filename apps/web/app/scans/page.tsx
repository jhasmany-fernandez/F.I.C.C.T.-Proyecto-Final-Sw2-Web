import { PageIntro } from "@/components/page-intro";
import { SectionCard } from "@/components/section-card";
import { scanChecklist, wifiNetworks } from "@/lib/data";

export default function ScansPage() {
  return (
    <>
      <PageIntro
        eyebrow="Escaneos"
        title="Redes detectadas y checklist de captura"
        description="Pantalla pensada para visualizar lo que llega desde Android: SSID, BSSID, canal, frecuencia y permisos operativos."
      />

      <section className="page-grid">
        <SectionCard
          title="Redes detectadas"
          subtitle="Muestra resumida de un barrido reciente"
        >
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>SSID</th>
                  <th>BSSID</th>
                  <th>Canal</th>
                  <th>Banda</th>
                  <th>RSSI</th>
                  <th>Seguridad</th>
                </tr>
              </thead>
              <tbody>
                {wifiNetworks.map((network) => (
                  <tr key={network.bssid}>
                    <td>{network.ssid}</td>
                    <td>{network.bssid}</td>
                    <td>{network.channel}</td>
                    <td>{network.band}</td>
                    <td>{network.rssi}</td>
                    <td>
                      <span className={`status-badge status-badge--${network.tone}`}>
                        {network.security}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <SectionCard
          title="Checklist del dispositivo"
          subtitle="Lo minimo para iniciar un barrido valido"
        >
          <ul className="check-list">
            {scanChecklist.map((item) => (
              <li className="check-list__item" key={item}>
                <span className="check-list__marker check-list__marker--done" />
                <div>
                  <strong>{item}</strong>
                  <p>Listo para enlazar con la app movil y persistir localmente.</p>
                </div>
              </li>
            ))}
          </ul>
        </SectionCard>
      </section>
    </>
  );
}
