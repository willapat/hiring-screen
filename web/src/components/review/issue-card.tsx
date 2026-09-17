"use client";

import { forwardRef } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useAnalysis } from "@/lib/analysis-context";
import type { ReviewIssue } from "@/lib/types";
import { cn } from "@/lib/utils";

const SEVERITY_VARIANT: Record<ReviewIssue["severity"], string> = {
  high: "bg-red-500/10 text-red-600 dark:text-red-400",
  medium: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  low: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
};

export const IssueCard = forwardRef<HTMLDivElement, { issue: ReviewIssue }>(function IssueCard({ issue }, ref) {
  const { state, dispatch } = useAnalysis();
  const isActive = state.activeIssueId === issue.id;

  return (
    <Card
      ref={ref}
      className={cn("cursor-pointer transition-shadow", isActive && "ring-2 ring-primary")}
      onMouseEnter={() => dispatch({ type: "issue/hover", payload: issue.id })}
      onMouseLeave={() => dispatch({ type: "issue/hover", payload: null })}
    >
      <CardContent className="space-y-2">
        <div className="flex items-center gap-2">
          <Badge className={SEVERITY_VARIANT[issue.severity]}>{issue.severity}</Badge>
          <Badge variant="outline" className="text-muted-foreground">
            {issue.category}
          </Badge>
          {!issue.span && (
            <Badge variant="outline" className="text-muted-foreground">
              unanchored
            </Badge>
          )}
        </div>
        <p className="text-sm">{issue.problem}</p>
        <p className="text-sm text-muted-foreground">{issue.suggestion}</p>
      </CardContent>
    </Card>
  );
});
