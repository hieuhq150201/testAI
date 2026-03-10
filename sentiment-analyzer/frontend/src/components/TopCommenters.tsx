"use client";
interface CommenterStat {
  author: string; positive: number; negative: number;
  comments: Array<{ text: string; sentiment: string; confidence: number }>;
}

export function TopCommenters({
  topPositive, topNegative, spamFiltered, spamRate, spamReasons
}: {
  topPositive: CommenterStat[]; topNegative: CommenterStat[];
  spamFiltered: number; spamRate: number; spamReasons: Record<string,number>;
}) {
  return (
    <div className="space-y-4">
      {/* Bot/Spam stats */}
      {spamFiltered > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 mb-2">
            <span>🤖</span>
            <span className="text-sm font-semibold text-yellow-400">
              Đã lọc {spamFiltered} bình luận spam ({(spamRate*100).toFixed(1)}%)
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(spamReasons).map(([reason, count]) => (
              <span key={reason} className="text-xs bg-yellow-500/20 text-yellow-300 px-2 py-0.5 rounded-full">
                {reason}: {count}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Top commenters */}
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-semibold text-emerald-400 mb-3">
            🏆 Người bình luận tích cực nhất
          </h3>
          <div className="space-y-2">
            {topPositive.slice(0,5).map((u, i) => (
              <div key={i} className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-3 py-2.5">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-emerald-300 truncate">{u.author}</span>
                  <div className="flex gap-2 text-xs shrink-0 ml-2">
                    <span className="text-emerald-400">+{u.positive}</span>
                    {u.negative > 0 && <span className="text-rose-400">-{u.negative}</span>}
                  </div>
                </div>
                {u.comments[0] && (
                  <p className="text-xs text-slate-400 line-clamp-1">"{u.comments[0].text}"</p>
                )}
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-rose-400 mb-3">
            👎 Người bình luận tiêu cực nhất
          </h3>
          <div className="space-y-2">
            {topNegative.slice(0,5).map((u, i) => (
              <div key={i} className="bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2.5">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-rose-300 truncate">{u.author}</span>
                  <div className="flex gap-2 text-xs shrink-0 ml-2">
                    <span className="text-rose-400">-{u.negative}</span>
                    {u.positive > 0 && <span className="text-emerald-400">+{u.positive}</span>}
                  </div>
                </div>
                {u.comments[0] && (
                  <p className="text-xs text-slate-400 line-clamp-1">"{u.comments[0].text}"</p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
