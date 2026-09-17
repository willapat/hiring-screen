export interface UploadResponse {
  resume_id: string;
  filename: string;
  page_count: number;
  char_count: number;
  canonical_text: string;
  warnings: string[];
}

export type CheckStage =
  | "extraction"
  | "reading_order"
  | "segmentation"
  | "field_extraction"
  | "skills"
  | "advisory";

export type CheckStatus = "pass" | "warn" | "fail" | "skip";

export interface AtsCheck {
  id: string;
  label: string;
  stage: CheckStage;
  status: CheckStatus;
  weight: number;
  detail: string;
  evidence: string[];
}

export interface KeywordCoverage {
  covered: string[];
  missing: string[];
  alias_only: string[];
  pct: number;
}

export interface AtsReport {
  score: number;
  grade: "A" | "B" | "C" | "D" | "F";
  reading_order_fidelity: number;
  checks: AtsCheck[];
  keyword_coverage: KeywordCoverage | null;
  narrative_markdown: string | null;
  llm_used: boolean;
}

export type IssueCategory =
  | "clarity"
  | "impact"
  | "formatting"
  | "grammar"
  | "quantification"
  | "tailoring"
  | "other";

export type IssueSeverity = "low" | "medium" | "high";

export interface Span {
  start: number;
  end: number;
}

export interface ReviewIssue {
  id: string;
  category: IssueCategory;
  severity: IssueSeverity;
  quote: string;
  line: number;
  problem: string;
  suggestion: string;
  span: Span | null;
}

export interface Segment {
  text: string;
  issue_ids: string[];
}

export interface ReviewReport {
  issues: ReviewIssue[];
  segments: Segment[];
  anchor_rate: number;
  summary_markdown: string | null;
}

export interface ApiError {
  detail: string;
}

export interface JobAnalysis {
  role_title: string;
  company_name: string;
  required_skills: string[];
  nice_to_have: string[];
  responsibilities: string[];
  company_summary: string;
}

export type FitVerdict = "strong" | "moderate" | "weak";

export interface SkillMatch {
  required: string;
  candidate_has: string;
  note: string;
}

export interface FitScore {
  verdict: FitVerdict;
  score: number;
  matched_skills: string[];
  partial_matches: SkillMatch[];
  missing_skills: string[];
  reasoning: string;
}

export interface JobMatchResponse {
  session_id: string;
  status: "awaiting_review" | "rejected";
  job_analysis: JobAnalysis | null;
  fit_score: FitScore | null;
  message: string | null;
}

export interface AdviceResponse {
  verdict: FitVerdict;
  advice_markdown: string;
  tailoring: ReviewReport | null;
}

export interface LatexBuildResponse {
  build_id: string;
  tex: string;
  pdf_available: boolean;
  compile_log_tail: string | null;
  ats_before: AtsReport;
  ats_after: AtsReport | null;
}
