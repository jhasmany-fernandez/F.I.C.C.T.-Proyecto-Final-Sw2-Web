import type { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
  children: ReactNode;
};

export function SectionCard({
  title,
  subtitle,
  action,
  className,
  children,
}: SectionCardProps) {
  const classes = ["surface-card", className].filter(Boolean).join(" ");

  return (
    <section className={classes}>
      <header className="surface-card__header">
        <div>
          <h2 className="surface-card__title">{title}</h2>
          {subtitle ? <p className="surface-card__subtitle">{subtitle}</p> : null}
        </div>
        {action ? <div className="surface-card__action">{action}</div> : null}
      </header>
      <div className="surface-card__body">{children}</div>
    </section>
  );
}
