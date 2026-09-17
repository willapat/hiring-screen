"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAnalysis } from "@/lib/analysis-context";
import { ApiRequestError, startJobMatch } from "@/lib/api";

export function JobDescriptionInput() {
  const { state, dispatch } = useAnalysis();
  const [value, setValue] = useState(state.jobDescription);

  const submit = async () => {
    if (!state.resumeId || !value.trim()) return;
    dispatch({ type: "jobDescription/set", payload: value });
    dispatch({ type: "jobMatch/loading" });
    try {
      const result = await startJobMatch(state.resumeId, value);
      if (result.status === "rejected" || !result.job_analysis || !result.fit_score) {
        dispatch({
          type: "jobMatch/rejected",
          payload: result.message ?? "That doesn't look like a job description.",
        });
        return;
      }
      dispatch({
        type: "jobMatch/ok",
        payload: { sessionId: result.session_id, jobAnalysis: result.job_analysis, fitScore: result.fit_score },
      });
    } catch (err) {
      dispatch({
        type: "jobMatch/error",
        payload: err instanceof ApiRequestError ? err.message : "Failed to analyze the job description.",
      });
    }
  };

  return (
    <div className="space-y-3">
      <Textarea
        placeholder="Paste the full job description here..."
        rows={8}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={state.jobMatchLoading}
      />
      <Button onClick={() => void submit()} disabled={state.jobMatchLoading || !value.trim()}>
        {state.jobMatchLoading ? "Analyzing..." : "Score my fit"}
      </Button>
      {state.jobMatchError && <p className="text-sm text-destructive">{state.jobMatchError}</p>}
      {state.rejectionMessage && <p className="text-sm text-destructive">{state.rejectionMessage}</p>}
    </div>
  );
}
