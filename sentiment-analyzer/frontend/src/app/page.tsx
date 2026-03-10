"use client";
import { useState } from "react";
import { predictText, predictBatch, analyzeUrl, analyzeYoutube, PredictResult, SourceResult } from "@/lib/api";
import { SentimentBadge } from "@/components/SentimentBadge";
import { ProgressBar } from "@/components/ProgressBar";
import { DonutChart } from "@/components/DonutChart";
import { TopCommenters } from "@/components/TopCommenters";
import { BarChartComp } from "@/components/BarChart";

type Tab = "text" | "batch" | "url" | "youtube";

export default function Home() {
  const [tab, setTab] = useState<Tab>("text");

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <header className="border-b border-white/10 bg-white/5 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🎭</span>
            <div>
              <h1 className="font-bold text-lg leading-none">Phân Tích Cảm Xúc</h1>
              <p className="text-xs text-slate-400 mt-0.5">Tiếng Việt · Tiếng Anh · URL · YouTube</p>
            </div>
          </div>
          <div className="flex gap-1.5">
            <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full">EN 89.4%</span>
            <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full">VI 92.9%</span>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex gap-1 p-1 bg-white/5 rounded-xl mb-8">
          {([
            { key: "text",    icon: "✍️", label: "Nhập văn bản" },
            { key: "batch",   icon: "📦", label: "Nhiều văn bản" },
            { key: "url",     icon: "🔗", label: "Phân tích URL" },
            { key: "youtube", icon: "🎬", label: "YouTube" },
          ] as const).map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-sm font-medium transition-all
                ${tab === t.key ? "bg-white text-slate-900 shadow" : "text-slate-400 hover:text-white hover:bg-white/10"}`}>
              <span>{t.icon}</span>
              <span className="hidden sm:inline">{t.label}</span>
            </button>
          ))}
        </div>

        {tab === "text"    && <TextTab />}
        {tab === "batch"   && <BatchTab />}
        {tab === "url"     && <UrlTab />}
        {tab === "youtube" && <YoutubeTab />}
      </div>
    </main>
  );
}

/* ── Text ──────────────────────────────────────────────────────── */
function TextTab() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<PredictResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    if (!text.trim()) return;
    setLoading(true); setError("");
    try { setResult(await predictText(text)); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <textarea value={text} onChange={e => setText(e.target.value)}
          onKeyDown={e => e.key === "Enter" && e.ctrlKey && analyze()}
          placeholder="Nhập đánh giá, bình luận, đoạn văn bất kỳ… (Ctrl+Enter để phân tích)"
          rows={5}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        <div className="absolute bottom-3 right-3 text-xs text-slate-500">{text.length} ký tự</div>
      </div>
      <button onClick={analyze} disabled={!text.trim() || loading}
        className="w-full py-3 rounded-xl font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 transition-all">
        {loading ? "⏳ Đang phân tích…" : "🔍 Phân tích"}
      </button>
      {error && <ErrorBox msg={error} />}
      {result && (
        <div className="bg-white/5 border border-white/10 rounded-xl p-6 space-y-5 animate-in">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <SentimentBadge sentiment={result.sentiment} confidence={result.confidence} />
            <div className="flex gap-2 text-xs text-slate-400">
              {result.language && <span className="bg-white/10 px-2 py-0.5 rounded-full uppercase">{result.language}</span>}
              {result.latency_ms && <span>{result.latency_ms.toFixed(1)}ms</span>}
              {result.cached && <span className="text-yellow-400">⚡ cache</span>}
            </div>
          </div>

          {/* Donut chart */}
          <div className="flex items-center gap-6">
            <DonutChart positive={result.positive_prob} negative={result.negative_prob} size={120} />
            <div className="flex-1 space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-emerald-400">😊 Tích cực</span>
                  <span className="text-emerald-400 font-mono font-bold">{(result.positive_prob * 100).toFixed(1)}%</span>
                </div>
                <ProgressBar value={result.positive_prob} color="emerald" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-rose-400">😞 Tiêu cực</span>
                  <span className="text-rose-400 font-mono font-bold">{(result.negative_prob * 100).toFixed(1)}%</span>
                </div>
                <ProgressBar value={result.negative_prob} color="rose" />
              </div>
            </div>
          </div>
          {result.method && <p className="text-xs text-slate-500">Mô hình: {result.method}</p>}
        </div>
      )}
    </div>
  );
}

/* ── Batch ──────────────────────────────────────────────────────── */
function BatchTab() {
  const [input, setInput] = useState("");
  const [results, setResults] = useState<PredictResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    const lines = input.split("\n").map(l => l.trim()).filter(Boolean);
    if (!lines.length) return;
    setLoading(true); setError("");
    try { setResults(await predictBatch(lines)); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  const pos = results.filter(r => r.sentiment === "positive").length;
  const neg = results.length - pos;

  return (
    <div className="space-y-4">
      <textarea value={input} onChange={e => setInput(e.target.value)}
        placeholder={"Mỗi dòng một đánh giá:\nPhim này hay quá!\nSản phẩm kém chất lượng\nGreat service!"}
        rows={7}
        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500" />
      <button onClick={analyze} disabled={!input.trim() || loading}
        className="w-full py-3 rounded-xl font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 transition-all">
        {loading ? "⏳ Đang xử lý…" : `📦 Phân tích ${input.split("\n").filter(l => l.trim()).length} dòng`}
      </button>
      {error && <ErrorBox msg={error} />}

      {results.length > 0 && (
        <div className="space-y-4 animate-in">
          <div className="grid grid-cols-3 gap-3">
            <StatCard label="Tổng cộng" value={results.length} color="text-white" />
            <StatCard label="Tích cực 😊" value={pos} color="text-emerald-400" />
            <StatCard label="Tiêu cực 😞" value={neg} color="text-rose-400" />
          </div>

          {/* Bar chart */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-3">Phân bố cảm xúc</p>
            <BarChartComp data={[
              { name: "Tích cực 😊", value: pos, fill: "#10b981" },
              { name: "Tiêu cực 😞", value: neg, fill: "#f43f5e" },
            ]} />
          </div>

          <ProgressBar value={pos / results.length} color="emerald" />
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {results.map((r, i) => (
              <div key={i} className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-xl px-4 py-3">
                <span className="text-xl shrink-0">{r.sentiment === "positive" ? "😊" : "😞"}</span>
                <p className="text-sm text-slate-200 truncate flex-1">{r.text}</p>
                <span className={`text-xs font-mono shrink-0 ${r.sentiment === "positive" ? "text-emerald-400" : "text-rose-400"}`}>
                  {(r.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── URL ──────────────────────────────────────────────────────── */
function UrlTab() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<SourceResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    if (!url.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try { setResult(await analyzeUrl(url)); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input value={url} onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === "Enter" && analyze()}
          placeholder="https://example.com/bai-viet-danh-gia"
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        <button onClick={analyze} disabled={!url.trim() || loading}
          className="px-6 py-3 rounded-xl font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 transition-all shrink-0">
          {loading ? "⏳" : "🔍 Crawl"}
        </button>
      </div>
      {error && <ErrorBox msg={error} />}
      {loading && <LoadingCard icon="🔍" text="Đang tải và phân tích trang web…" />}
      {result && <SourceCard result={result} />}
    </div>
  );
}

/* ── YouTube ──────────────────────────────────────────────────── */
function YoutubeTab() {
  const [url, setUrl] = useState("");
  const [maxItems, setMaxItems] = useState(500);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    if (!url.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try { setResult(await analyzeYoutube(url, maxItems)); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input value={url} onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === "Enter" && analyze()}
          placeholder="https://youtube.com/watch?v=..."
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-red-500" />
        <button onClick={analyze} disabled={!url.trim() || loading}
          className="px-6 py-3 rounded-xl font-semibold bg-red-600 hover:bg-red-500 disabled:opacity-40 transition-all shrink-0">
          {loading ? "⏳" : "🎬 Phân tích"}
        </button>
      </div>

      <div className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-xl px-4 py-3">
        <label className="text-sm text-slate-300 shrink-0">Số bình luận:</label>
        <input type="range" min={50} max={1000} step={50} value={maxItems}
          onChange={e => setMaxItems(+e.target.value)} className="flex-1 accent-red-500" />
        <span className="text-sm font-mono font-bold text-white w-16 text-right">{maxItems.toLocaleString()}</span>
      </div>

      {error && <ErrorBox msg={error} />}
      {loading && <LoadingCard icon="🎬" text={`Đang lấy ${maxItems.toLocaleString()} bình luận từ YouTube…`} />}
      {result && (
        <>
          <SourceCard result={result} showComments />
          {(result.spam_filtered > 0 || result.top_positive_users?.length > 0) && (
            <TopCommenters
              topPositive={result.top_positive_users ?? []}
              topNegative={result.top_negative_users ?? []}
              spamFiltered={result.spam_filtered ?? 0}
              spamRate={result.spam_rate ?? 0}
              spamReasons={result.spam_reasons ?? {}}
            />
          )}
        </>
      )}
    </div>
  );
}

/* ── Shared Source Result Card ──────────────────────────────────── */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function SourceCard({ result, showComments = false }: { result: any; showComments?: boolean }) {
  return (
    <div className="space-y-4 animate-in">
      {result.title && (
        <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-3">
          <p className="font-medium text-slate-200">{result.title}</p>
          {result.url && <p className="text-xs text-slate-500 truncate mt-0.5">{result.url}</p>}
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Kết quả" value={result.overall_sentiment === "positive" ? "Tích cực 😊" : "Tiêu cực 😞"}
          color={result.overall_sentiment === "positive" ? "text-emerald-400" : "text-rose-400"} small />
        <StatCard label="Đã phân tích" value={`${result.total_analyzed.toLocaleString()}${result.total_fetched && result.total_fetched > result.total_analyzed ? ` / ${result.total_fetched.toLocaleString()}` : ""}`} color="text-white" />
        <StatCard label="Tích cực" value={`${(result.positive_rate * 100).toFixed(1)}%`} color="text-emerald-400" />
        <StatCard label="Tiêu cực" value={`${(result.negative_rate * 100).toFixed(1)}%`} color="text-rose-400" />
      </div>

      {/* Biểu đồ tròn + bar */}
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex items-center gap-4">
          <DonutChart positive={result.positive_rate} negative={result.negative_rate} size={100} />
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-2 text-sm">
              <span className="w-3 h-3 rounded-full bg-emerald-500 shrink-0" />
              <span className="text-slate-300">Tích cực</span>
              <span className="ml-auto font-bold text-emerald-400">{result.positive_count.toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="w-3 h-3 rounded-full bg-rose-500 shrink-0" />
              <span className="text-slate-300">Tiêu cực</span>
              <span className="ml-auto font-bold text-rose-400">{result.negative_count.toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="w-3 h-3 rounded-full bg-slate-500 shrink-0" />
              <span className="text-slate-300">Độ tin cậy TB</span>
              <span className="ml-auto font-bold text-slate-300">{(result.avg_confidence * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
          <p className="text-xs text-slate-400 mb-2">Phân bố cảm xúc</p>
          <BarChartComp data={[
            { name: "Tích cực 😊", value: result.positive_count, fill: "#10b981" },
            { name: "Tiêu cực 😞", value: result.negative_count, fill: "#f43f5e" },
          ]} />
        </div>
      </div>

      {/* Top comments (YouTube) */}
      {showComments && (
        <div className="grid sm:grid-cols-2 gap-4">
          {[
            { title: "🏆 Tích cực nhất", items: result.top_positive, cls: "emerald" },
            { title: "👎 Tiêu cực nhất", items: result.top_negative, cls: "rose" },
          ].map(col => (
            <div key={col.title}>
              <h3 className={`text-sm font-semibold text-${col.cls}-400 mb-2`}>{col.title}</h3>
              <div className="space-y-2">
                {(col.items ?? []).slice(0, 5).map((c: {text:string;confidence:number}, i: number) => (
                  <div key={i} className={`bg-${col.cls}-500/10 border border-${col.cls}-500/20 rounded-lg px-3 py-2`}>
                    <p className="text-xs text-slate-200 line-clamp-2">{c.text}</p>
                    <p className={`text-xs text-${col.cls}-400 mt-1 font-mono`}>{(c.confidence * 100).toFixed(0)}%</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Sample paragraphs (URL) */}
      {!showComments && result.sample_texts && result.sample_texts.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-300 mb-2">📝 Mẫu đoạn văn đã phân tích</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {result.sample_texts.map((s: {text:string;sentiment:string;confidence:number}, i: number) => (
              <div key={i} className={`flex items-start gap-2 border rounded-xl px-3 py-2
                ${s.sentiment === "positive" ? "bg-emerald-500/10 border-emerald-500/20" : "bg-rose-500/10 border-rose-500/20"}`}>
                <span className="shrink-0 mt-0.5">{s.sentiment === "positive" ? "😊" : "😞"}</span>
                <p className="text-xs text-slate-200 line-clamp-2">{s.text}</p>
                <span className={`text-xs font-mono shrink-0 ${s.sentiment === "positive" ? "text-emerald-400" : "text-rose-400"}`}>
                  {(s.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Shared helpers ─────────────────────────────────────────────── */
function StatCard({ label, value, color, small }: { label: string; value: string | number; color: string; small?: boolean }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center">
      <div className={`font-bold ${small ? "text-base" : "text-2xl"} ${color}`}>{value}</div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  );
}

function ErrorBox({ msg }: { msg: string }) {
  return <div className="bg-rose-500/20 border border-rose-500/30 rounded-xl px-4 py-3 text-rose-300 text-sm">{msg}</div>;
}

function LoadingCard({ icon, text }: { icon: string; text: string }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-8 text-center">
      <div className="text-3xl animate-bounce mb-3">{icon}</div>
      <p className="text-slate-400 text-sm">{text}</p>
    </div>
  );
}
