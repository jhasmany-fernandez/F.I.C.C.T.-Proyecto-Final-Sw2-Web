import type { ReactElement, SVGProps } from "react";

export type IconName =
  | "store"
  | "dashboard"
  | "plans"
  | "measurements"
  | "wifi"
  | "reports"
  | "settings"
  | "search"
  | "bell"
  | "user"
  | "signal";

type IconProps = SVGProps<SVGSVGElement> & {
  name: IconName;
};

type IconComponent = (props: SVGProps<SVGSVGElement>) => ReactElement;

const baseProps = {
  fill: "none",
  stroke: "currentColor",
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  strokeWidth: 1.8,
  viewBox: "0 0 24 24",
};

const icons: Record<IconName, IconComponent> = {
  store: (props) => (
    <svg {...baseProps} {...props}>
      <path d="M4 9.5 5.2 5h13.6L20 9.5" />
      <path d="M5 9.5V19a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9.5" />
      <path d="M9 13h6" />
      <path d="M9 17h4" />
    </svg>
  ),
  dashboard: (props) => (
    <svg {...baseProps} {...props}>
      <rect x="3" y="3" width="8" height="8" rx="2" />
      <rect x="13" y="3" width="8" height="5" rx="2" />
      <rect x="13" y="10" width="8" height="11" rx="2" />
      <rect x="3" y="13" width="8" height="8" rx="2" />
    </svg>
  ),
  plans: (props) => (
    <svg {...baseProps} {...props}>
      <path d="M4 6.5 12 3l8 3.5v11L12 21l-8-3.5Z" />
      <path d="M12 3v18" />
      <path d="M4 6.5 12 10l8-3.5" />
    </svg>
  ),
  measurements: (props) => (
    <svg {...baseProps} {...props}>
      <path d="M6 19V8" />
      <path d="M12 19V5" />
      <path d="M18 19v-9" />
      <path d="M4 19h16" />
    </svg>
  ),
  wifi: (props) => (
    <svg {...baseProps} {...props}>
      <path d="M2.5 8.5a15 15 0 0 1 19 0" />
      <path d="M5.5 12a10.5 10.5 0 0 1 13 0" />
      <path d="M8.75 15.5a6 6 0 0 1 6.5 0" />
      <circle cx="12" cy="19" r="1.25" fill="currentColor" stroke="none" />
    </svg>
  ),
  reports: (props) => (
    <svg {...baseProps} {...props}>
      <path d="M7 3h7l5 5v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" />
      <path d="M14 3v5h5" />
      <path d="M9 14h6" />
      <path d="M9 18h6" />
      <path d="M9 10h2" />
    </svg>
  ),
  settings: (props) => (
    <svg {...baseProps} {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1 1 0 0 0 .2 1.1l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1 1 0 0 0-1.1-.2 1 1 0 0 0-.6.9V20a2 2 0 1 1-4 0v-.2a1 1 0 0 0-.6-.9 1 1 0 0 0-1.1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1 1 0 0 0 .2-1.1 1 1 0 0 0-.9-.6H4a2 2 0 1 1 0-4h.2a1 1 0 0 0 .9-.6 1 1 0 0 0-.2-1.1l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1 1 0 0 0 1.1.2 1 1 0 0 0 .6-.9V4a2 2 0 1 1 4 0v.2a1 1 0 0 0 .6.9 1 1 0 0 0 1.1-.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1 1 0 0 0-.2 1.1 1 1 0 0 0 .9.6h.2a2 2 0 1 1 0 4h-.2a1 1 0 0 0-.9.6Z" />
    </svg>
  ),
  search: (props) => (
    <svg {...baseProps} {...props}>
      <circle cx="11" cy="11" r="6" />
      <path d="m20 20-4.2-4.2" />
    </svg>
  ),
  bell: (props) => (
    <svg {...baseProps} {...props}>
      <path d="M15 18H5.5a1 1 0 0 1-.8-1.6L6 14.5V10a6 6 0 1 1 12 0v4.5l1.3 1.9a1 1 0 0 1-.8 1.6H18" />
      <path d="M10 20a2 2 0 0 0 4 0" />
    </svg>
  ),
  user: (props) => (
    <svg {...baseProps} {...props}>
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 20a7 7 0 0 1 14 0" />
    </svg>
  ),
  signal: (props) => (
    <svg {...baseProps} {...props}>
      <path d="M4 18h2" />
      <path d="M8 14h2" />
      <path d="M12 10h2" />
      <path d="M16 6h2" />
      <path d="M5 18v-3" />
      <path d="M9 18v-7" />
      <path d="M13 18V7" />
      <path d="M17 18V3" />
    </svg>
  ),
};

export function Icon({ name, ...props }: IconProps) {
  const Component = icons[name];
  return <Component aria-hidden="true" {...props} />;
}
