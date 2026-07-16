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
 * 01–10). Every module with a genuine "browse a collection" endpoint now
 * has a route: Overview (09), Targets (01), Scans (02), Assets/
 * Vulnerabilities (05), Risk (06), Reports (08), Audit Events (10).
 *
 * AI Remediation (Module 07) is intentionally NOT given its own nav entry
 * or route: there is no `GET /ai/recommendations` collection endpoint to
 * list, only per-assessment retrieval — a standalone page would have
 * nothing to browse without first knowing a specific VULNERABILITY-scope
 * assessment id. AI remediation is reachable from the Risk page instead,
 * via the "Remediation" action on VULNERABILITY-scope rows.
 */
export const NAV_SECTIONS: NavSection[] = [
  {
    label: null,
    items: [{ label: "Overview", href: "/", icon: LayoutDashboard, enabled: true }],
  },
  {
    label: "Operations",
    items: [
      { label: "Targets", href: "/targets", icon: Crosshair, enabled: true },
      { label: "Scans", href: "/scans", icon: Radar, enabled: true },
    ],
  },
  {
    label: "Security",
    items: [
      { label: "Assets", href: "/assets", icon: Server, enabled: true },
      {
        label: "Vulnerabilities",
        href: "/vulnerabilities",
        icon: ShieldAlert,
        enabled: true,
      },
      { label: "Risk", href: "/risk", icon: Gauge, enabled: true },
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
    items: [{ label: "Reports", href: "/reports", icon: FileText, enabled: true }],
  },
  {
    label: "System",
    items: [
      { label: "Audit Events", href: "/audit", icon: ScrollText, enabled: true },
    ],
  },
];
