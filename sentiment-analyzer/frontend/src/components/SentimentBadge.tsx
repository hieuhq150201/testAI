export function SentimentBadge({ sentiment, confidence }: { sentiment: string; confidence: number }) {
  const isPos = sentiment === "positive";
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold
      ${isPos ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400"
               : "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-400"}`}>
      {isPos ? "😊" : "😞"} {isPos ? "Tích cực" : "Tiêu cực"} · {(confidence * 100).toFixed(0)}%
    </span>
  );
}
