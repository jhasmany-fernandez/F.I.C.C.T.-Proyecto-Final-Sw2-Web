import type { IconName } from "@/components/icons";

export type Tone = "emerald" | "blue" | "amber" | "rose";

export type SummaryStat = {
  label: string;
  value: string;
  detail: string;
  progress: number;
  icon: IconName;
  tone: Tone;
};

export type SignalTrendPoint = {
  day: string;
  score: number;
  rssi: string;
};

export type MeasurementRow = {
  point: string;
  plan: string;
  ssid: string;
  band: string;
  rssi: string;
  capturedAt: string;
  tone: Tone;
  quality: string;
};

export type TaskItem = {
  title: string;
  detail: string;
  done: boolean;
};

export type Hotspot = {
  x: string;
  y: string;
  tone: "good" | "warning" | "poor";
};

export type FloorPlan = {
  name: string;
  location: string;
  coverage: string;
  points: number;
  status: string;
  tone: Tone;
  lastSync: string;
  hotspots: Hotspot[];
};

export type ActivityItem = {
  title: string;
  time: string;
  description: string;
};

export type NetworkRow = {
  ssid: string;
  bssid: string;
  channel: string;
  band: string;
  rssi: string;
  security: string;
  tone: Tone;
};

export type ReportHighlight = {
  title: string;
  description: string;
  tone: Tone;
};

export type CoverageZone = {
  zone: string;
  score: string;
  note: string;
  tone: Tone;
};

export type SettingGroup = {
  title: string;
  description: string;
  items: Array<{
    label: string;
    value: string;
    hint: string;
  }>;
};

export const summaryStats: SummaryStat[] = [
  {
    label: "Planos activos",
    value: "12",
    detail: "3 nuevos ambientes cargados esta semana",
    progress: 72,
    icon: "plans",
    tone: "emerald",
  },
  {
    label: "Mediciones registradas",
    value: "1,284",
    detail: "84 puntos medidos en la ultima jornada",
    progress: 66,
    icon: "measurements",
    tone: "blue",
  },
  {
    label: "Promedio RSSI",
    value: "-58 dBm",
    detail: "Zona mas estable: biblioteca y laboratorios",
    progress: 81,
    icon: "signal",
    tone: "amber",
  },
  {
    label: "Escaneos pendientes",
    value: "09",
    detail: "Sectores con cobertura irregular por revisar",
    progress: 34,
    icon: "wifi",
    tone: "rose",
  },
];

export const signalTrend: SignalTrendPoint[] = [
  { day: "Lun", score: 58, rssi: "-63" },
  { day: "Mar", score: 64, rssi: "-60" },
  { day: "Mie", score: 71, rssi: "-57" },
  { day: "Jue", score: 69, rssi: "-58" },
  { day: "Vie", score: 76, rssi: "-54" },
  { day: "Sab", score: 67, rssi: "-59" },
  { day: "Dom", score: 74, rssi: "-55" },
];

export const recentMeasurements: MeasurementRow[] = [
  {
    point: "Pasillo A-03",
    plan: "Bloque Norte - Piso 1",
    ssid: "Campus-WiFi",
    band: "5 GHz",
    rssi: "-58 dBm",
    capturedAt: "09:18",
    tone: "emerald",
    quality: "Alta",
  },
  {
    point: "Laboratorio Redes",
    plan: "Bloque Norte - Piso 2",
    ssid: "Lab-Docentes",
    band: "5 GHz",
    rssi: "-64 dBm",
    capturedAt: "09:11",
    tone: "blue",
    quality: "Estable",
  },
  {
    point: "Biblioteca Este",
    plan: "Edificio Central",
    ssid: "Campus-WiFi",
    band: "2.4 GHz",
    rssi: "-72 dBm",
    capturedAt: "08:54",
    tone: "amber",
    quality: "Media",
  },
  {
    point: "Aula 3B",
    plan: "Bloque Sur - Piso 1",
    ssid: "Invitados",
    band: "2.4 GHz",
    rssi: "-81 dBm",
    capturedAt: "08:37",
    tone: "rose",
    quality: "Baja",
  },
];

export const taskBoard: TaskItem[] = [
  {
    title: "Validar permisos de ubicacion en Android",
    detail: "Necesario para mantener los escaneos reales activos.",
    done: true,
  },
  {
    title: "Cerrar puntos ciegos del laboratorio oeste",
    detail: "Faltan cuatro mediciones cerca del rack secundario.",
    done: false,
  },
  {
    title: "Sincronizar nombres de planos con backend",
    detail: "Evita inconsistencias al exportar lecturas a la API.",
    done: false,
  },
  {
    title: "Revisar canalizacion en red de invitados",
    detail: "Se detectaron superposiciones en 2.4 GHz.",
    done: true,
  },
];

export const floorPlans: FloorPlan[] = [
  {
    name: "Bloque Norte - Piso 1",
    location: "Campus Principal",
    coverage: "82%",
    points: 24,
    status: "Listo para analisis",
    tone: "emerald",
    lastSync: "Hace 12 min",
    hotspots: [
      { x: "18%", y: "28%", tone: "good" },
      { x: "52%", y: "40%", tone: "warning" },
      { x: "74%", y: "66%", tone: "good" },
    ],
  },
  {
    name: "Bloque Sur - Piso 1",
    location: "Campus Principal",
    coverage: "64%",
    points: 17,
    status: "Requiere nueva visita",
    tone: "amber",
    lastSync: "Hace 37 min",
    hotspots: [
      { x: "26%", y: "52%", tone: "warning" },
      { x: "48%", y: "30%", tone: "poor" },
      { x: "72%", y: "58%", tone: "warning" },
    ],
  },
  {
    name: "Edificio Central",
    location: "Biblioteca",
    coverage: "88%",
    points: 31,
    status: "Cobertura estable",
    tone: "blue",
    lastSync: "Hace 1 h",
    hotspots: [
      { x: "22%", y: "22%", tone: "good" },
      { x: "46%", y: "50%", tone: "good" },
      { x: "80%", y: "38%", tone: "good" },
    ],
  },
];

export const activityFeed: ActivityItem[] = [
  {
    title: "Se importo un plano nuevo",
    time: "Hace 8 min",
    description: "Bloque Norte - Piso 2 se agrego con 14 puntos iniciales.",
  },
  {
    title: "Escaneo completado",
    time: "Hace 19 min",
    description: "Campus-WiFi respondio con 11 AP detectados en la biblioteca.",
  },
  {
    title: "Sugerencia de mejora",
    time: "Hace 42 min",
    description: "El canal 6 presenta interferencia con la red de invitados.",
  },
];

export const wifiNetworks: NetworkRow[] = [
  {
    ssid: "Campus-WiFi",
    bssid: "CC:11:72:9A:44:01",
    channel: "44",
    band: "5 GHz",
    rssi: "-57 dBm",
    security: "WPA2 Enterprise",
    tone: "emerald",
  },
  {
    ssid: "Lab-Docentes",
    bssid: "CC:11:72:9A:44:08",
    channel: "36",
    band: "5 GHz",
    rssi: "-63 dBm",
    security: "WPA2",
    tone: "blue",
  },
  {
    ssid: "Invitados",
    bssid: "CC:11:72:9A:44:12",
    channel: "6",
    band: "2.4 GHz",
    rssi: "-76 dBm",
    security: "Portal cautivo",
    tone: "amber",
  },
  {
    ssid: "Backoffice-IoT",
    bssid: "CC:11:72:9A:44:17",
    channel: "1",
    band: "2.4 GHz",
    rssi: "-84 dBm",
    security: "WPA2 PSK",
    tone: "rose",
  },
];

export const reportHighlights: ReportHighlight[] = [
  {
    title: "Biblioteca con cobertura superior al objetivo",
    description: "Las mediciones se mantienen por encima de -60 dBm en horas pico.",
    tone: "emerald",
  },
  {
    title: "Aula 3B necesita recolocacion de AP",
    description: "Se registran caidas repetidas por debajo de -80 dBm en 2.4 GHz.",
    tone: "rose",
  },
  {
    title: "Canales de 5 GHz mejor distribuidos",
    description: "El ultimo barrido redujo interferencia entre laboratorios contiguos.",
    tone: "blue",
  },
];

export const coverageZones: CoverageZone[] = [
  {
    zone: "Biblioteca Este",
    score: "88%",
    note: "Cobertura consistente, ideal para trafico academico sostenido.",
    tone: "emerald",
  },
  {
    zone: "Laboratorio Oeste",
    score: "71%",
    note: "Buena capacidad, aunque con sombras cerca del rack secundario.",
    tone: "amber",
  },
  {
    zone: "Aulas del Bloque Sur",
    score: "63%",
    note: "Variabilidad alta cuando se llena el sector de estudiantes.",
    tone: "rose",
  },
];

export const scanChecklist = [
  "Permisos de ubicacion y WiFi habilitados en Android.",
  "Plano activo seleccionado antes de iniciar la captura.",
  "Coordenadas relativas visibles para cada punto medido.",
  "Persistencia local lista para guardar SSID, BSSID, RSSI y frecuencia.",
];

export const settingGroups: SettingGroup[] = [
  {
    title: "Captura en campo",
    description: "Parametros que afectan la recoleccion de datos desde el dispositivo.",
    items: [
      {
        label: "Frecuencia de escaneo",
        value: "Cada 15 segundos",
        hint: "Balancea bateria y granularidad de las lecturas.",
      },
      {
        label: "Precision de ubicacion",
        value: "Alta",
        hint: "Mejora la consistencia de coordenadas en interiores.",
      },
      {
        label: "Formato de guardado",
        value: "SQLite local",
        hint: "Compatible con exportaciones futuras hacia NestJS.",
      },
    ],
  },
  {
    title: "Integraciones",
    description: "Configuracion prevista para el backend y el flujo de sincronizacion.",
    items: [
      {
        label: "API base URL",
        value: "http://localhost:3000/api",
        hint: "Se usara cuando la capa web sincronice lecturas y planos.",
      },
      {
        label: "Modo de entorno",
        value: "development",
        hint: "Mantiene separadas las pruebas locales de futuras rutas productivas.",
      },
      {
        label: "Exportacion de reportes",
        value: "Pendiente",
        hint: "Espacio reservado para CSV, PDF y reportes comparativos.",
      },
    ],
  },
];
