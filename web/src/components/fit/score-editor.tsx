"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ApiRequestError, getAdvice } from "@/lib/api";
import { useAnalysis } from "@/lib/analysis-context";
import type { FitVerdict } from "@/lib/types";

const VERDICTS: FitVerdict[] = ["strong", "moderate", "weak"];

export function ScoreEditor() {
  const { state, dispatch } = useAnalysis();
  const fitScore = state.fitScore;
  const [score, setScore] = useState(fitScore?.score ?? 0);
  const [verdict, setVerdict] = useState<FitVerdict>(fitScore?.verdict ?? "moderate");
  const [note, setNote] = useState("");
  const [tailor, setTailor] = useState(false);

  if (!fitScore) return null;

  const submit = async () => {
    if (!state.sessionId) return;
    dispatch({ type: "advice/loading" });
    try {
      const changed = score !== fitScore.score || verdict !== fitScore.verdict;
      const result = await getAdvice(state.sessionId, {
        fitScoreOverride: changed ? { ...fitScore, score, verdict } : undefined,
        note: note.trim() || undefined,
        tailor,
      });
      dispatch({
        type: "advice/ok",
        payload: { markdown: result.advice_markdown, tailoring: result.tailoring },
      });
    } catch (err) {
      dispatch({
        type: "advice/error",
        payload: err instanceof ApiRequestError ? err.message : "Failed to get advice.",
      });
    }
  };

  return (
    <div className="space-y-3 rounded-lg border p-4">
      <p className="text-sm font-medium">If anything above looks wrong, correct it before getting advice</p>
      <div className="flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-sm">
          Score
          <Input
            type="number"
            min={0}
            max={100}
            value={score}
            onChange={(e) => setScore(Number(e.target.value))}
            className="w-20"
          />
        </label>
        <label className="flex items-center gap-2 text-sm">
          Verdict
          <select
            value={verdict}
            onChange={(e) => setVerdict(e.target.value as FitVerdict)}
            className="h-8 rounded-lg border bg-background px-2 text-sm capitalize"
          >
            {VERDICTS.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </label>
      </div>
      <Textarea
        placeholder="Optional: correct anything the scorer got wrong..."
        rows={2}
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <input
          type="checkbox"
          checked={tailor}
          onChange={(e) => setTailor(e.target.checked)}
          className="size-4 rounded border"
        />
        Also suggest tailored rewrites for this job
      </label>
      <Button onClick={() => void submit()} disabled={state.adviceLoading}>
        {state.adviceLoading ? "Getting advice..." : "Get tailored advice"}
      </Button>
      {state.adviceError && <p className="text-sm text-destructive">{state.adviceError}</p>}
    </div>
  );
}
