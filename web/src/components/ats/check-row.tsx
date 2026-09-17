"use client";

import { useState } from "react";
import { ChevronDown, CircleCheck, CircleX, MinusCircle, TriangleAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AtsCheck } from "@/lib/types";

const STATUS_CONFIG = {
  pass: { icon: CircleCheck, className: "text-emerald-500" },
  warn: { icon: TriangleAlert, className: "text-amber-500" },
  fail: { icon: CircleX, className: "text-red-500" },
  skip: { icon: MinusCircle, className: "text-muted-foreground" },
} as const;

export function CheckRow({ check }: { check: AtsCheck }) {
  const [open, setOpen] = useState(check.status === "fail" || check.status === "warn");
  const { icon: Icon, className } = STATUS_CONFIG[check.status];

  return (
    <div className="border-b py-3 last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 text-left"
      >
        <Icon className={cn("size-4 shrink-0", className)} />
        <span className="flex-1 text-sm font-medium">{check.label}</span>
        <Badge variant="outline" className="text-xs text-muted-foreground">
          {check.weight} pts
        </Badge>
        <ChevronDown className={cn("size-4 shrink-0 text-muted-foreground transition-transform", open && "rotate-180")} />
      </button>
      {open && <p className="mt-2 pl-7 text-sm text-muted-foreground">{check.detail}</p>}
      {open && check.evidence.length > 0 && (
        <ul className="mt-2 space-y-1 pl-7">
          {check.evidence.map((e) => (
            <li key={e} className="font-mono text-xs text-muted-foreground">
              {e}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
