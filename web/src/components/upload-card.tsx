"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, Loader2, Upload } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { ApiRequestError, uploadResume } from "@/lib/api";
import { useAnalysis } from "@/lib/analysis-context";

const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;

export function UploadCard() {
  const router = useRouter();
  const { dispatch } = useAnalysis();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleFile = useCallback(
    async (file: File) => {
      if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
        toast.error("Please upload a PDF file.");
        return;
      }
      if (file.size > MAX_UPLOAD_BYTES) {
        toast.error("That file is larger than 5MB.");
        return;
      }

      setIsUploading(true);
      try {
        const result = await uploadResume(file);
        dispatch({ type: "resume/set", payload: result });
        if (result.warnings.length > 0) {
          result.warnings.forEach((w) => toast.warning(w));
        }
        router.push("/analyze");
      } catch (err) {
        const message = err instanceof ApiRequestError ? err.message : "Upload failed — is the API running?";
        toast.error(message);
      } finally {
        setIsUploading(false);
      }
    },
    [dispatch, router],
  );

  return (
    <Card
      className={cn(
        "border-2 border-dashed shadow-sm transition-colors",
        isDragging ? "border-primary bg-primary/5" : "border-border bg-card/50",
      )}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files?.[0];
        if (file) void handleFile(file);
      }}
    >
      <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
        {isUploading ? (
          <Loader2 className="size-10 animate-spin text-muted-foreground" />
        ) : (
          <div className="flex size-14 items-center justify-center rounded-full bg-primary/10">
            <FileText className="size-7 text-primary" />
          </div>
        )}

        <div className="space-y-1">
          <p className="text-sm font-medium">
            {isUploading ? "Uploading and parsing your resume…" : "Drop your resume here"}
          </p>
          <p className="text-xs text-muted-foreground">PDF only, up to 5MB</p>
        </div>

        <Button
          variant="outline"
          size="sm"
          disabled={isUploading}
          onClick={() => inputRef.current?.click()}
        >
          <Upload data-icon="inline-start" />
          Choose a file
        </Button>

        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
            e.target.value = "";
          }}
        />
      </CardContent>
    </Card>
  );
}
