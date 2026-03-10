"use client";
import { useState } from "react";
import { predictText, predictBatch, analyzeUrl, analyzeYoutube, PredictResult, SourceResult } from "@/lib/api";

type Tab = "text" | "batch" | "url" | "youtube" | "video";

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: "text",    label: "Văn bản",  icon: "✦" },
  { key: "batch",   label: "Hàng loạt", icon: "≡" },
  { key: "url",     label: "URL",      icon: "⊕" },
  { key: "youtube", label: "YouTube",  icon: "▷" },
];

export default function Home() {
  const [tab, setTab] = useState<Tab>("text");
  // ── Video ─────────────────────────────────────────────────────────
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoResult, setVideoResult] = useState<any>(null);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoError, setVideoError] = useState("");

  const handleVideoAnalyze = async () => {
    if (!videoFile) return;
    setVideoLoading(true); setVideoError(""); setVideoResult(null);
    try {
      const formData = new FormData();
      formData.append("file", videoFile);
      const res = await fetch("http://localhost:8000/analyze/video", {
        method: "POST", body: formData,
      });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Lỗi"); }
      setVideoResult(await res.json());
    } catch(e: any) { setVideoError(e.message); }
    finally { setVideoLoading(false); }
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      {/* Header */}
      <header style={{
        background: "var(--surface)", borderBottom: "1px solid var(--border)",
        position: "sticky", top: 0, zIndex: 20,
        boxShadow: "var(--shadow)",
      }}>
        <div style={{ maxWidth: 760, margin: "0 auto", padding: "0 20px", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 15, color: "#fff", fontWeight: 700,
            }}>S</div>
            <span style={{ fontWeight: 700, fontSize: 16, letterSpacing: "-0.3px" }}>SentimentAI</span>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <Pill color="#059669" bg="#ecfdf5">EN 89.4%</Pill>
            <Pill color="#6366f1" bg="#eef2ff">VI 92.9%</Pill>
          </div>
        </div>
      </header>

      <div style={{ maxWidth: 760, margin: "0 auto", padding: "32px 20px 80px" }}>
        {/* Hero */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.5px", marginBottom: 8 }}>
            Phân tích cảm xúc văn bản
          </h1>
          <p style={{ color: "var(--text-2)", fontSize: 15 }}>
            Hỗ trợ Tiếng Việt · Tiếng Anh · Crawl URL · YouTube comments
          </p>
        </div>

        {/* Tabs */}
        <div style={{
          display: "flex", gap: 4, background: "var(--surface-2)",
          padding: 4, borderRadius: 10, marginBottom: 24, border: "1px solid var(--border)",
        }}>
          {TABS.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{
              flex: 1, padding: "8px 12px", borderRadius: 7, border: "none", cursor: "pointer",
              fontWeight: tab === t.key ? 600 : 500,
              fontSize: 13.5,
              background: tab === t.key ? "var(--surface)" : "transparent",
              color: tab === t.key ? "var(--text)" : "var(--text-2)",
              boxShadow: tab === t.key ? "var(--shadow)" : "none",
              transition: "all .15s",
              display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
            }}>
              <span style={{ opacity: 0.7 }}>{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>

        {tab === "text"    && <TextTab />}
        {tab === "batch"   && <BatchTab />}
        {tab === "url"     && <UrlTab />}
        {tab === "youtube" && <YoutubeTab />}
      </div>
    </div>
  );
}

/* ── Text ─────────────────────────────────────────────────────── */
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

  const isPos = result?.sentiment === "positive";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card>
        <textarea value={text} onChange={e => setText(e.target.value)}
          onKeyDown={e => e.ctrlKey && e.key === "Enter" && analyze()}
          placeholder="Nhập đánh giá hoặc bình luận bất kỳ…"
          rows={4}
          style={{
            width: "100%", border: "none", outline: "none", resize: "none",
            fontSize: 15, lineHeight: 1.6, color: "var(--text)",
            background: "transparent", fontFamily: "inherit",
          }} />
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--border)" }}>
          <span style={{ fontSize: 12, color: "var(--text-3)" }}>{text.length} ký tự · Ctrl+Enter để gửi</span>
          <Btn onClick={analyze} loading={loading} disabled={!text.trim()}>Phân tích</Btn>
        </div>
      </Card>

      {error && <ErrorBox msg={error} />}

      {result && (
        <div className="animate-in">
          <Card>
            {/* Kết quả chính */}
            <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
              <div style={{
                width: 56, height: 56, borderRadius: 16,
                background: isPos ? "var(--pos-bg)" : "var(--neg-bg)",
                border: `1px solid ${isPos ? "var(--pos-border)" : "var(--neg-border)"}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 26,
              }}>
                {isPos ? "😊" : "😞"}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 20, color: isPos ? "var(--pos)" : "var(--neg)" }}>
                  {isPos ? "Tích cực" : "Tiêu cực"}
                </div>
                <div style={{ fontSize: 13, color: "var(--text-2)", marginTop: 2 }}>
                  Độ tin cậy {(result.confidence * 100).toFixed(1)}%
                  {result.language && <span style={{ marginLeft: 8 }}> · {result.language.toUpperCase()}</span>}
                  {result.cached && <span style={{ marginLeft: 8, color: "#d97706" }}> · ⚡ cache</span>}
                </div>
              </div>
            </div>

            {/* Thanh progress */}
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <ProbBar label="Tích cực" value={result.positive_prob} color="var(--pos)" bg="var(--pos-bg)" />
              <ProbBar label="Tiêu cực" value={result.negative_prob} color="var(--neg)" bg="var(--neg-bg)" />
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

/* ── Batch ────────────────────────────────────────────────────── */
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
  const lines = input.split("\n").filter(l => l.trim()).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card>
        <textarea value={input} onChange={e => setInput(e.target.value)}
          placeholder={"Mỗi dòng một câu:\nPhim này hay quá!\nSản phẩm kém chất lượng\nGreat service!"}
          rows={6}
          style={{
            width: "100%", border: "none", outline: "none", resize: "none",
            fontSize: 14, lineHeight: 1.7, color: "var(--text)",
            background: "transparent", fontFamily: "inherit",
          }} />
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--border)" }}>
          <span style={{ fontSize: 12, color: "var(--text-3)" }}>{lines} dòng</span>
          <Btn onClick={analyze} loading={loading} disabled={lines === 0}>Phân tích {lines > 0 ? lines : ""} dòng</Btn>
        </div>
      </Card>

      {error && <ErrorBox msg={error} />}

      {results.length > 0 && (
        <div className="animate-in" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {/* Stats */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
            <StatCard label="Tổng" value={results.length} />
            <StatCard label="Tích cực" value={pos} color="var(--pos)" bg="var(--pos-bg)" />
            <StatCard label="Tiêu cực" value={neg} color="var(--neg)" bg="var(--neg-bg)" />
          </div>

          {/* Ratio bar */}
          <Card style={{ padding: "14px 16px" }}>
            <div style={{ fontSize: 12, color: "var(--text-2)", marginBottom: 8 }}>Tỉ lệ tích cực / tiêu cực</div>
            <div style={{ height: 10, borderRadius: 99, background: "var(--neg-bg)", overflow: "hidden", display: "flex" }}>
              <div style={{ width: `${pos/results.length*100}%`, background: "var(--pos)", borderRadius: 99, transition: "width .5s" }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 12 }}>
              <span style={{ color: "var(--pos)", fontWeight: 600 }}>{(pos/results.length*100).toFixed(0)}% tích cực</span>
              <span style={{ color: "var(--neg)", fontWeight: 600 }}>{(neg/results.length*100).toFixed(0)}% tiêu cực</span>
            </div>
          </Card>

          {/* List */}
          <Card style={{ padding: 0, overflow: "hidden" }}>
            <div style={{ maxHeight: 320, overflowY: "auto" }}>
              {results.map((r, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 12,
                  padding: "10px 16px",
                  borderBottom: i < results.length-1 ? "1px solid var(--border)" : "none",
                }}>
                  <span style={{ fontSize: 16, flexShrink: 0 }}>{r.sentiment === "positive" ? "😊" : "😞"}</span>
                  <span style={{ flex: 1, fontSize: 13.5, color: "var(--text)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.text}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: r.sentiment === "positive" ? "var(--pos)" : "var(--neg)", flexShrink: 0 }}>
                    {(r.confidence*100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </Card>
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
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card style={{ padding: "12px 16px" }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <input value={url} onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === "Enter" && analyze()}
            placeholder="https://example.com/bai-viet-danh-gia"
            style={{
              flex: 1, border: "none", outline: "none", fontSize: 14,
              color: "var(--text)", background: "transparent", fontFamily: "inherit",
            }} />
          <Btn onClick={analyze} loading={loading} disabled={!url.trim()}>Crawl & Phân tích</Btn>
        </div>
      </Card>
      {error && <ErrorBox msg={error} />}
      {loading && <LoadingCard text="Đang crawl trang web…" />}
      {result && <SourceResultCard result={result} />}
    </div>
  );
}

/* ── YouTube ──────────────────────────────────────────────────── */
function YoutubeTab() {
  const [url, setUrl] = useState("");
  const [max, setMax] = useState(500);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    if (!url.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try { setResult(await analyzeYoutube(url, max)); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card>
        <input value={url} onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === "Enter" && analyze()}
          placeholder="https://youtube.com/watch?v=..."
          style={{
            width: "100%", border: "none", outline: "none", fontSize: 14,
            color: "var(--text)", background: "transparent", fontFamily: "inherit",
            marginBottom: 14,
          }} />

        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderTop: "1px solid var(--border)", borderBottom: "1px solid var(--border)", marginBottom: 14 }}>
          <label style={{ fontSize: 13, color: "var(--text-2)", flexShrink: 0 }}>Số bình luận:</label>
          <input type="range" min={50} max={1000} step={50} value={max}
            onChange={e => setMax(+e.target.value)}
            style={{ flex: 1, accentColor: "#6366f1" }} />
          <span style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", width: 48, textAlign: "right", flexShrink: 0 }}>{max.toLocaleString()}</span>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <Btn onClick={analyze} loading={loading} disabled={!url.trim()}>Phân tích</Btn>
        </div>
      </Card>

      {error && <ErrorBox msg={error} />}
      {loading && <LoadingCard text={`Đang lấy ${max.toLocaleString()} bình luận…`} />}
      {result && (
        <div className="animate-in" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <SourceResultCard result={result} />
          {result.spam_filtered > 0 && (
            <SpamBadge filtered={result.spam_filtered} rate={result.spam_rate} reasons={result.spam_reasons} details={result.spam_details} />
          )}
          {(result.top_positive_users?.length > 0 || result.top_negative_users?.length > 0) && (
            <TopCommentersCard pos={result.top_positive_users ?? []} neg={result.top_negative_users ?? []} />
          )}
          <TopComments pos={result.top_positive ?? []} neg={result.top_negative ?? []} />
        </div>
      )}
    </div>
  );
}

/* ── SourceResultCard ─────────────────────────────────────────── */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function SourceResultCard({ result }: { result: any }) {
  const isPos = result.overall_sentiment === "positive";
  return (
    <Card>
      {result.title && (
        <div style={{ marginBottom: 16, paddingBottom: 16, borderBottom: "1px solid var(--border)" }}>
          <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 2 }}>{result.title}</div>
          {result.url && <div style={{ fontSize: 12, color: "var(--text-3)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{result.url}</div>}
        </div>
      )}

      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
        <div style={{
          width: 52, height: 52, borderRadius: 14,
          background: isPos ? "var(--pos-bg)" : "var(--neg-bg)",
          border: `1px solid ${isPos ? "var(--pos-border)" : "var(--neg-border)"}`,
          display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24,
        }}>
          {isPos ? "😊" : "😞"}
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 18, color: isPos ? "var(--pos)" : "var(--neg)" }}>
            {isPos ? "Phần lớn tích cực" : "Phần lớn tiêu cực"}
          </div>
          <div style={{ fontSize: 13, color: "var(--text-2)", marginTop: 2 }}>
            {result.total_analyzed.toLocaleString()} bình luận · độ tin cậy TB {(result.avg_confidence*100).toFixed(0)}%
            {result.total_fetched && result.total_fetched > result.total_analyzed &&
              <span> · lấy mẫu từ {result.total_fetched.toLocaleString()}</span>}
          </div>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <ProbBar label={`Tích cực (${result.positive_count.toLocaleString()})`} value={result.positive_rate} color="var(--pos)" bg="var(--pos-bg)" />
        <ProbBar label={`Tiêu cực (${result.negative_count.toLocaleString()})`} value={result.negative_rate} color="var(--neg)" bg="var(--neg-bg)" />
      </div>
    </Card>
  );
}

/* ── SpamBadge ────────────────────────────────────────────────── */
const REASON_LABEL: Record<string, string> = {
  "lặp ký tự":     "🔤 Lặp ký tự",
  "emoji spam":    "😂 Emoji spam",
  "all caps spam": "🔊 All caps",
  "quảng cáo/link":"🔗 Quảng cáo/link",
  "username bot":  "🤖 Username bot",
};
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function SpamBadge({ filtered, rate, reasons, details }: { filtered: number; rate: number; reasons: Record<string,number>; details?: any[] }) {
  const [open, setOpen] = useState(false);
  return (
    <Card style={{ padding: "12px 16px", background: "#fffbeb", border: "1px solid #fde68a" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 15 }}>🤖</span>
          <span style={{ fontWeight: 600, fontSize: 13.5, color: "#92400e" }}>
            Đã lọc {filtered.toLocaleString()} spam ({(rate*100).toFixed(1)}%)
          </span>
        </div>
        {details && details.length > 0 && (
          <button onClick={() => setOpen(o => !o)} style={{
            fontSize: 12, fontWeight: 600, color: "#92400e",
            background: "#fef3c7", border: "1px solid #fde68a",
            borderRadius: 6, padding: "3px 10px", cursor: "pointer",
          }}>
            {open ? "Ẩn ▲" : "Xem chi tiết ▼"}
          </button>
        )}
      </div>

      {/* Reason pills */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: open ? 14 : 0 }}>
        {Object.entries(reasons).map(([k,v]) => (
          <span key={k} style={{ fontSize: 12, background: "#fef3c7", color: "#78350f", padding: "3px 10px", borderRadius: 99, border: "1px solid #fde68a", fontWeight: 500 }}>
            {REASON_LABEL[k] ?? k}: {v as number}
          </span>
        ))}
      </div>

      {/* Detail table */}
      {open && details && details.length > 0 && (
        <div style={{ borderTop: "1px solid #fde68a", paddingTop: 12 }}>
          <div style={{ fontSize: 12, color: "#78350f", marginBottom: 8, fontWeight: 600 }}>
            Chi tiết từng bình luận spam:
          </div>
          <div style={{ maxHeight: 320, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6 }}>
            {details.map((d: any, i: number) => (
              <div key={i} style={{
                display: "grid", gridTemplateColumns: "auto 1fr auto",
                gap: 10, alignItems: "start",
                padding: "8px 10px", borderRadius: 8,
                background: "#fef9ec", border: "1px solid #fde68a",
                fontSize: 12.5,
              }}>
                <span style={{
                  background: "#fde68a", color: "#78350f",
                  padding: "2px 7px", borderRadius: 99, fontSize: 11, fontWeight: 600,
                  whiteSpace: "nowrap",
                }}>
                  {REASON_LABEL[d.reason] ?? d.reason}
                </span>
                <div>
                  <div style={{ fontWeight: 500, color: "#92400e", marginBottom: 2 }}>@{d.author}</div>
                  <div style={{ color: "#78350f", lineHeight: 1.5 }}>{d.text}</div>
                </div>
                {d.votes > 0 && (
                  <span style={{ color: "#a16207", fontSize: 11, whiteSpace: "nowrap" }}>👍 {d.votes.toLocaleString()}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

/* ── TopCommentersCard ────────────────────────────────────────── */
function TopCommentersCard({ pos, neg }: { pos: any[]; neg: any[] }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      {[
        { title: "Tích cực nhất", items: pos, color: "var(--pos)", bg: "var(--pos-bg)", border: "var(--pos-border)" },
        { title: "Tiêu cực nhất", items: neg, color: "var(--neg)", bg: "var(--neg-bg)", border: "var(--neg-border)" },
      ].map(col => (
        <Card key={col.title}>
          <div style={{ fontWeight: 600, fontSize: 13, color: col.color, marginBottom: 10 }}>🏅 {col.title}</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {col.items.slice(0,5).map((u: any, i: number) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ width: 28, height: 28, borderRadius: 99, background: col.bg, border: `1px solid ${col.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: col.color, flexShrink: 0 }}>
                  {i+1}
                </div>
                <div style={{ flex: 1, overflow: "hidden" }}>
                  <div style={{ fontSize: 12.5, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{u.author}</div>
                  <div style={{ fontSize: 11, color: "var(--text-3)" }}>{col.title === "Tích cực nhất" ? u.positive : u.negative} bình luận</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}

/* ── TopComments ──────────────────────────────────────────────── */
function TopComments({ pos, neg }: { pos: any[]; neg: any[] }) {
  if (!pos.length && !neg.length) return null;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      {[
        { title: "Tích cực nhất", items: pos, color: "var(--pos)", bg: "var(--pos-bg)", border: "var(--pos-border)" },
        { title: "Tiêu cực nhất", items: neg, color: "var(--neg)", bg: "var(--neg-bg)", border: "var(--neg-border)" },
      ].map(col => (
        <Card key={col.title}>
          <div style={{ fontWeight: 600, fontSize: 13, color: col.color, marginBottom: 10 }}>💬 {col.title}</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {col.items.slice(0,3).map((c: any, i: number) => (
              <div key={i} style={{ padding: "8px 10px", borderRadius: 8, background: col.bg, border: `1px solid ${col.border}` }}>
                <div style={{ fontSize: 12.5, color: "var(--text)", lineHeight: 1.5, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{c.text}</div>
                <div style={{ fontSize: 11, color: col.color, marginTop: 4, fontWeight: 600 }}>{c.author} · {(c.confidence*100).toFixed(0)}%</div>
              </div>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}

/* ── Shared atoms ─────────────────────────────────────────────── */
function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: 16, boxShadow: "var(--shadow)", ...style }}>
      {children}
    </div>
  );
}

function Btn({ children, onClick, disabled, loading }: { children: React.ReactNode; onClick: () => void; disabled?: boolean; loading?: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled || loading} style={{
      padding: "8px 18px", borderRadius: "var(--radius-sm)", border: "none",
      background: disabled || loading ? "var(--border)" : "var(--accent)",
      color: disabled || loading ? "var(--text-3)" : "#fff",
      fontWeight: 600, fontSize: 13.5, cursor: disabled || loading ? "not-allowed" : "pointer",
      transition: "all .15s", fontFamily: "inherit",
      whiteSpace: "nowrap",
    }}>
      {loading ? "Đang xử lý…" : children}
    </button>
  );
}

function ProbBar({ label, value, color, bg }: { label: string; value: number; color: string; bg: string }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 5 }}>
        <span style={{ color: "var(--text-2)" }}>{label}</span>
        <span style={{ fontWeight: 700, color }}>{(value*100).toFixed(1)}%</span>
      </div>
      <div style={{ height: 8, borderRadius: 99, background: bg, overflow: "hidden" }}>
        <div style={{ width: `${value*100}%`, height: "100%", background: color, borderRadius: 99, transition: "width .5s" }} />
      </div>
    </div>
  );
}

function StatCard({ label, value, color, bg }: { label: string; value: number; color?: string; bg?: string }) {
  return (
    <div style={{ background: bg ?? "var(--surface-2)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "14px 16px", textAlign: "center" }}>
      <div style={{ fontSize: 24, fontWeight: 700, color: color ?? "var(--text)" }}>{value}</div>
      <div style={{ fontSize: 12, color: "var(--text-2)", marginTop: 4 }}>{label}</div>
    </div>
  );
}

function Pill({ children, color, bg }: { children: React.ReactNode; color: string; bg: string }) {
  return (
    <span style={{ fontSize: 11.5, fontWeight: 600, color, background: bg, padding: "3px 9px", borderRadius: 99 }}>
      {children}
    </span>
  );
}

function ErrorBox({ msg }: { msg: string }) {
  return (
    <div style={{ padding: "12px 16px", borderRadius: "var(--radius)", background: "var(--neg-bg)", border: "1px solid var(--neg-border)", color: "var(--neg)", fontSize: 13.5 }}>
      {msg}
    </div>
  );
}

function LoadingCard({ text }: { text: string }) {
  return (
    <Card style={{ textAlign: "center", padding: "32px 16px" }}>
      <div style={{ fontSize: 13.5, color: "var(--text-2)" }}>⏳ {text}</div>
    </Card>
  );
}
