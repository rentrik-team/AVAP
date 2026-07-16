"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { isInvalidPortFilter, parsePortFilter } from "@/features/assets/lib/filters";
import type { AssetListFilters } from "@/features/assets/types/asset";
import { useDebouncedValue } from "@/hooks/use-debounced-value";

/**
 * Owns raw filter input and debouncing; emits committed, backend-shaped
 * filters via `onFilterChange`. `onFilterChange` must be a stable
 * reference (e.g. a useState setter) — it is an effect dependency here by
 * design, not suppressed.
 */
export function AssetFilterBar({
  onFilterChange,
}: {
  onFilterChange: (filters: AssetListFilters) => void;
}) {
  const [ip, setIp] = useState("");
  const [hostname, setHostname] = useState("");
  const [port, setPort] = useState("");
  const [cve, setCve] = useState("");

  const debouncedIp = useDebouncedValue(ip);
  const debouncedHostname = useDebouncedValue(hostname);
  const debouncedPort = useDebouncedValue(port);
  const debouncedCve = useDebouncedValue(cve);

  useEffect(() => {
    onFilterChange({
      ip: debouncedIp.trim() || undefined,
      hostname: debouncedHostname.trim() || undefined,
      port: parsePortFilter(debouncedPort),
      cve: debouncedCve.trim() || undefined,
    });
  }, [debouncedIp, debouncedHostname, debouncedPort, debouncedCve, onFilterChange]);

  const hasActiveInput = Boolean(ip || hostname || port || cve);
  const portInvalid = isInvalidPortFilter(debouncedPort);

  function handleClear() {
    setIp("");
    setHostname("");
    setPort("");
    setCve("");
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="asset-filter-ip">IP address</Label>
          <Input
            id="asset-filter-ip"
            placeholder="192.168.1.10"
            autoComplete="off"
            value={ip}
            onChange={(event) => setIp(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="asset-filter-hostname">Hostname</Label>
          <Input
            id="asset-filter-hostname"
            placeholder="web-server"
            autoComplete="off"
            value={hostname}
            onChange={(event) => setHostname(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="asset-filter-port">Port</Label>
          <Input
            id="asset-filter-port"
            inputMode="numeric"
            placeholder="443"
            autoComplete="off"
            value={port}
            onChange={(event) => setPort(event.target.value)}
            aria-invalid={portInvalid}
            aria-describedby={portInvalid ? "asset-filter-port-error" : undefined}
          />
          {portInvalid && (
            <p id="asset-filter-port-error" role="alert" className="text-xs text-destructive">
              Enter a port between 1 and 65535.
            </p>
          )}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="asset-filter-cve">CVE</Label>
          <Input
            id="asset-filter-cve"
            placeholder="CVE-2024-12345"
            autoComplete="off"
            value={cve}
            onChange={(event) => setCve(event.target.value)}
          />
        </div>
      </div>
      {hasActiveInput && (
        <Button
          variant="ghost"
          size="sm"
          className="w-fit text-muted-foreground"
          onClick={handleClear}
        >
          Clear filters
        </Button>
      )}
    </div>
  );
}
