"use client";

import { useEffect, useMemo, useState } from "react";

import { LogEntry } from "@/lib/types";

type Props = {
  apiBase: string;
  fallbackLogs: LogEntry[];
};

export function ActivityLog({ apiBase, fallbackLogs }: Props) {
  const [events, setEvents] = useState<LogEntry[]>(fallbackLogs ?? []);

  useEffect(() => {
    const stream = new EventSource(`${apiBase}/events`);

    stream.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "keepalive") return;
        setEvents((prev) => [...prev.slice(-249), payload]);
      } catch {
        // ignore malformed events
      }
    };

    stream.onerror = () => {
      stream.close();
    };

    return () => stream.close();
  }, [apiBase]);

  const rendered = useMemo(() => (events.length ? events : fallbackLogs), [events, fallbackLogs]);

  return (
    <article className="rounded-2xl border border-warning/20 bg-panel p-6 shadow-neon">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">Activity Log</h2>
        <p className="text-xs uppercase tracking-[0.2em] text-warning">Live SSE</p>
      </div>
      <div className="metric-font h-[420px] overflow-auto rounded-xl border border-panelAlt bg-[#0f1318] p-4 text-xs">
        {rendered.slice().reverse().map((item, idx) => (
          <p key={`${item.ts}-${idx}`} className="mb-2 text-slate-300">
            <span className="text-warning">
              [
              {new Date(item.ts).toLocaleTimeString("en-KE", {
                timeZone: "Africa/Nairobi",
                hour12: false,
              })}{" "}
              EAT]
            </span>{" "}
            <span className="uppercase text-textSoft">{item.level}</span> {item.message}
          </p>
        ))}
        {!rendered.length && <p className="text-textSoft">No activity yet...</p>}
      </div>
    </article>
  );
}
