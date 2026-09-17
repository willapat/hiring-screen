"use client";

import { useEffect } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Markdown } from "@/components/markdown";
import { ApiRequestError, scanAts } from "@/lib/api";
import { useAnalysis } from "@/lib/analysis-context";
import { ScoreDial } from "./score-dial";
import { CheckRow } from "./check-row";
import { KeywordCoveragePanel } from "./keyword-coverage";

export function AtsPanel() {
  const { state, dispatch } = useAnalysis();
  const { resumeId, ats, atsLoading, atsError } = state;

  useEffect(() => {
    if (!resumeId || ats || atsLoading) return;
    dispatch({ type: "ats/loading" });
    scanAts(resumeId)
      .then((report) => dispatch({ type: "ats/ok", payload: report }))
      .catch((err) =>
        dispatch({
          type: "ats/error",
          payload: err instanceof ApiRequestError ? err.message : "Failed to run the ATS scan.",
        }),
      );
  }, [resumeId, ats, atsLoading, dispatch]);

  if (atsError) {
    return <p className="text-sm text-destructive">{atsError}</p>;
  }

  if (!ats || atsLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="size-32 shrink-0 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        </div>
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  const sortedChecks = [...ats.checks].sort((a, b) => b.weight - a.weight);

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
        <ScoreDial score={ats.score} grade={ats.grade} />
        <div className="flex-1 space-y-2 text-center sm:text-left">
          <p className="text-sm text-muted-foreground">
            Reading order fidelity: {(ats.reading_order_fidelity * 100).toFixed(0)}%
          </p>
          {ats.narrative_markdown ? (
            <Markdown>{ats.narrative_markdown}</Markdown>
          ) : (
            <p className="text-sm text-muted-foreground">
              Narrative summary unavailable {"—"} the checks below are still fully computed.
            </p>
          )}
        </div>
      </div>

      {ats.keyword_coverage && <KeywordCoveragePanel coverage={ats.keyword_coverage} />}

      <div>
        <p className="mb-2 text-sm font-medium">All checks</p>
        <div className="rounded-lg border px-4">
          {sortedChecks.map((check) => (
            <CheckRow key={check.id} check={check} />
          ))}
        </div>
      </div>
    </div>
  );
}
