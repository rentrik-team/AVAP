import type { ServiceResponse } from "@/features/assets/types/asset";

/**
 * Static technical display only — never a clickable URL, "Open Service", or
 * connectivity action. The frontend must never construct a protocol URL
 * from scanner metadata or otherwise imply it can probe discovered
 * infrastructure (design_system.md security rules / this phase's brief).
 */
export function ServiceList({ services }: { services: ServiceResponse[] }) {
  if (services.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-muted-foreground">
        No open services discovered for this asset.
      </p>
    );
  }

  return (
    <ul className="flex flex-col divide-y divide-border">
      {services.map((service) => (
        <li
          key={service.id}
          className="flex flex-wrap items-center justify-between gap-3 py-3"
        >
          <div className="flex items-center gap-3">
            <span className="shrink-0 rounded-md bg-muted px-2 py-1 font-mono text-sm font-medium text-foreground">
              {service.port}/{service.protocol.toUpperCase()}
            </span>
            <span className="text-sm text-foreground">{service.service_name}</span>
          </div>
          {(service.product || service.version) && (
            <span className="text-sm text-muted-foreground">
              {[service.product, service.version].filter(Boolean).join(" ")}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}
