"use client";

import { useEffect } from "react";
import { ArrowRight, Download } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiRequestError, buildLatex, latexDownloadUrl } from "@/lib/api";
import { useAnalysis } from "@/lib/analysis-context";
import type { AtsReport, CheckStatus } from "@/lib/types";

const STATUS_RANK: Record<CheckStatus, number> = { fail: 0, warn: 1, skip: 1.5, pass: 2 };
const STATUS_LABEL: Record<CheckStatus, string> = { fail: "Fail", warn: "Warn", skip: "Skipped", pass: "Pass" };

interface CheckDelta {
  id: string;
  label: string;
  before: CheckStatus;
  after: CheckStatus;
  improved: boolean;
}

function computeCheckDeltas(before: AtsReport, after: AtsReport): CheckDelta[] {
  const afterById = new Map(after.checks.map((c) => [c.id, c]));
  const deltas: CheckDelta[] = [];
  for (const b of before.checks) {
    const a = afterById.get(b.id);
    if (!a || a.status === b.status) continue;
    deltas.push({
      id: b.id,
      label: b.label,
      before: b.status,
      after: a.status,
      improved: STATUS_RANK[a.status] > STATUS_RANK[b.status],
    });
  }
  return deltas;
}

export function ExportPanel() {
  const { state, dispatch } = useAnalysis();
  const { resumeId, latex, latexLoading, latexError } = state;

  useEffect(() => {
    if (!resumeId || latex || latexLoading) return;
    dispatch({ type: "latex/loading" });
    buildLatex(resumeId)
      .then((result) => dispatch({ type: "latex/ok", payload: result }))
      .catch((err) =>
        dispatch({
          type: "latex/error",
          payload: err instanceof ApiRequestError ? err.message : "Failed to build the LaTeX resume.",
        }),
      );
  }, [resumeId, latex, latexLoading, dispatch]);

  if (latexError) {
    return <p className="text-sm text-destructive">{latexError}</p>;
  }

  if (!latex || latexLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-[500px] w-full" />
      </div>
    );
  }

  const improved = latex.ats_after !== null && latex.ats_after.score >= latex.ats_before.score;
  const deltas = latex.ats_after ? computeCheckDeltas(latex.ats_before, latex.ats_after) : [];

  return (
    <div className="space-y-6">
      <div className="space-y-4 rounded-lg border p-6">
        <div>
          <p className="text-sm font-medium">ATS score, before vs. after</p>
          <p className="text-xs text-muted-foreground">
            The same 16-check rubric as the ATS Scan tab, run once on your original PDF and once on
            the LaTeX rewrite below. &ldquo;Before&rdquo; is how your uploaded resume scores today;
            &ldquo;after&rdquo; is how the regenerated version scores.
          </p>
        </div>
        <div className="flex items-center justify-center gap-6">
          <div className="text-center">
            <p className="text-xs text-muted-foreground">Before</p>
            <p className="text-3xl font-semibold tabular-nums">{latex.ats_before.score}</p>
          </div>
          <ArrowRight className="size-6 text-muted-foreground" />
          <div className="text-center">
            <p className="text-xs text-muted-foreground">After</p>
            <p className={`text-3xl font-semibold tabular-nums ${latex.ats_after !== null && improved ? "text-emerald-500" : ""}`}>
              {latex.ats_after?.score ?? "—"}
            </p>
          </div>
        </div>
      </div>

      {latex.ats_after &&
        (deltas.length > 0 ? (
          <div className="space-y-2">
            <p className="text-sm font-medium">What changed</p>
            <div className="divide-y rounded-lg border">
              {deltas.map((d) => (
                <div key={d.id} className="flex items-center justify-between gap-3 p-3">
                  <span className="text-sm">{d.label}</span>
                  <span className="flex shrink-0 items-center gap-1.5">
                    <Badge variant="outline" className="text-muted-foreground">
                      {STATUS_LABEL[d.before]}
                    </Badge>
                    <ArrowRight className="size-3 text-muted-foreground" />
                    <Badge
                      className={
                        d.improved
                          ? "bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/10 dark:text-emerald-400"
                          : "bg-red-500/10 text-red-600 hover:bg-red-500/10 dark:text-red-400"
                      }
                    >
                      {STATUS_LABEL[d.after]}
                    </Badge>
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-center text-sm text-muted-foreground">
            No individual checks changed status — the rewrite held the same ground it started
            from.
          </p>
        ))}

      {!latex.pdf_available && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 text-sm text-muted-foreground">
          PDF compilation isn&apos;t available on this server right now — the LaTeX source below
          is still ready to download and compile yourself (e.g. on Overleaf).
          {latex.compile_log_tail && (
            <pre className="mt-2 max-h-32 overflow-y-auto whitespace-pre-wrap font-mono text-xs">
              {latex.compile_log_tail}
            </pre>
          )}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          nativeButton={false}
          render={<a href={latexDownloadUrl(latex.build_id, "tex")} download="resume.tex" />}
        >
          <Download data-icon="inline-start" />
          Download .tex
        </Button>
        {latex.pdf_available && (
          <Button
            size="sm"
            nativeButton={false}
            render={<a href={latexDownloadUrl(latex.build_id, "pdf")} download="resume.pdf" />}
          >
            <Download data-icon="inline-start" />
            Download .pdf
          </Button>
        )}
      </div>

      {latex.pdf_available ? (
        <iframe
          src={latexDownloadUrl(latex.build_id, "pdf")}
          className="h-[600px] w-full rounded-lg border"
          title="Compiled resume PDF"
        />
      ) : (
        <pre className="max-h-[600px] overflow-y-auto whitespace-pre-wrap rounded-lg border p-4 font-mono text-xs">
          {latex.tex}
        </pre>
      )}
    </div>
  );
}
