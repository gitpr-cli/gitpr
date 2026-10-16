/**
 * Defense-in-depth secret masking for notifications and OutputChannel logs.
 * Mirrors the server-side patterns in src/infrastructure/ci/masking.py.
 */

const SECRET_PATTERNS: Array<[RegExp, string]> = [
  [
    /-----BEGIN (?:[A-Z0-9_-]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z0-9_-]+ )?PRIVATE KEY-----/g,
    "-----BEGIN PRIVATE KEY-----\n***\n-----END PRIVATE KEY-----",
  ],
  [/\bAKIA[0-9A-Z]{16}\b/g, "***"],
  [/\bgh[pousr]_[A-Za-z0-9_]{36,255}\b/g, "***"],
  [/\bgithub_pat_[A-Za-z0-9_]{82}\b/g, "***"],
  [/\bglpat-[A-Za-z0-9_-]{20,}\b/g, "***"],
  [/\bAIza[0-9A-Za-z\-_]{30,45}\b/g, "***"],
  [/\bsk-[A-Za-z0-9_-]{20,}\b/g, "***"],
  [/\bxox[baprs]-[0-9A-Za-z]{10,48}\b/g, "***"],
  [/\bBearer\s+[A-Za-z0-9\-_.]{20,}\b/gi, "Bearer ***"],
  [/(https?:\/\/[^:/@\s]+):([^/@\s]+)@/g, "$1:***@"],
];

export function maskSensitiveText(text: string | undefined | null): string {
  if (!text) {
    return "";
  }
  let masked = String(text);
  for (const [pattern, replacement] of SECRET_PATTERNS) {
    masked = masked.replace(pattern, replacement);
  }
  return masked;
}
