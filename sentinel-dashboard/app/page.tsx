"use client";

import { useEffect, useMemo, useState } from "react";

import { ActivityLog } from "@/components/activity-log";
import { StatusPulse } from "@/components/status-pulse";
import { getWorkerApiBaseUrl } from "@/lib/config";
import { WorkerStatus } from "@/lib/types";

const API_BASE = getWorkerApiBaseUrl();

const initialStatus: WorkerStatus = {
  status: "offline",
  next_post_at: null,
  last_post_at: null,
  posts_today: 0,
  history_size: 0,
  trend_confidence_today_avg: 0,
  trend_priority_posts_today: 0,
  recent_logs: [],
};

export default function Home() {
  const [status, setStatus] = useState<WorkerStatus>(initialStatus);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(`${API_BASE}/status`, { cache: "no-store" });
        const data = await response.json();
        setStatus(data);
      } catch {
        setStatus((prev) => ({ ...prev, status: "offline" }));
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 8000);
    return () => clearInterval(interval);
  }, []);

  const countdown = useMemo(() => {
    if (!status.next_post_at) return "--:--:--";
    const distance = new Date(status.next_post_at).getTime() - now;
    if (distance <= 0) return "imminent";
    const hours = Math.floor(distance / 3_600_000);
    const minutes = Math.floor((distance % 3_600_000) / 60_000);
    const seconds = Math.floor((distance % 60_000) / 1000);
    return [hours, minutes, seconds].map((v) => String(v).padStart(2, "0")).join(":");
  }, [status.next_post_at, now]);

  const nextPostEAT = useMemo(() => {
    if (!status.next_post_at) return "Not scheduled";
    return new Date(status.next_post_at).toLocaleString("en-KE", {
      timeZone: "Africa/Nairobi",
      hour12: false,
    });
  }, [status.next_post_at]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-[#0a0c0f] via-bg to-[#0f1217] p-6 md:p-10">
      <section className="mx-auto mb-6 max-w-7xl">
        <div className="rounded-2xl border border-warning/30 bg-panel p-4 shadow-glow">
          <img src="/sentinel-logo.svg" alt="SquareAutomation" className="h-auto w-full rounded-xl" />
        </div>
      </section>
      <section className="mx-auto grid max-w-7xl gap-6 md:grid-cols-3">
        <article className="rounded-2xl border border-warning/20 bg-panel p-6 shadow-neon">
          <p className="text-xs uppercase tracking-[0.25em] text-warning">Engine Status</p>
          <div className="mt-5 flex items-center justify-between">
            <StatusPulse status={status.status} />
            <span className="rounded-full border border-warning/30 px-4 py-1 text-sm text-warning">
              {status.status}
            </span>
          </div>
          <p className="mt-4 text-sm text-textSoft">Live operating mode, synced from worker runtime.</p>
        </article>

        <article className="rounded-2xl border border-warning/20 bg-panel p-6 shadow-neon">
          <p className="text-xs uppercase tracking-[0.25em] text-warning">Next Post Countdown</p>
          <p className="metric-font mt-5 text-4xl text-slate-100">{countdown}</p>
          <p className="mt-2 text-xs text-textSoft">Next post time (EAT): {nextPostEAT}</p>
          <p className="mt-3 text-sm text-textSoft">Cadence uses randomized jitter plus sleep windows.</p>
        </article>

        <article className="rounded-2xl border border-warning/20 bg-panel p-6 shadow-neon">
          <p className="text-xs uppercase tracking-[0.25em] text-warning">Output Metrics</p>
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-panelAlt bg-[#11151a] p-3">
              <p className="text-xs text-textSoft">Posts Today</p>
              <p className="text-xl font-semibold text-slate-100">{status.posts_today}</p>
            </div>
            <div className="rounded-lg border border-panelAlt bg-[#11151a] p-3">
              <p className="text-xs text-textSoft">Historical Posts</p>
              <p className="text-xl font-semibold text-slate-100">{status.history_size}</p>
            </div>
            <div className="rounded-lg border border-panelAlt bg-[#11151a] p-3">
              <p className="text-xs text-textSoft">Trend Priority Posts</p>
              <p className="text-xl font-semibold text-warning">{status.trend_priority_posts_today ?? 0}</p>
            </div>
            <div className="rounded-lg border border-panelAlt bg-[#11151a] p-3">
              <p className="text-xs text-textSoft">Trend Confidence Avg</p>
              <p className="metric-font text-xl font-semibold text-warning">
                {Number(status.trend_confidence_today_avg ?? 0).toFixed(2)}
              </p>
            </div>
          </div>
        </article>
      </section>

      <section className="mx-auto mt-6 max-w-7xl">
        <ActivityLog apiBase={API_BASE} fallbackLogs={status.recent_logs} />
      </section>
    </main>
  );
}
