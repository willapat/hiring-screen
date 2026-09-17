"use client";

import { createContext, useContext, useReducer, type Dispatch, type ReactNode } from "react";
import type { AtsReport, FitScore, JobAnalysis, LatexBuildResponse, ReviewReport, UploadResponse } from "./types";

interface AnalysisState {
  resumeId: string | null;
  filename: string | null;
  canonicalText: string;
  ats: AtsReport | null;
  atsLoading: boolean;
  atsError: string | null;
  review: ReviewReport | null;
  reviewLoading: boolean;
  reviewError: string | null;
  activeIssueId: string | null;
  jobDescription: string;
  jobMatchLoading: boolean;
  jobMatchError: string | null;
  sessionId: string | null;
  jobAnalysis: JobAnalysis | null;
  fitScore: FitScore | null;
  rejectionMessage: string | null;
  adviceLoading: boolean;
  adviceError: string | null;
  adviceMarkdown: string | null;
  tailoring: ReviewReport | null;
  latex: LatexBuildResponse | null;
  latexLoading: boolean;
  latexError: string | null;
}

type AnalysisAction =
  | { type: "resume/set"; payload: UploadResponse }
  | { type: "resume/clear" }
  | { type: "ats/loading" }
  | { type: "ats/ok"; payload: AtsReport }
  | { type: "ats/error"; payload: string }
  | { type: "review/loading" }
  | { type: "review/ok"; payload: ReviewReport }
  | { type: "review/error"; payload: string }
  | { type: "issue/hover"; payload: string | null }
  | { type: "jobDescription/set"; payload: string }
  | { type: "jobMatch/loading" }
  | { type: "jobMatch/ok"; payload: { sessionId: string; jobAnalysis: JobAnalysis; fitScore: FitScore } }
  | { type: "jobMatch/rejected"; payload: string }
  | { type: "jobMatch/error"; payload: string }
  | { type: "advice/loading" }
  | { type: "advice/ok"; payload: { markdown: string; tailoring: ReviewReport | null } }
  | { type: "advice/error"; payload: string }
  | { type: "jobMatch/reset" }
  | { type: "latex/loading" }
  | { type: "latex/ok"; payload: LatexBuildResponse }
  | { type: "latex/error"; payload: string };

const initialState: AnalysisState = {
  resumeId: null,
  filename: null,
  canonicalText: "",
  ats: null,
  atsLoading: false,
  atsError: null,
  review: null,
  reviewLoading: false,
  reviewError: null,
  activeIssueId: null,
  jobDescription: "",
  jobMatchLoading: false,
  jobMatchError: null,
  sessionId: null,
  jobAnalysis: null,
  fitScore: null,
  rejectionMessage: null,
  adviceLoading: false,
  adviceError: null,
  adviceMarkdown: null,
  tailoring: null,
  latex: null,
  latexLoading: false,
  latexError: null,
};

function reducer(state: AnalysisState, action: AnalysisAction): AnalysisState {
  switch (action.type) {
    case "resume/set":
      return {
        ...initialState,
        resumeId: action.payload.resume_id,
        filename: action.payload.filename,
        canonicalText: action.payload.canonical_text,
      };
    case "resume/clear":
      return initialState;
    case "ats/loading":
      return { ...state, atsLoading: true, atsError: null };
    case "ats/ok":
      return { ...state, ats: action.payload, atsLoading: false };
    case "ats/error":
      return { ...state, atsLoading: false, atsError: action.payload };
    case "review/loading":
      return { ...state, reviewLoading: true, reviewError: null };
    case "review/ok":
      return { ...state, review: action.payload, reviewLoading: false };
    case "review/error":
      return { ...state, reviewLoading: false, reviewError: action.payload };
    case "issue/hover":
      return { ...state, activeIssueId: action.payload };
    case "jobDescription/set":
      return { ...state, jobDescription: action.payload };
    case "jobMatch/loading":
      return {
        ...state,
        jobMatchLoading: true,
        jobMatchError: null,
        rejectionMessage: null,
        adviceMarkdown: null,
        adviceError: null,
      };
    case "jobMatch/ok":
      return {
        ...state,
        jobMatchLoading: false,
        sessionId: action.payload.sessionId,
        jobAnalysis: action.payload.jobAnalysis,
        fitScore: action.payload.fitScore,
      };
    case "jobMatch/rejected":
      return { ...state, jobMatchLoading: false, rejectionMessage: action.payload };
    case "jobMatch/error":
      return { ...state, jobMatchLoading: false, jobMatchError: action.payload };
    case "advice/loading":
      return { ...state, adviceLoading: true, adviceError: null };
    case "advice/ok":
      return {
        ...state,
        adviceLoading: false,
        adviceMarkdown: action.payload.markdown,
        tailoring: action.payload.tailoring,
      };
    case "advice/error":
      return { ...state, adviceLoading: false, adviceError: action.payload };
    case "jobMatch/reset":
      return {
        ...state,
        jobDescription: "",
        jobMatchLoading: false,
        jobMatchError: null,
        sessionId: null,
        jobAnalysis: null,
        fitScore: null,
        rejectionMessage: null,
        adviceLoading: false,
        adviceError: null,
        adviceMarkdown: null,
        tailoring: null,
      };
    case "latex/loading":
      return { ...state, latexLoading: true, latexError: null };
    case "latex/ok":
      return { ...state, latexLoading: false, latex: action.payload };
    case "latex/error":
      return { ...state, latexLoading: false, latexError: action.payload };
    default:
      return state;
  }
}

interface AnalysisContextValue {
  state: AnalysisState;
  dispatch: Dispatch<AnalysisAction>;
}

const AnalysisContext = createContext<AnalysisContextValue | null>(null);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return <AnalysisContext.Provider value={{ state, dispatch }}>{children}</AnalysisContext.Provider>;
}

export function useAnalysis(): AnalysisContextValue {
  const ctx = useContext(AnalysisContext);
  if (!ctx) {
    throw new Error("useAnalysis must be used within an AnalysisProvider");
  }
  return ctx;
}
