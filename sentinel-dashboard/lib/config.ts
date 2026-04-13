const FALLBACK_WORKER_URL = "http://localhost:8585/api";

export function getWorkerApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_WORKER_URL ?? FALLBACK_WORKER_URL;
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
}
