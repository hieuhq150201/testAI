"use client";
export function BarChartComp({ data }: { data: Array<{ name: string; value: number; fill: string }> }) {
  const max = Math.max(...data.map(d => d.value), 1);
  return (
    <div className="space-y-2">
      {data.map((d, i) => (
        <div key={i}>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-300">{d.name}</span>
            <span className="font-mono font-bold" style={{ color: d.fill }}>{d.value.toLocaleString()}</span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-5 overflow-hidden">
            <div
              className="h-5 rounded-full transition-all duration-700 flex items-center justify-end pr-2"
              style={{ width: `${(d.value / max) * 100}%`, backgroundColor: d.fill }}
            >
              {(d.value / max) > 0.15 && (
                <span className="text-xs text-white font-bold">
                  {((d.value / data.reduce((a,b) => a+b.value,0))*100).toFixed(0)}%
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
