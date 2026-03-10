"use client";
import { useState, useRef } from "react";
import { predictText, predictBatch, analyzeUrl, analyzeYoutube, PredictResult, SourceResult } from "@/lib/api";
import { SentimentBadge } from "@/components/SentimentBadge";
import { ProgressBar } from "@/components/ProgressBar";

type Tab = "text" | "batch" | "url" | "youtube";

export default function Home() {
  const [tab, setTab] = useState<Tab>("text");

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-white/10 bg-white/5 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🎭</span>
            <div>
              <h1 className="font-bold text-lg leading-none">Sentiment Analyzer</h1>
              <p className="text-xs text-slate-400 mt-0.5">VI · EN · URL · YouTube</p>
            </div>
          </div>
          <div className="flex gap-1.5">
            <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full">EN 89.4%</span>
            <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full">VI 92.9%</span>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="flex gap-1 p-1 bg-white/5 rounded-xl mb-8 backdrop-blur-sm">
          {([
            { key: "text",    icon: "✍️",  label: "Nhập text" },
            { key: "batch",   icon: "📦",  label: "Batch" },
            { key: "url",     icon: "🔗",  label: "URL" },
            { key: "youtube", icon: "🎬",  label: "YouTube" },
          ] as const).map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-sm font-medium transition-all
                ${tab === t.key
                  ? "bg-white text-slate-900 shadow"
                  : "text-slate-400 hover:text-white hover:bg-white/10"}`}
            >
              <span>{t.icon}</span>
              <span className="hidden sm:inline">{t.label}</span>
            </button>
          ))}
        </div>

        {/* Tab panels */}
        {tab === "text"    && <TextTab />}
        {tab === "batch"   && <BatchTab />}
        {tab === "url"     && <UrlTab />}
        {tab === "youtube" && <YoutubeTab />}
      </div>
    </main>
  );
}

/* ── Text Tab ─────────────────────────────────────────────────────── */
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
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => e.key === "Enter" && e.ctrlKey && analyze()}
          placeholder="Nhập review, comment, đoạn văn bất kỳ… (Ctrl+Enter để phân tích)"
          rows={5}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
        <div className="absolute bottom-3 right-3 text-xs text-slate-500">{text.length} ký tự</div>
      </div>

      <button
        onClick={analyze}
        disabled={!text.trim() || loading}
        className="w-full py-3 rounded-xl font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        {loading ? "⏳ Đang phân tích…" : "🔍 Phân tích"}
      </button>

      {error && <div className="bg-rose-500/20 border border-rose-500/30 rounded-xl px-4 py-3 text-rose-300 text-sm">{error}</div>}

      {result && (
        <div className="bg-white/5 border border-white/10 rounded-xl p-6 space-y-4 animate-in fade-in duration-300">
          <div className="flex items-center justify-between">
            <SentimentBadge sentiment={result.sentiment} confidence={result.confidence} />
            <div className="flex gap-2 text-xs text-slate-400">
              {result.language && <span className="bg-white/10 px-2 py-0.5 rounded-full uppercase">{result.language}</span>}
              {result.latency_ms && <span>{result.latency_ms.toFixed(1)}ms</span>}
              {result.cached && <span className="text-yellow-400">⚡ cached</span>}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-emerald-400">😊 Tích cực</span>
              <span className="text-emerald-400 font-mono">{(result.positive_prob * 100).toFixed(1)}%</span>
            </div>
            <ProgressBar value={result.positive_prob} color="emerald" />
            <div className="flex justify-between text-sm">
              <span className="text-rose-400">😞 Tiêu cực</span>
              <span className="text-rose-400 font-mono">{(result.negative_prob * 100).toFixed(1)}%</span>
            </div>
            <ProgressBar value={result.negative_prob} color="rose" />
          </div>

          {result.method && (
            <p className="text-xs text-slate-500">Model: {result.method}</p>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Batch Tab ────────────────────────────────────────────────────── */
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
      <textarea
        value={input}
        onChange={e => setInput(e.target.value)}
        placeholder={"Mỗi dòng 1 review:\nPhim này hay quá!\nSản phẩm kém chất lượng\nGreat service!"}
        rows={7}
        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
      <button onClick={analyze} disabled={!input.trim() || loading}
        className="w-full py-3 rounded-xl font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 transition-all">
        {loading ? "⏳ Đang xử lý…" : `📦 Phân tích ${input.split("\n").filter(l => l.trim()).length} dòng`}
      </button>

      {error && <div className="bg-rose-500/20 border border-rose-500/30 rounded-xl px-4 py-3 text-rose-300 text-sm">{error}</div>}

      {results.length > 0 && (
        <div className="space-y-3">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Tổng", value: results.length, color: "text-white" },
              { label: "Tích cực", value: pos, color: "text-emerald-400" },
              { label: "Tiêu cực", value: neg, color: "text-rose-400" },
            ].map(s => (
              <div key={s.label} className="bg-white/5 border border-white/10 rounded-xl p-4 text-center">
                <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
                <div className="text-xs text-slate-400 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
          <ProgressBar value={pos / results.length} color="emerald" />

          {/* List */}
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {results.map((r, i) => (
              <div key={i} className="flex items-start gap-3 bg-white/5 border border-white/10 rounded-xl px-4 py-3">
                <span className="text-lg shrink-0">{r.sentiment === "positive" ? "😊" : "😞"}</span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-slate-200 truncate">{r.text}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{(r.confidence * 100).toFixed(0)}% confidence</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── URL Tab ──────────────────────────────────────────────────────── */
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
        <input
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === "Enter" && analyze()}
          placeholder="https://example.com/review-article"
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button onClick={analyze} disabled={!url.trim() || loading}
          className="px-6 py-3 rounded-xl font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 transition-all shrink-0">
          {loading ? "⏳" : "🔗 Crawl"}
        </button>
      </div>

      {error && <div className="bg-rose-500/20 border border-rose-500/30 rounded-xl px-4 py-3 text-rose-300 text-sm">{error}</div>}
      {loading && (
        <div className="bg-white/5 border border-white/10 rounded-xl p-8 text-center">
          <div className="text-3xl animate-bounce mb-3">🔍</div>
          <p className="text-slate-400">Đang crawl và phân tích…</p>
        </div>
      )}

      {result && <SourceResultCard result={result} />}
    </div>
  );
}

/* ── YouTube Tab ──────────────────────────────────────────────────── */
function YoutubeTab() {
  const [url, setUrl] = useState("");
  const [maxItems, setMaxItems] = useState(100);
  const [result, setResult] = useState<SourceResult | null>(null);
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
        <input
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === "Enter" && analyze()}
          placeholder="https://youtube.com/watch?v=..."
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-red-500"
        />
        <button onClick={analyze} disabled={!url.trim() || loading}
          className="px-6 py-3 rounded-xl font-semibold bg-red-600 hover:bg-red-500 disabled:opacity-40 transition-all shrink-0">
          {loading ? "⏳" : "🎬 Phân tích"}
        </button>
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm text-slate-400 shrink-0">Số comments:</label>
        <input type="range" min={20} max={200} step={10} value={maxItems} onChange={e => setMaxItems(+e.target.value)}
          className="flex-1 accent-red-500" />
        <span className="text-sm text-white font-mono w-8 text-right">{maxItems}</span>
      </div>

      {error && <div className="bg-rose-500/20 border border-rose-500/30 rounded-xl px-4 py-3 text-rose-300 text-sm">{error}</div>}
      {loading && (
        <div className="bg-white/5 border border-white/10 rounded-xl p-8 text-center">
          <div className="text-3xl animate-spin mb-3">🎬</div>
          <p className="text-slate-400">Đang lấy comments từ YouTube…</p>
        </div>
      )}

      {result && <SourceResultCard result={result} showComments />}
    </div>
  );
}

/* ── Shared Source Result Card ────────────────────────────────────── */
function SourceResultCard({ result, showComments = false }: { result: SourceResult; showComments?: boolean }) {
  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      {/* Title */}
      {result.title && (
        <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-3">
          <p className="text-sm font-medium text-slate-200">{result.title}</p>
          {result.url && <p className="text-xs text-slate-500 truncate mt-0.5">{result.url}</p>}
        </div>
      )}

      {/* Overall */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Kết quả", value: result.overall_sentiment === "positive" ? "Tích cực 😊" : "Tiêu cực 😞",
            color: result.overall_sentiment === "positive" ? "text-emerald-400" : "text-rose-400" },
          { label: "Đã phân tích", value: `${result.total_analyzed}`, color: "text-white" },
          { label: "Tích cực", value: `${(result.positive_rate * 100).toFixed(1)}%`, color: "text-emerald-400" },
          { label: "Tiêu cực", value: `${(result.negative_rate * 100).toFixed(1)}%`, color: "text-rose-400" },
        ].map(s => (
          <div key={s.label} className="bg-white/5 border border-white/10 rounded-xl p-4 text-center">
            <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-xs text-slate-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="space-y-1">
        <div className="flex justify-between text-xs text-slate-400 mb-1">
          <span>😊 {result.positive_count} tích cực</span>
          <span>😞 {result.negative_count} tiêu cực</span>
        </div>
        <ProgressBar value={result.positive_rate} color="emerald" />
      </div>

      {/* Comments or Samples */}
      {showComments && result.top_positive && result.top_positive.length > 0 && (
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <h3 className="text-sm font-semibold text-emerald-400 mb-2">🏆 Top tích cực</h3>
            <div className="space-y-2">
              {result.top_positive.slice(0,3).map((c, i) => (
                <div key={i} className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">
                  <p className="text-xs text-slate-200 line-clamp-2">{c.text}</p>
                  <p className="text-xs text-emerald-400 mt-1">{(c.confidence*100).toFixed(0)}%</p>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-rose-400 mb-2">👎 Top tiêu cực</h3>
            <div className="space-y-2">
              {(result.top_negative ?? []).slice(0,3).map((c, i) => (
                <div key={i} className="bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
                  <p className="text-xs text-slate-200 line-clamp-2">{c.text}</p>
                  <p className="text-xs text-rose-400 mt-1">{(c.confidence*100).toFixed(0)}%</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {!showComments && result.sample_texts && result.sample_texts.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-300 mb-2">📝 Mẫu phân tích</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {result.sample_texts.map((s, i) => (
              <div key={i} className={`flex items-start gap-2 border rounded-lg px-3 py-2
                ${s.sentiment === "positive"
                  ? "bg-emerald-500/10 border-emerald-500/20"
                  : "bg-rose-500/10 border-rose-500/20"}`}>
                <span className="shrink-0">{s.sentiment === "positive" ? "😊" : "😞"}</span>
                <p className="text-xs text-slate-200 line-clamp-2">{s.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
