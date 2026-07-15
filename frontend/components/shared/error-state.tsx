"use client";

import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";

/**
 * Actionable, sanitized error surface. Never renders the raw error message
 * from the backend/Axios — only a fixed, human-readable summary plus a
 * retry action, per the "no stack traces to users" security requirement.
 */
export function ErrorState({
  title = "Unable to load this data",
  description = "The request could not be completed. Please try again.",
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center gap-3 py-10 text-center"
    >
      <span className="flex size-10 items-center justify-center rounded-full bg-destructive-bg text-destructive">
        <AlertTriangle className="size-5" aria-hidden="true" />
      </span>
      <div>
        <p className="text-sm font-medium text-foreground">{title}</p>
        <p className="mt-1 max-w-xs text-sm text-muted-foreground">{description}</p>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
