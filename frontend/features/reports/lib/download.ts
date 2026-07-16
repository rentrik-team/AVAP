/**
 * Saves a Blob to the user's device using the standard temporary-anchor
 * pattern (native browser APIs only — no library). Filename mirrors the
 * backend's own Content-Disposition convention exactly
 * (`avap-report-<report_id>.pdf`, set server-side in
 * app/api/routes/v1/reports.py) rather than inventing a new one.
 */
export function triggerBrowserDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
