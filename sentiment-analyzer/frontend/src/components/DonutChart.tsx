"use client";
export function DonutChart({ positive, negative, size = 120 }: {
  positive: number; negative: number; size?: number;
}) {
  const r = 38;
  const circ = 2 * Math.PI * r;
  const posArc = circ * positive;
  const negArc = circ * negative;
  const cx = size / 2, cy = size / 2;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0">
      {/* BG */}
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={10} />
      {/* Tiêu cực */}
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#f43f5e" strokeWidth={10}
        strokeDasharray={`${negArc} ${circ}`}
        strokeDashoffset={-posArc}
        strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`} />
      {/* Tích cực */}
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#10b981" strokeWidth={10}
        strokeDasharray={`${posArc} ${circ}`}
        strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`} />
      {/* Nhãn giữa */}
      <text x={cx} y={cy - 6} textAnchor="middle" className="fill-white" fontSize={13} fontWeight="bold">
        {(positive * 100).toFixed(0)}%
      </text>
      <text x={cx} y={cy + 10} textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize={9}>
        tích cực
      </text>
    </svg>
  );
}
