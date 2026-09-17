import { Badge } from "@/components/ui/badge";
import { Markdown } from "@/components/markdown";
import { HighlightedResume } from "@/components/review/highlighted-resume";
import { IssueCard } from "@/components/review/issue-card";
import { useAnalysis } from "@/lib/analysis-context";

export function AdviceView() {
  const { state } = useAnalysis();
  if (!state.adviceMarkdown) return null;

  return (
    <div className="space-y-4">
      <div className="rounded-lg border p-4">
        <Markdown>{state.adviceMarkdown}</Markdown>
      </div>

      {state.tailoring && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Tailored rewrite suggestions</p>
            <Badge variant="outline" className="text-muted-foreground">
              {Math.round(state.tailoring.anchor_rate * 100)}% located in text
            </Badge>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <HighlightedResume segments={state.tailoring.segments} issues={state.tailoring.issues} />
            <div className="max-h-[600px] space-y-3 overflow-y-auto">
              {state.tailoring.issues.map((issue) => (
                <IssueCard key={issue.id} issue={issue} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
