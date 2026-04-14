type Props = {
  status: "posting" | "sleeping" | "offline" | string;
};

const palette = {
  posting: "bg-success shadow-[0_0_12px_rgba(46,189,133,0.8)]",
  sleeping: "bg-warning shadow-[0_0_12px_rgba(240,185,11,0.8)]",
  offline: "bg-danger shadow-[0_0_12px_rgba(246,70,93,0.8)]",
};

export function StatusPulse({ status }: Props) {
  const cls = palette[status as keyof typeof palette] ?? "bg-danger";

  return (
    <div className="flex items-center gap-3">
      <span className={`inline-flex h-3 w-3 animate-pulse rounded-full ${cls}`} />
      <span className="text-sm text-textSoft">Live runtime monitor</span>
    </div>
  );
}
