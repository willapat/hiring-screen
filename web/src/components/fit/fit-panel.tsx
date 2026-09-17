"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { JobDescriptionInput } from "@/components/job-description-input";
import { useAnalysis } from "@/lib/analysis-context";
import { AdviceView } from "./advice-view";
import { ScoreEditor } from "./score-editor";
import { SkillChips } from "./skill-chips";

export function FitPanel() {
  const { state, dispatch } = useAnalysis();

  if (state.jobMatchLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-6 w-1/3" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (!state.sessionId || !state.jobAnalysis || !state.fitScore) {
    return <JobDescriptionInput />;
  }

  const { jobAnalysis, fitScore } = state;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-lg font-semibold">{jobAnalysis.role_title}</p>
          <p className="text-sm text-muted-foreground">{jobAnalysis.company_name}</p>
        </div>
        <Button variant="ghost" size="sm" onClick={() => dispatch({ type: "jobMatch/reset" })}>
          Start over
        </Button>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-3xl font-semibold tabular-nums">{fitScore.score}</span>
        <Badge className="capitalize">{fitScore.verdict}</Badge>
      </div>
      <p className="text-sm text-muted-foreground">{fitScore.reasoning}</p>

      <SkillChips fitScore={fitScore} />

      {state.adviceMarkdown ? <AdviceView /> : <ScoreEditor />}
    </div>
  );
}
