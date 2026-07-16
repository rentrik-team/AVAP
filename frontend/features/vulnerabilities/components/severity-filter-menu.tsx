"use client";

import { ChevronDown } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

/**
 * Presentation labels are humanized ("Informational"); the value sent to
 * the backend is the exact raw severity_rating it expects — "None" is the
 * backend's own informational bucket (app/api/routes/v1/vulnerabilities.py),
 * not an invented label.
 */
const SEVERITY_FILTER_OPTIONS = [
  { label: "All severities", value: "" },
  { label: "Critical", value: "Critical" },
  { label: "High", value: "High" },
  { label: "Medium", value: "Medium" },
  { label: "Low", value: "Low" },
  { label: "Informational", value: "None" },
];

export function SeverityFilterMenu({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  const selected =
    SEVERITY_FILTER_OPTIONS.find((option) => option.value === value) ??
    SEVERITY_FILTER_OPTIONS[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" aria-label="Filter by severity" className="justify-between">
          {selected.label}
          <ChevronDown className="size-4 text-muted-foreground" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuRadioGroup value={value} onValueChange={onChange}>
          {SEVERITY_FILTER_OPTIONS.map((option) => (
            <DropdownMenuRadioItem key={option.value || "all"} value={option.value}>
              {option.label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
