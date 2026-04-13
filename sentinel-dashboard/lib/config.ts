const FALLBACK_WORKER_URL = "https://api.mamaoliechrestaurant.tech/api";

export function getWorkerApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_WORKER_URL ?? FALLBACK_WORKER_URL;
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
}
