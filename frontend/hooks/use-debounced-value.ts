"use client";

import { useEffect, useState } from "react";

/**
 * Debounces a rapidly-changing value (e.g. free-text filter input) so a
 * server request fires only once the user pauses, not on every keystroke.
 * Shared by the Assets and Vulnerabilities filter bars — a plain
 * setTimeout/useEffect is sufficient; no dependency is needed for this.
 */
export function useDebouncedValue<T>(value: T, delayMs = 350): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timeout = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timeout);
  }, [value, delayMs]);

  return debounced;
}
