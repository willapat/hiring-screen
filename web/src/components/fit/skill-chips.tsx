import { Badge } from "@/components/ui/badge";
import type { FitScore } from "@/lib/types";

export function SkillChips({ fitScore }: { fitScore: FitScore }) {
  return (
    <div className="space-y-3">
      <div>
        <p className="mb-1.5 text-xs font-medium text-muted-foreground">Matched</p>
        <div className="flex flex-wrap gap-1.5">
          {fitScore.matched_skills.length === 0 && <p className="text-sm text-muted-foreground">None</p>}
          {fitScore.matched_skills.map((s) => (
            <Badge key={s} className="bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/10 dark:text-emerald-400">
              {s}
            </Badge>
          ))}
        </div>
      </div>

      {fitScore.partial_matches.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-medium text-muted-foreground">Adjacent / transferable</p>
          <div className="flex flex-wrap gap-1.5">
            {fitScore.partial_matches.map((m) => (
              <Badge
                key={m.required}
                title={m.note}
                className="bg-amber-500/10 text-amber-600 hover:bg-amber-500/10 dark:text-amber-400"
              >
                {m.candidate_has} → {m.required}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div>
        <p className="mb-1.5 text-xs font-medium text-muted-foreground">Missing</p>
        <div className="flex flex-wrap gap-1.5">
          {fitScore.missing_skills.length === 0 && <p className="text-sm text-muted-foreground">None</p>}
          {fitScore.missing_skills.map((s) => (
            <Badge key={s} variant="outline" className="text-muted-foreground">
              {s}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}
