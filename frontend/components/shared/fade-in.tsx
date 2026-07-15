"use client";

import { motion, useReducedMotion } from "motion/react";

/** Subtle, one-time card/section entrance — never decorative/looping. */
export function FadeIn({
  children,
  delay = 0,
  className,
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      initial={prefersReducedMotion ? undefined : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      // design_system.md §39: motion-slow (280ms), standard easing curve.
      transition={{ duration: 0.28, delay, ease: [0.2, 0, 0, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
