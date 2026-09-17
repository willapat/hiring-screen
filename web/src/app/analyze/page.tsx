"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { FileText } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AtsPanel } from "@/components/ats/ats-panel";
import { ReviewPanel } from "@/components/review/review-panel";
import { FitPanel } from "@/components/fit/fit-panel";
import { ExportPanel } from "@/components/export/export-panel";
import { useAnalysis } from "@/lib/analysis-context";

export default function AnalyzePage() {
  const router = useRouter();
  const { state } = useAnalysis();
  const { resumeId, filename, canonicalText } = state;

  useEffect(() => {
    if (!resumeId) router.replace("/");
  }, [resumeId, router]);

  if (!resumeId) return null;

  const wordCount = canonicalText.trim() ? canonicalText.trim().split(/\s+/).length : 0;

  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
      <div className="mb-6 flex items-center gap-3 rounded-xl border bg-card p-4 shadow-sm">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <FileText className="size-5" />
        </span>
        <div>
          <h1 className="font-semibold">{filename}</h1>
          <p className="text-sm text-muted-foreground">{wordCount} words extracted</p>
        </div>
      </div>

      <Tabs defaultValue="ats">
        <TabsList>
          <TabsTrigger value="ats">ATS Scan</TabsTrigger>
          <TabsTrigger value="review">Resume Review</TabsTrigger>
          <TabsTrigger value="fit">Job Fit</TabsTrigger>
          <TabsTrigger value="export">Export</TabsTrigger>
        </TabsList>
        <TabsContent value="ats" className="pt-6">
          <AtsPanel />
        </TabsContent>
        <TabsContent value="review" className="pt-6">
          <ReviewPanel />
        </TabsContent>
        <TabsContent value="fit" className="pt-6">
          <FitPanel />
        </TabsContent>
        <TabsContent value="export" className="pt-6">
          <ExportPanel />
        </TabsContent>
      </Tabs>
    </main>
  );
}
