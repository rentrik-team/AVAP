import { clsx, type ClassValue } from "clsx"
import { extendTailwindMerge } from "tailwind-merge"

// design_system.md §7 defines a custom named type scale (text-display-lg,
// text-display, text-h1, text-h2, text-h3, text-title, text-caption,
// text-micro) alongside Tailwind's own default font-size scale. Without
// this, tailwind-merge doesn't know they conflict with e.g. "text-sm", so
// a component overriding its base size via className (e.g. RiskScore's
// "text-h1" in the Dashboard hero) would keep both classes instead of the
// override winning.
const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      "font-size": [
        "text-display-lg",
        "text-display",
        "text-h1",
        "text-h2",
        "text-h3",
        "text-title",
        "text-caption",
        "text-micro",
      ],
    },
  },
})

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
