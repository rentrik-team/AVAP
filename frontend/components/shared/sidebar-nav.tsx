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
            const trigger = (
              <Link
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className="block"
              >
                <span
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    collapsed && "justify-center px-0",
                    isActive && "bg-accent text-accent-foreground",
                    !isActive &&
                      "text-foreground/80 hover:bg-accent/60 hover:text-accent-foreground"
                  )}
                >
                  <item.icon className="size-4.5 shrink-0" aria-hidden="true" />
                  {!collapsed && <span className="flex-1 truncate">{item.label}</span>}
                </span>
              </Link>
            );

            if (!collapsed) {
              return <div key={item.href}>{trigger}</div>;
            }

            return (
              <Tooltip key={item.href}>
                <TooltipTrigger asChild>{trigger}</TooltipTrigger>
                <TooltipContent side="right">{item.label}</TooltipContent>
              </Tooltip>
            );
          })}
        </div>
      ))}
    </nav>
  );
}
