"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";

/** Click-to-copy technical value (IPv4, CVE id, etc.) with mono typography. */
export function CopyableValue({
  value,
  label,
  className,
}: {
  value: string;
  label?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("Couldn't copy to clipboard");
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={`Copy ${label ?? value} to clipboard`}
      className={cn(
        "group inline-flex items-center gap-1.5 rounded-md font-mono text-sm text-foreground hover:text-primary",
        className
      )}
    >
      <span className="truncate">{value}</span>
      {copied ? (
        <Check className="size-3.5 shrink-0 text-success" aria-hidden="true" />
      ) : (
        <Copy
          className="size-3.5 shrink-0 text-muted-foreground group-hover:text-primary"
          aria-hidden="true"
        />
      )}
    </button>
  );
}
