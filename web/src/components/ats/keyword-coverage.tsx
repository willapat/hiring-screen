import { Badge } from "@/components/ui/badge";
import type { KeywordCoverage } from "@/lib/types";

export function KeywordCoveragePanel({ coverage }: { coverage: KeywordCoverage }) {
  return (
    <div className="space-y-3 rounded-lg border p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">Keyword coverage vs. job description</p>
        <p className="text-sm text-muted-foreground">{coverage.pct}%</p>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {coverage.covered.map((s) => (
          <Badge key={s} className="bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/10 dark:text-emerald-400">
            {s}
          </Badge>
        ))}
        {coverage.alias_only.map((s) => (
          <Badge key={s} className="bg-amber-500/10 text-amber-600 hover:bg-amber-500/10 dark:text-amber-400">
            {s} (alias)
          </Badge>
        ))}
        {coverage.missing.map((s) => (
          <Badge key={s} variant="outline" className="text-muted-foreground line-through">
            {s}
          </Badge>
        ))}
      </div>
    </div>
  );
}
