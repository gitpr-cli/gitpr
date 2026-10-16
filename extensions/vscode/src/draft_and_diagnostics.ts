import { maskSensitiveText } from "./masking";

export interface CheckFindingPayload {
  fingerprint?: string;
  rule_id: string;
  category?: string;
  file_path: string;
  line_start: number;
  line_end?: number;
  severity: "error" | "warning" | "info";
  source?: string;
  message: string;
  suggestion?: string | null;
  baseline_status?: string | null;
}

export interface CheckEnvelopeResponse {
  status?: "success" | "failure" | "error";
  exit_code?: number;
  incomplete?: boolean;
  message?: string;
  findings?: CheckFindingPayload[];
}

export interface ParsedPrDraft {
  title: string;
  body: string;
}

export function formatPrDraftDocument(title: string, body: string): string {
  const cleanTitle = (title || "feat: update branch").trim();
  const cleanBody = (body || "").trim();
  return `${cleanTitle}\n\n${cleanBody}\n`;
}

export function parsePrDraftDocument(rawContent: string): ParsedPrDraft {
  const lines = rawContent.split(/\r?\n/);
  let titleLineIndex = -1;
  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (trimmed.length > 0) {
      titleLineIndex = i;
      break;
    }
  }
  if (titleLineIndex === -1) {
    return { title: "", body: "" };
  }
  const rawTitle = lines[titleLineIndex].replace(/^#+\s*/, "").trim();
  const body = lines
    .slice(titleLineIndex + 1)
    .join("\n")
    .trim();
  return { title: rawTitle, body };
}

export interface NormalizedDiagnosticItem {
  filePath: string;
  startLineZeroBased: number;
  endLineZeroBased: number;
  severity: "error" | "warning" | "info";
  message: string;
  source: string;
  code: string;
}

export function normalizeCheckFindings(
  findings: CheckFindingPayload[]
): NormalizedDiagnosticItem[] {
  const items: NormalizedDiagnosticItem[] = [];
  for (const f of findings) {
    if (
      f.baseline_status === "ignored" ||
      f.baseline_status === "resolved"
    ) {
      continue;
    }
    const startLine = Math.max(0, (f.line_start || 1) - 1);
    const endLine = Math.max(startLine, (f.line_end || f.line_start || 1) - 1);
    const msgParts = [maskSensitiveText(f.message)];
    if (f.suggestion) {
      msgParts.push(`Suggestion: ${maskSensitiveText(f.suggestion)}`);
    }
    const sev = (f.severity || "info").toLowerCase();
    const normSev: "error" | "warning" | "info" =
      sev === "error" || sev === "warning" ? sev : "info";

    items.push({
      filePath: f.file_path,
      startLineZeroBased: startLine,
      endLineZeroBased: endLine,
      severity: normSev,
      message: msgParts.join(" — "),
      source: `gitpr (${f.source ?? "check"})`,
      code: f.rule_id,
    });
  }
  return items;
}
