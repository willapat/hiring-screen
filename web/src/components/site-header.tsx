"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ScanSearch, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAnalysis } from "@/lib/analysis-context";

export function SiteHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { dispatch } = useAnalysis();

  return (
    <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur-md supports-backdrop-filter:bg-background/60">
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ScanSearch className="size-4" />
          </span>
          Hiring Screen
        </Link>

        {pathname === "/analyze" && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              dispatch({ type: "resume/clear" });
              router.push("/");
            }}
          >
            <Upload data-icon="inline-start" />
            New resume
          </Button>
        )}
      </div>
    </header>
  );
}
