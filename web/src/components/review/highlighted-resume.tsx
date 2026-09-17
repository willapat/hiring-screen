"use client";

import type { ReviewIssue, Segment } from "@/lib/types";
import { useAnalysis } from "@/lib/analysis-context";
import { cn } from "@/lib/utils";

const SEVERITY_RANK: Record<ReviewIssue["severity"], number> = { high: 3, medium: 2, low: 1 };

const SEVERITY_CLASS: Record<ReviewIssue["severity"], string> = {
  high: "bg-red-500/25 decoration-red-500 dark:bg-red-500/30",
  medium: "bg-amber-500/25 decoration-amber-500 dark:bg-amber-500/30",
  low: "bg-blue-500/25 decoration-blue-500 dark:bg-blue-500/30",
};

function severityFor(issueIds: string[], issuesById: Map<string, ReviewIssue>): ReviewIssue["severity"] | null {
  let best: ReviewIssue["severity"] | null = null;
  for (const id of issueIds) {
    const severity = issuesById.get(id)?.severity;
    if (severity && (!best || SEVERITY_RANK[severity] > SEVERITY_RANK[best])) {
      best = severity;
    }
  }
  return best;
}

interface HighlightedResumeProps {
  segments: Segment[];
  issues: ReviewIssue[];
  onIssueClick?: (issueId: string) => void;
}

export function HighlightedResume({ segments, issues, onIssueClick }: HighlightedResumeProps) {
  const { state, dispatch } = useAnalysis();
  const issuesById = new Map(issues.map((i) => [i.id, i]));

  return (
    <pre className="max-h-[600px] overflow-y-auto whitespace-pre-wrap rounded-lg border p-4 font-sans text-sm leading-relaxed">
      {segments.map((segment, i) => {
        if (segment.issue_ids.length === 0) {
          return <span key={i}>{segment.text}</span>;
        }
        const severity = severityFor(segment.issue_ids, issuesById);
        const isActive = segment.issue_ids.includes(state.activeIssueId ?? "");
        return (
          <mark
            key={i}
            className={cn(
              "cursor-pointer rounded-sm bg-transparent text-inherit underline decoration-2 underline-offset-2 transition-shadow",
              severity && SEVERITY_CLASS[severity],
              isActive && "ring-2 ring-primary",
            )}
            onMouseEnter={() => dispatch({ type: "issue/hover", payload: segment.issue_ids[0] })}
            onMouseLeave={() => dispatch({ type: "issue/hover", payload: null })}
            onClick={() => onIssueClick?.(segment.issue_ids[0])}
          >
            {segment.text}
          </mark>
        );
      })}
    </pre>
  );
}
