import type { LucideIcon } from "lucide-react";
import {
  Crosshair,
  FileText,
  Gauge,
  LayoutDashboard,
  Radar,
  ScrollText,
  Server,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  /** False for backend resources not yet implemented in the frontend. */
  enabled: boolean;
}

export interface NavSection {
  label: string | null;
  items: NavItem[];
}

/**
 * Navigation taxonomy aligned to existing backend resources (Modules
 * 01–10). Only Overview (the Module 09 dashboard) is implemented in this
 * phase; the rest are shown as deliberately disabled upcoming sections
 * rather than fake pages, per the phased frontend delivery plan.
 */
export const NAV_SECTIONS: NavSection[] = [
  {
    label: null,
    items: [{ label: "Overview", href: "/", icon: LayoutDashboard, enabled: true }],
  },
  {
    label: "Operations",
    items: [
      { label: "Targets", href: "/targets", icon: Crosshair, enabled: false },
      { label: "Scans", href: "/scans", icon: Radar, enabled: false },
    ],
  },
  {
    label: "Security",
    items: [
      { label: "Assets", href: "/assets", icon: Server, enabled: false },
      {
        label: "Vulnerabilities",
        href: "/vulnerabilities",
        icon: ShieldAlert,
        enabled: false,
      },
      { label: "Risk", href: "/risk", icon: Gauge, enabled: false },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { label: "AI Remediation", href: "/ai", icon: Sparkles, enabled: false },
    ],
  },
  {
    label: "Outputs",
    items: [{ label: "Reports", href: "/reports", icon: FileText, enabled: false }],
  },
  {
    label: "System",
    items: [
      { label: "Audit Events", href: "/audit", icon: ScrollText, enabled: false },
    ],
  },
];
