"use client";

import { AlertTriangle, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { isRecommendationFresh, useAiRecommendation, useGenerateRecommendation } from "@/features/ai/hooks/use-ai";
import { ApiError } from "@/lib/api/errors";
import { formatRelativeTime } from "@/utils/format";

function StepList({
  title,
  steps,
  ordered,
}: {
  title: string;
  steps: string[];
  ordered: boolean;
}) {
  if (steps.length === 0) return null;
  const ListTag = ordered ? "ol" : "ul";
  return (
    <section>
      <h3 className="text-title text-foreground">{title}</h3>
      <ListTag
        className={
          ordered
            ? "mt-2 flex list-inside list-decimal flex-col gap-2"
            : "mt-2 flex flex-col gap-2"
        }
      >
        {steps.map((step, index) => (
          <li key={index} className="text-sm break-words whitespace-pre-line text-foreground">
            {step}
          </li>
        ))}
      </ListTag>
    </section>
  );
}

/**
 * Renders the actual RecommendationOutput contract (summary, explanation,
 * remediation_steps, validation_steps, cautions) — every field is
 * untrusted AI-generated text, rendered through plain JSX text
 * interpolation only. No dangerouslySetInnerHTML, no Markdown execution,
 * no URL auto-activation, no "Run"/"Execute"/"Apply Fix" actions: AVAP's
 * AI is advisory only.
 */
export function RecommendationPanel({
  assessmentId,
  riskCalculatedAt,
}: {
  assessmentId: string;
  /** The owning RiskAssessment's calculated_at, passed down by the Risk
   * feature (never fetched here) so freshness uses the exact backend rule. */
  riskCalculatedAt: string;
}) {
  const { data: recommendation, isPending, isError, error, refetch } =
    useAiRecommendation(assessmentId);
  const { mutate, isPending: isGenerating } = useGenerateRecommendation();

  function handleGenerate() {
    if (isGenerating) return;
    mutate(assessmentId, {
      onError: (err) => toast.error(err.message),
    });
  }

  if (isPending) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  // A missing recommendation (404 NOT_FOUND) is a valid product state —
  // checked via the normalized error's structured `code`, never by
  // matching error text.
  const isMissing = isError && error instanceof ApiError && error.code === "NOT_FOUND";

  if (isMissing) {
    return (
      <EmptyState
        icon={Sparkles}
        title="No remediation guidance yet"
        description="AI-assisted remediation guidance generated from the current vulnerability and deterministic risk context. Advisory only — not a guaranteed fix."
        action={
          <Button size="sm" onClick={handleGenerate} disabled={isGenerating}>
            {isGenerating ? "Generating remediation guidance…" : "Generate Remediation"}
          </Button>
        }
      />
    );
  }

  if (isError || !recommendation) {
    return (
      <ErrorState
        title="Unable to load remediation guidance"
        description="The AI recommendation could not be retrieved."
        onRetry={() => refetch()}
      />
    );
  }

  const isFresh = isRecommendationFresh(recommendation.generated_at, riskCalculatedAt);

  return (
    <div className="flex flex-col gap-5">
      {!isFresh && (
        <div
          role="status"
          className="flex items-start gap-2 rounded-md border border-warning/30 bg-warning-bg px-3 py-2 text-sm text-warning"
        >
          <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>
            Risk has been recalculated since this guidance was generated. Generate
            again for guidance based on the current assessment.
          </span>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          Generated {formatRelativeTime(recommendation.generated_at)} ·{" "}
          {recommendation.provider} / {recommendation.model}
        </p>
        <Button variant="outline" size="sm" onClick={handleGenerate} disabled={isGenerating}>
          {isGenerating ? "Generating…" : isFresh ? "Regenerate" : "Generate Remediation"}
        </Button>
      </div>

      <section>
        <h3 className="text-title text-foreground">Summary</h3>
        <p className="mt-1 text-sm break-words whitespace-pre-line text-foreground">
          {recommendation.summary}
        </p>
      </section>

      <section>
        <h3 className="text-title text-foreground">Why This Matters</h3>
        <p className="mt-1 text-sm break-words whitespace-pre-line text-foreground">
          {recommendation.explanation}
        </p>
      </section>

      <StepList title="Remediation Steps" steps={recommendation.remediation_steps} ordered />
      <StepList title="Validation Steps" steps={recommendation.validation_steps} ordered />

      {recommendation.cautions.length > 0 && (
        <section>
          <h3 className="text-title text-foreground">Cautions</h3>
          <ul className="mt-2 flex flex-col gap-2">
            {recommendation.cautions.map((caution, index) => (
              <li
                key={index}
                className="flex items-start gap-2 rounded-md border border-warning/30 bg-warning-bg px-3 py-2 text-sm text-warning"
              >
                <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
                <span className="break-words whitespace-pre-line">{caution}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="text-xs text-muted-foreground">
        Advisory guidance only. AVAP does not execute remediation automatically.
      </p>
    </div>
  );
}
