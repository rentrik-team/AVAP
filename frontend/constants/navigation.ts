import type { LucideIcon } from "lucide-react";
import {
  Bug,
  Crosshair,
  FileText,
  LayoutDashboard,
  Radar,
  ScrollText,
  Server,
  ShieldAlert,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export interface NavSection {
  label: string | null;
  items: NavItem[];
}

/**
 * Scan-centric product taxonomy — the sidebar mirrors the assessment
 * workflow (add a target → scan it → review what was discovered → act on
 * the outputs), not the backend module list.
 *
 * - Operations: the things you manage and run — Targets, the Scans that
 *   execute against them, and the Assets those scans discover.
 * - Security: what the platform concluded — Findings (deterministic
 *   risk-scored results from the Risk Engine, with AI remediation actions)
 *   and Vulnerabilities (the normalized identity catalog, including
 *   AI-inferred entries labelled as such).
 * - Outputs: generated artifacts and evidence — Reports and the
 *   append-only Audit trail.
 *
 * Risk and AI are deliberately NOT primary destinations: risk is
 * calculated from, and displayed on, a scan's detail page (the workflow
 * hub), and AI remediation is generated from a finding's remediation
 * sheet there and on /findings. Legacy /risk redirects to /findings.
 */
export const NAV_SECTIONS: NavSection[] = [
  {
    label: null,
    items: [{ label: "Overview", href: "/", icon: LayoutDashboard }],
  },
  {
    label: "Operations",
    items: [
      { label: "Targets", href: "/targets", icon: Crosshair },
      { label: "Scans", href: "/scans", icon: Radar },
      { label: "Assets", href: "/assets", icon: Server },
    ],
  },
  {
    label: "Security",
    items: [
      { label: "Findings", href: "/findings", icon: ShieldAlert },
      { label: "Vulnerabilities", href: "/vulnerabilities", icon: Bug },
    ],
  },
  {
    label: "Outputs",
    items: [
      { label: "Reports", href: "/reports", icon: FileText },
      { label: "Audit Events", href: "/audit", icon: ScrollText },
    ],
  },
];
