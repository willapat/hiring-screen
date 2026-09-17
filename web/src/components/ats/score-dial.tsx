import { cn } from "@/lib/utils";

const GRADE_COLORS: Record<string, string> = {
  A: "text-emerald-500",
  B: "text-emerald-500",
  C: "text-amber-500",
  D: "text-orange-500",
  F: "text-red-500",
};

export function ScoreDial({ score, grade }: { score: number; grade: string }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);
  const colorClass = GRADE_COLORS[grade] ?? "text-muted-foreground";

  return (
    <div className="relative flex size-32 shrink-0 items-center justify-center">
      <svg viewBox="0 0 120 120" className="size-32 -rotate-90">
        <circle cx="60" cy="60" r={radius} strokeWidth="10" className="fill-none stroke-muted" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          strokeWidth="10"
          strokeLinecap="round"
          stroke="currentColor"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={cn("fill-none transition-[stroke-dashoffset] duration-700 ease-out", colorClass)}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-3xl font-semibold tabular-nums">{score}</span>
        <span className={cn("text-sm font-medium", colorClass)}>{grade}</span>
      </div>
    </div>
  );
}
