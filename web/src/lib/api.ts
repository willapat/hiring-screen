import type {
  AdviceResponse,
  ApiError,
  AtsReport,
  FitScore,
  JobMatchResponse,
  LatexBuildResponse,
  ReviewReport,
  UploadResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiRequestError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiRequestError";
  }
}

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as ApiError;
    return body.detail ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new ApiRequestError(res.status, await parseErrorDetail(res));
  }
  return res.json() as Promise<T>;
}

export async function uploadResume(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/api/resume/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    throw new ApiRequestError(res.status, await parseErrorDetail(res));
  }
  return res.json() as Promise<UploadResponse>;
}

export async function scanAts(resumeId: string, requiredSkills?: string[]): Promise<AtsReport> {
  return postJson<AtsReport>("/api/ats/scan", {
    resume_id: resumeId,
    required_skills: requiredSkills ?? null,
    narrative: true,
  });
}

export async function reviewResume(resumeId: string): Promise<ReviewReport> {
  return postJson<ReviewReport>("/api/review", { resume_id: resumeId });
}

export async function startJobMatch(resumeId: string, jobDescription: string): Promise<JobMatchResponse> {
  return postJson<JobMatchResponse>("/api/job-match", {
    resume_id: resumeId,
    job_description: jobDescription,
  });
}

export async function buildLatex(resumeId: string): Promise<LatexBuildResponse> {
  return postJson<LatexBuildResponse>("/api/latex/build", { resume_id: resumeId });
}

export function latexDownloadUrl(buildId: string, kind: "tex" | "pdf"): string {
  return `${API_URL}/api/latex/${buildId}/resume.${kind}`;
}

export async function getAdvice(
  sessionId: string,
  options?: { fitScoreOverride?: FitScore; note?: string; tailor?: boolean },
): Promise<AdviceResponse> {
  return postJson<AdviceResponse>(`/api/job-match/${sessionId}/advice`, {
    fit_score_override: options?.fitScoreOverride ?? null,
    note: options?.note ?? null,
    tailor: options?.tailor ?? false,
  });
}
