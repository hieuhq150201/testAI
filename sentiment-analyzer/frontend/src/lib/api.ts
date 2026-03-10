const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface PredictResult {
  text: string;
  sentiment: "positive" | "negative";
  confidence: number;
  positive_prob: number;
  negative_prob: number;
  language?: string;
  method?: string;
  cached?: boolean;
  latency_ms?: number;
}

export interface SourceResult {
  source: string;
  title?: string;
  url?: string;
  total_analyzed: number;
  overall_sentiment: "positive" | "negative";
  positive_rate: number;
  negative_rate: number;
  avg_confidence: number;
  positive_count: number;
  negative_count: number;
  sample_texts?: Array<{ text: string; sentiment: string; confidence: number }>;
  top_positive?: Array<{ text: string; confidence: number }>;
  top_negative?: Array<{ text: string; confidence: number }>;
}

export async function predictText(text: string): Promise<PredictResult> {
  const r = await fetch(`${API_BASE}/predict/multilingual`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function predictBatch(texts: string[]): Promise<PredictResult[]> {
  const r = await fetch(`${API_BASE}/predict/batch`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texts }),
  });
  if (!r.ok) throw new Error(await r.text());
  const data = await r.json();
  return data.results;
}

export async function analyzeUrl(url: string): Promise<SourceResult> {
  const r = await fetch(`${API_BASE}/analyze/url`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function analyzeYoutube(url: string, maxItems = 100): Promise<SourceResult> {
  const r = await fetch(`${API_BASE}/analyze/youtube`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, max_items: maxItems }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getStats() {
  const r = await fetch(`${API_BASE}/stats`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
