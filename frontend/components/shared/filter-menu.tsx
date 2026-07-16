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
 * Generic labeled single-select filter dropdown (Radix DropdownMenuRadioGroup
 * under the hood) — the common shape behind every discrete server-side
 * filter across Risk/Audit (and, by the same pattern, Vulnerabilities'
 * severity filter). `""` always means "no filter applied" for a given
 * dimension, mapped to `undefined` by the caller before it reaches the API.
 */
export function FilterMenu<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { label: string; value: T | "" }[];
  value: T | "";
  onChange: (value: T | "") => void;
}) {
  const selected = options.find((option) => option.value === value) ?? options[0];
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" aria-label={label} className="justify-between">
          {selected.label}
          <ChevronDown className="size-4 text-muted-foreground" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuRadioGroup
          value={value}
          onValueChange={(next) => onChange(next as T | "")}
        >
          {options.map((option) => (
            <DropdownMenuRadioItem key={option.value || "all"} value={option.value}>
              {option.label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
