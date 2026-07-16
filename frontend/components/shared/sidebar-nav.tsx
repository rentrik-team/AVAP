"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { NAV_SECTIONS } from "@/constants/navigation";
import { cn } from "@/lib/utils";

export function SidebarNav({ collapsed = false }: { collapsed?: boolean }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-1 flex-col gap-5 overflow-y-auto px-3 py-4">
      {NAV_SECTIONS.map((section, index) => (
        <div key={section.label ?? `section-${index}`} className="flex flex-col gap-1">
          {section.label && !collapsed && (
            <h2 className="px-3 pb-1 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
              {section.label}
            </h2>
          )}
          {section.items.map((item) => {
            // "/" only matches exactly; other items also match their own
            // sub-routes (e.g. "/scans/{id}" under "/scans") now that
            // Targets/Scans introduce nested routes.
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
            const content = (
              <span
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  collapsed && "justify-center px-0",
                  item.enabled && isActive && "bg-accent text-accent-foreground",
                  item.enabled &&
                    !isActive &&
                    "text-foreground/80 hover:bg-accent/60 hover:text-accent-foreground",
                  !item.enabled && "text-muted-foreground/60"
                )}
              >
                <item.icon className="size-4.5 shrink-0" aria-hidden="true" />
                {!collapsed && <span className="flex-1 truncate">{item.label}</span>}
                {!collapsed && !item.enabled && (
                  <span className="rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                    Soon
                  </span>
                )}
              </span>
            );

            const trigger = item.enabled ? (
              <Link
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className="block"
              >
                {content}
              </Link>
            ) : (
              <span
                aria-disabled="true"
                aria-label={`${item.label} — not yet available`}
                className="block cursor-not-allowed"
              >
                {content}
              </span>
            );

            if (!collapsed) {
              return <div key={item.href}>{trigger}</div>;
            }

            return (
              <Tooltip key={item.href}>
                <TooltipTrigger asChild>{trigger}</TooltipTrigger>
                <TooltipContent side="right">
                  {item.label}
                  {!item.enabled && " — coming soon"}
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>
      ))}
    </nav>
  );
}
