import { FileSearch, ScanSearch, Sparkles, Target } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { UploadCard } from "@/components/upload-card";

const FEATURES = [
  {
    icon: ScanSearch,
    title: "ATS Scan",
    description: "See exactly what an applicant-tracking parser sees in your PDF — fonts, reading order, formatting.",
  },
  {
    icon: FileSearch,
    title: "Resume Review",
    description: "Concrete, highlighted fixes for clarity, impact, and formatting — anchored to the exact text.",
  },
  {
    icon: Target,
    title: "Job Fit",
    description: "Score your resume against a job description and get a tailored gap-closing plan.",
  },
  {
    icon: Sparkles,
    title: "LaTeX Rewrite",
    description: "A clean, ATS-safe LaTeX resume rebuilt from your content and compiled to PDF.",
  },
];

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center gap-14 px-4 py-16 sm:py-24">
      <div className="space-y-5 text-center">
        <Badge variant="outline" className="mx-auto gap-1.5 border-primary/20 bg-primary/5 px-3 py-1 text-primary">
          <Sparkles className="size-3.5" />
          AI-powered resume tools
        </Badge>
        <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          Know exactly how your resume reads
        </h1>
        <p className="mx-auto max-w-xl text-balance text-muted-foreground">
          Upload a resume to scan it the way an ATS parser does, get a highlighted review, and see
          how it fits a specific job — all in one pass.
        </p>
      </div>

      <div className="w-full max-w-md">
        <UploadCard />
      </div>

      <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-2">
        {FEATURES.map(({ icon: Icon, title, description }) => (
          <div
            key={title}
            className="flex gap-3 rounded-xl border bg-card p-4 shadow-sm transition-colors hover:border-primary/30"
          >
            <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Icon className="size-4.5" />
            </span>
            <div className="space-y-1">
              <p className="text-sm font-medium">{title}</p>
              <p className="text-sm text-muted-foreground">{description}</p>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
