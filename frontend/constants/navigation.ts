import type { LucideIcon } from "lucide-react";
import {
  Crosshair,
  FileText,
  Gauge,
  LayoutDashboard,
  Radar,
  ScrollText,
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
 * has a route: Overview (09), Targets (01), Scans (02), Risk (06),
 * Reports (08), Audit Events (10).
 *
 * Assets and Vulnerabilities (Module 05) are intentionally NOT given their
 * own top-level nav entries: both are scanner-discovered inventory with no
 * meaning independent of the target that produced them, so a flat
 * ungrouped "everything at once" list would misrepresent the data. They're
 * reached target-wise instead, as sections on a Target's detail page
 * (/targets/{id}) — the per-entity detail routes (/assets/{id},
 * /vulnerabilities/{id}) still exist for drill-down from there.
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
    items: [{ label: "Risk", href: "/risk", icon: Gauge, enabled: true }],
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
