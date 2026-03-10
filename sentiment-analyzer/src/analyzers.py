"""
🌐 Sprint 7 — Source Analyzers
Crawl & analyze từ URL, YouTube, File
"""
import re, requests, logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def _aggregate(results: List[dict]) -> dict:
    """Tổng hợp kết quả từ list predictions"""
    if not results:
        return {}
    pos = sum(1 for r in results if r.get("sentiment") == "positive")
    neg = len(results) - pos
    avg_conf = sum(r.get("confidence", 0) for r in results) / len(results)
    overall = "positive" if pos >= neg else "negative"
    return {
        "overall_sentiment": overall,
        "total_analyzed": len(results),
        "positive_count": pos,
        "negative_count": neg,
        "positive_rate": round(pos / len(results), 4),
        "negative_rate": round(neg / len(results), 4),
        "avg_confidence": round(avg_conf, 4),
    }

# ── URL Analyzer ──────────────────────────────────────────────────
def extract_text_from_url(url: str) -> Dict[str, Any]:
    """Crawl URL, extract title + paragraphs"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        raise ValueError(f"Không thể tải URL: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove script/style
    for tag in soup(["script","style","nav","footer","header","aside"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else "N/A"

    # Extract paragraphs (>50 chars)
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")
                  if len(p.get_text(strip=True)) > 50]

    # Also try article / main content
    if not paragraphs:
        paragraphs = [soup.get_text(separator=" ", strip=True)]

    return {"title": title, "paragraphs": paragraphs[:50], "url": url}


def analyze_url(url: str, predict_fn) -> dict:
    data = extract_text_from_url(url)
    paragraphs = data["paragraphs"]
    if not paragraphs:
        raise ValueError("Không extract được text từ URL này")

    results = [predict_fn(p) for p in paragraphs]
    agg = _aggregate(results)

    return {
        "source": "url",
        "url": url,
        "title": data["title"],
        **agg,
        "sample_texts": [
            {"text": p[:120] + "..." if len(p) > 120 else p,
             "sentiment": r["sentiment"],
             "confidence": r["confidence"]}
            for p, r in zip(paragraphs[:5], results[:5])
        ]
    }


# ── YouTube Analyzer ──────────────────────────────────────────────
def extract_video_id(url: str) -> str:
    """Extract YouTube video ID từ nhiều dạng URL"""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    raise ValueError("Không nhận ra YouTube URL. Dùng dạng: https://youtube.com/watch?v=VIDEO_ID")


def _parse_votes(v) -> int:
    """Parse votes: '8,9\xa0N' → 8900, '1.2K' → 1200, 42 → 42"""
    if not v: return 0
    s = str(v).replace("\xa0","").replace(",",".").strip()
    try:
        if s.upper().endswith("K"): return int(float(s[:-1]) * 1000)
        if s.upper().endswith("N"): return int(float(s[:-1]) * 1000)  # N = nghìn (VI)
        if s.upper().endswith("M"): return int(float(s[:-1]) * 1_000_000)
        return int(float(s))
    except Exception:
        return 0


def get_youtube_comments(video_id: str, max_comments: int = 500) -> List[str]:
    """Fetch YouTube comments — trả về list dict {text, author, votes}"""
    try:
        from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
        downloader = YoutubeCommentDownloader()
        gen = downloader.get_comments_from_url(
            f"https://youtube.com/watch?v={video_id}",
            sort_by=SORT_BY_POPULAR
        )
        comments = []
        for c in gen:
            text = c.get("text", "").strip()
            if text and len(text) > 5:
                comments.append({
                    "text":   text,
                    "author": c.get("author", "Unknown"),
                    "votes":  _parse_votes(c.get("votes", 0)),
                    "reply":  bool(c.get("reply", False)),
                })
            if len(comments) >= max_comments:
                break
        return comments
    except Exception as e:
        raise ValueError(f"Lỗi lấy comments YouTube: {e}")


def analyze_youtube(url: str, predict_fn, max_comments: int = 500) -> dict:
    """Phân tích YouTube comments với bot detection + smart sampling"""
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("URL YouTube không hợp lệ")

    # Lấy title
    title = f"YouTube Video ({video_id})"
    try:
        import requests as req
        r = req.get(f"https://www.youtube.com/oembed?url=https://youtube.com/watch?v={video_id}&format=json", timeout=5)
        if r.status_code == 200:
            title = r.json().get("title", title)
    except Exception:
        pass

    raw_comments = get_youtube_comments(video_id, max_comments)

    from src.bot_detector import analyze_comments_with_bot_detection
    from src.context_analyzer import analyze_with_context, build_reply_threads
    result = analyze_comments_with_bot_detection(raw_comments, predict_fn, sample_size=min(max_comments, 500))
    result["source"] = "youtube"
    result["url"]    = url
    result["title"]  = title
    return result


def analyze_file_content(content: str, filename: str, predict_fn) -> dict:
    """Analyze text file — mỗi dòng là 1 text"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

    if ext == "csv":
        import csv, io
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        # Tìm cột text
        text_cols = [c for c in (rows[0].keys() if rows else [])
                     if any(k in c.lower() for k in ["text","review","comment","content","body"])]
        col = text_cols[0] if text_cols else list(rows[0].keys())[0]
        texts = [r[col].strip() for r in rows if r.get(col, "").strip()]
    else:
        # TXT: mỗi dòng
        texts = [l.strip() for l in content.splitlines() if len(l.strip()) > 5]

    if not texts:
        raise ValueError("File không có nội dung hợp lệ")

    texts = texts[:500]  # limit 500 dòng
    results = [predict_fn(t) for t in texts]
    agg = _aggregate(results)

    return {
        "source": "file",
        "filename": filename,
        "file_type": ext,
        **agg,
        "sample_texts": [
            {"text": t[:120]+"..." if len(t)>120 else t,
             "sentiment": r["sentiment"],
             "confidence": r["confidence"]}
            for t, r in zip(texts[:5], results[:5])
        ]
    }
