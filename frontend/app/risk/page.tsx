import { redirect } from "next/navigation";

// The former Risk page now lives at /findings — risk itself belongs to the
// Scan Detail workflow, and the platform-wide list is framed as Findings.
// This permanent redirect keeps old bookmarks working.
export default function RiskPage() {
  redirect("/findings");
}
