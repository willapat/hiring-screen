"use client";

import { useEffect, useRef } from "react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiRequestError, reviewResume } from "@/lib/api";
import { useAnalysis } from "@/lib/analysis-context";
import { HighlightedResume } from "./highlighted-resume";
import { IssueCard } from "./issue-card";

export function ReviewPanel() {
  const { state, dispatch } = useAnalysis();
  const { resumeId, review, reviewLoading, reviewError } = state;
  const cardRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    if (!resumeId || review || reviewLoading) return;
    dispatch({ type: "review/loading" });
    reviewResume(resumeId)
      .then((report) => dispatch({ type: "review/ok", payload: report }))
      .catch((err) =>
        dispatch({
          type: "review/error",
          payload: err instanceof ApiRequestError ? err.message : "Failed to run the resume review.",
        }),
      );
  }, [resumeId, review, reviewLoading, dispatch]);

  if (reviewError) {
    return <p className="text-sm text-destructive">{reviewError}</p>;
  }

  if (!review || reviewLoading) {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <Skeleton className="h-[600px] w-full" />
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      </div>
    );
  }

  const scrollToIssue = (issueId: string) => {
    dispatch({ type: "issue/hover", payload: issueId });
    cardRefs.current[issueId]?.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">What the ATS sees</p>
        <Badge variant="outline" className="text-muted-foreground">
          {Math.round(review.anchor_rate * 100)}% of issues located in text
        </Badge>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <HighlightedResume segments={review.segments} issues={review.issues} onIssueClick={scrollToIssue} />
        <div className="max-h-[600px] space-y-3 overflow-y-auto">
          {review.issues.map((issue) => (
            <IssueCard key={issue.id} issue={issue} ref={(el) => { cardRefs.current[issue.id] = el; }} />
          ))}
        </div>
      </div>
    </div>
  );
}
